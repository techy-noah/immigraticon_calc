import threading
import logging
import os
import sys
from typing import Any

logger = logging.getLogger(__name__)


def generate_ai_report_async(submission_id: int) -> None:
    """Background task to generate AI report for a submission."""
    def _task():
        try:
            import django
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
            
            if 'django' not in sys.modules:
                django.setup()
            
            from assessments.models import Submission
            from assessments.services import ScoringEngine, AIReportService
            
            submission = Submission.objects.get(pk=submission_id)
            
            if submission.ai_report:
                logger.info(f"AI report already exists for submission {submission_id}, skipping.")
                return
            
            logger.info(f"Starting AI report generation for submission {submission_id}")
            
            engine = ScoringEngine(submission.raw_answers)
            result = engine.process()
            
            ai_service = AIReportService()
            ai_report = ai_service.generate_report(
                submission=submission,
                scores=result,
                strengths=result['strongest_categories'],
                gaps=result['weakest_categories']
            )
            
            if ai_report:
                submission.ai_report = ai_report
                submission.save(update_fields=['ai_report'])
                logger.info(f"AI report generated successfully for submission {submission_id}")
                
                _send_user_notification(submission, ai_report, result)
                _send_admin_notification(submission, ai_report)
            else:
                logger.warning(f"AI report generation returned None for submission {submission_id}")
                
        except Exception as e:
            import traceback
            logger.error(f"Background AI report generation failed for submission {submission_id}: {e}")
            logger.error(traceback.format_exc())
    
    thread = threading.Thread(target=_task)
    thread.daemon = True
    thread.start()
    logger.info(f"Started background AI report generation for submission {submission_id}")


def _send_user_notification(submission: Any, ai_report: str, result: dict) -> None:
    """Send AI report notification email to user."""
    try:
        from django.conf import settings
        from django.template.loader import render_to_string
        from django.core.mail import EmailMultiAlternatives
        
        ai_summary = _extract_summary(ai_report)
        
        context = {
            'submission': submission,
            'ai_summary': ai_summary,
            'strengths': result.get('strongest_categories', [])[:3],
            'gaps': result.get('weakest_categories', [])[:3],
        }
        
        html_content = render_to_string('emails/ai_report_notification.html', context)
        
        strengths_list = result.get('strongest_categories', [])[:3]
        gaps_list = result.get('weakest_categories', [])[:3]
        
        strengths_text = '\n'.join([
            f"- {s['category']}: {s['score']}/{s['max_score']}"
            for s in strengths_list
        ]) if strengths_list else "None identified"
        
        gaps_text = '\n'.join([
            f"- {g['category']}: {g['score']}/{g['max_score']}"
            for g in gaps_list
        ]) if gaps_list else "None identified"
        
        text_content = f"""Hi {submission.full_name},

Your Expert Analysis Is Ready!

Score: {submission.total_score}/100 ({submission.readiness_band})

{ai_summary[:500] if ai_summary else 'Your detailed analysis is ready.'}

---
Your Key Strengths:
{strengths_text}

---
Areas to Strengthen:
{gaps_text}

---
Ready to develop a strategic roadmap for your petition?
Book Your Strategy Call: https://immigrationintel.com/consultation

---
ImmigrationIntel
"""
        
        msg = EmailMultiAlternatives(
            subject=f"Your EB1/EB2 Expert Analysis - Score: {submission.total_score}/100",
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@immigrationintel.com'),
            to=[submission.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        logger.info(f"AI report email sent to user {submission.email}")
        
    except Exception as e:
        import traceback
        logger.error(f"Failed to send AI report email to user: {e}")
        logger.error(traceback.format_exc())


def _send_admin_notification(submission: Any, ai_report: str) -> None:
    """Send admin notification that AI report was generated."""
    try:
        from django.conf import settings
        from django.template.loader import render_to_string
        from django.core.mail import EmailMultiAlternatives
        
        context = {
            'submission': submission,
            'ai_report': ai_report,
        }
        
        html_content = render_to_string('emails/admin_ai_report.html', context)
        text_content = f"""AI Report Generated

Name: {submission.full_name}
Email: {submission.email}
Score: {submission.total_score}/100
Readiness: {submission.readiness_band}

AI Report Preview:
{ai_report[:500] if ai_report else 'N/A'}...

View in Admin: https://immigrationintel.com/admin/assessments/submission/{submission.id}/change/
"""
        
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@immigrationintel.com')
        
        msg = EmailMultiAlternatives(
            subject=f"[AI] Report Ready: {submission.full_name} - Score: {submission.total_score}/100",
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@immigrationintel.com'),
            to=[admin_email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        logger.info(f"AI report admin notification sent for submission {submission.id}")
        
    except Exception as e:
        import traceback
        logger.error(f"Failed to send AI report admin notification: {e}")
        logger.error(traceback.format_exc())


def _extract_summary(ai_report: str) -> str:
    """Extract the summary section from AI report."""
    if not ai_report:
        return ''
    
    lines = ai_report.split('\n')
    
    in_summary = False
    summary_lines = []
    paragraph_count = 0
    
    for line in lines:
        stripped = line.strip()
        
        if any(x in stripped.lower() for x in ['## where you stand', '## professional summary', '## executive summary', '## your eb1/eb2 assessment']):
            in_summary = True
            continue
        
        if in_summary:
            if stripped.startswith('## ') or stripped.startswith('# '):
                break
            if stripped:
                summary_lines.append(stripped)
                if '.' in stripped:
                    paragraph_count += 1
            elif summary_lines:
                paragraph_count += 1
            
            if paragraph_count >= 3 and len(' '.join(summary_lines)) > 150:
                break
    
    return ' '.join(summary_lines) if summary_lines else ai_report[:300]


class AIReportGenerator:
    """Service to trigger async AI report generation."""
    
    @staticmethod
    def trigger(submission: Any) -> None:
        generate_ai_report_async(submission.pk)


def send_submission_emails_async(submission_id: int) -> None:
    """Background task to send initial submission emails."""
    def _task():
        try:
            import django
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
            
            if 'django' not in sys.modules:
                django.setup()
            
            from assessments.models import Submission
            from django.conf import settings
            from django.template.loader import render_to_string
            from django.core.mail import EmailMultiAlternatives
            
            submission = Submission.objects.get(pk=submission_id)
            
            if submission.email_sent:
                logger.info(f"Emails already sent for submission {submission_id}, skipping.")
                return
            
            logger.info(f"Sending submission emails for {submission_id}")
            
            user_html = render_to_string('emails/user_summary.html', {'submission': submission})
            
            user_msg = EmailMultiAlternatives(
                subject=f"Your EB1/EB2 Assessment - Score: {submission.total_score}/100",
                body=f"Hi {submission.full_name},\n\nYour assessment score is {submission.total_score}/100 ({submission.readiness_band}).\n\nView your full report at the link we sent earlier.\n\nQuestions? Reply to this email.\n\nBest,\nImmigrationIntel Team",
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@immigrationintel.com'),
                to=[submission.email]
            )
            user_msg.attach_alternative(user_html, "text/html")
            user_msg.send()
            
            admin_html = render_to_string('emails/admin_notification.html', {'submission': submission})
            admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@immigrationintel.com')
            
            admin_msg = EmailMultiAlternatives(
                subject=f"New Submission: {submission.full_name} - Score: {submission.total_score}",
                body=f"New submission from {submission.full_name} ({submission.email}). Score: {submission.total_score}.",
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@immigrationintel.com'),
                to=[admin_email]
            )
            admin_msg.attach_alternative(admin_html, "text/html")
            admin_msg.send()
            
            submission.email_sent = True
            submission.save(update_fields=['email_sent'])
            
            logger.info(f"Submission emails sent for {submission_id}")
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to send submission emails for {submission_id}: {e}")
            logger.error(traceback.format_exc())
    
    thread = threading.Thread(target=_task)
    thread.daemon = True
    thread.start()
    logger.info(f"Started submission email task for {submission_id}")
