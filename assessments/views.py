from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.template.loader import render_to_string
from .models import Submission, CategoryScore
from .services import ScoringEngine
import json
import logging
import re
from io import BytesIO
from xhtml2pdf import pisa

logger = logging.getLogger(__name__)

def landing_page(request):
    return render(request, 'assessments/landing.html')

def assessment_form(request):
    return render(request, 'assessments/form.html')

def submit_assessment(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                full_name = request.POST.get('full_name', '')
                petition_type_interest = request.POST.get('petition_type_interest', 'NOT_SURE')
                email = request.POST.get('email', '')
                phone = request.POST.get('phone', '')

                # Build raw answers dynamically
                raw_answers = {}
                for key, value in request.POST.items():
                    if key not in ['csrfmiddlewaretoken']:
                        raw_answers[key] = value

                # Process scoring
                engine = ScoringEngine(raw_answers)
                result = engine.process()

                # Handle CV upload
                cv_file = request.FILES.get('cv')
                cv_text = None
                
                if cv_file:
                    from .services.cv_parser import CVParser
                    parser = CVParser()
                    cv_text = parser.parse_file(cv_file)
                    
                    if cv_text:
                        cv_key_info = parser.extract_key_info(cv_text)
                        raw_answers['cv_extracted'] = cv_key_info

                # Create submission
                submission = Submission.objects.create(
                    full_name=full_name,
                    petition_type_interest=petition_type_interest,
                    email=email,
                    phone=phone,
                    raw_answers=raw_answers,
                    total_score=result['total_score'],
                    readiness_band=result['readiness_band'],
                    cv=cv_file,
                    cv_text=cv_text[:50000] if cv_text else None
                )

                # Build CategoryScores
                for cat, score in result['category_scores'].items():
                    max_score = result['category_max'][cat]
                    CategoryScore.objects.create(
                        submission=submission,
                        category_name=cat,
                        score=score,
                        max_score=max_score
                    )

            # Trigger async tasks (non-blocking) - emails sent in background
            from .services.ai_tasks import AIReportGenerator, send_submission_emails_async
            AIReportGenerator.trigger(submission)
            send_submission_emails_async(submission.pk)
            
            return redirect('assessments:results', pk=submission.pk)

        except Exception as e:
            logger.error(f"Error during form submission: {str(e)}")
            messages.error(request, 'An unexpected error occurred while processing your submission. Please try again.')
            return redirect('assessments:form')

    return redirect('assessments:form')

def assessment_results(request, pk):
    submission = get_object_or_404(Submission, pk=pk)
    # We can rebuild the engine context here for UI presentation or pull from DB
    engine = ScoringEngine(submission.raw_answers)
    result = engine.process()
    
    action_mapping = {
        'publications': 'Build authority by increasing scholarly publications and tracking performance metrics.',
        'citations': 'Gather evidence of others citing or relying on your work in significant ways.',
        'awards': 'Apply for or rigorously document nationally/internationally recognized prizes for excellence.',
        'media': 'Build media visibility by getting your work featured in major trade or mainstream publications.',
        'judging': 'Seek opportunities to act as a judge or peer reviewer of the work of others in your field.',
        'leadership': 'Leverage and document your role as a leader or critical contributor in distinguished organizations.',
        'salary': 'Provide objective comparative evidence that your remuneration is significantly higher than peers.',
        'memberships': 'Pursue exclusive memberships in professional associations that require outstanding achievements.',
        'recommendations': 'Identify independent experts who can provide strong recommendation letters outlining your specific impact.',
        'speaking': 'Pursue speaking opportunities at major conferences to establish expertise.',
        'patents': 'Document and protect original contributions of major significance.',
        'endeavor': 'Refine and clearly articulate your proposed endeavor and strictly document its national importance.'
    }

    context = {
        'submission': submission,
        'pk': pk,
        'result': result,
        'action_mapping': action_mapping
    }
    return render(request, 'assessments/results.html', context)

def resend_results_email(request, pk):
    """Resend results email to user"""
    submission = get_object_or_404(Submission, pk=pk)
    
    try:
        from django.core.mail import EmailMultiAlternatives
        
        user_subject = "Your EB1/EB2 Profile Intelligence Report"
        user_text = f"Hi {submission.full_name},\n\nYour score is {submission.total_score}/100 ({submission.readiness_band}).\n\nPlease visit the link below to view your full report:\nhttp://your-domain.com/results/{submission.pk}/"
        user_html = render_to_string('emails/user_summary.html', {'submission': submission})
        
        user_msg = EmailMultiAlternatives(
            subject=user_subject,
            body=user_text,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@immigrationintel.com'),
            to=[submission.email]
        )
        user_msg.attach_alternative(user_html, "text/html")
        user_msg.send()
        
        messages.success(request, f'Results email sent to {submission.email}')
    except Exception as e:
        logger.error(f"Failed to resend email: {str(e)}")
        messages.error(request, 'Failed to send email. Please try again.')
    
    return redirect('assessments:results', pk=pk)

def get_ai_report(request, pk):
    """API endpoint to fetch AI report status and content."""
    submission = get_object_or_404(Submission, pk=pk)
    
    if submission.ai_report:
        return JsonResponse({
            'status': 'ready',
            'report': submission.ai_report
        })
    else:
        return JsonResponse({
            'status': 'generating'
        })

def regenerate_ai_report(request, pk):
    """Regenerate AI report for a submission."""
    submission = get_object_or_404(Submission, pk=pk)
    
    submission.ai_report = None
    submission.save(update_fields=['ai_report'])
    
    from .services.ai_tasks import AIReportGenerator
    AIReportGenerator.trigger(submission)
    
    return JsonResponse({'status': 'triggered'})

def download_results_pdf(request, pk):
    """Generate and download results as PDF"""
    submission = get_object_or_404(Submission, pk=pk)
    
    try:
        # Rebuild the engine context for PDF presentation
        engine = ScoringEngine(submission.raw_answers)
        result = engine.process()
        
        action_mapping = {
            'publications': 'Build authority by increasing scholarly publications and tracking performance metrics.',
            'citations': 'Gather evidence of others citing or relying on your work in significant ways.',
            'awards': 'Apply for or rigorously document nationally/internationally recognized prizes for excellence.',
            'media': 'Build media visibility by getting your work featured in major trade or mainstream publications.',
            'judging': 'Seek opportunities to act as a judge or peer reviewer of the work of others in your field.',
            'leadership': 'Leverage and document your role as a leader or critical contributor in distinguished organizations.',
            'salary': 'Provide objective comparative evidence that your remuneration is significantly higher than peers.',
            'memberships': 'Pursue exclusive memberships in professional associations that require outstanding achievements.',
            'recommendations': 'Identify independent experts who can provide strong recommendation letters outlining your specific impact.',
            'endeavor': 'Refine and clearly articulate your proposed endeavor and strictly document its national importance.'
        }
        
        context = {
            'submission': submission,
            'result': result,
            'action_mapping': action_mapping
        }
        
        # Render HTML template for PDF
        html_string = render_to_string('assessments/results_pdf.html', context)
        
        # Generate PDF
        html = BytesIO(html_string.encode('utf-8'))
        pdf = BytesIO()
        pisa.pisaDocument(html, pdf)
        
        # Return PDF as response
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '', submission.full_name.replace(" ", "_"))
        response = HttpResponse(pdf.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="EB1_EB2_Report_{safe_name}.pdf"'
        return response
        
    except Exception as e:
        logger.error(f"Failed to generate PDF: {str(e)}")
        messages.error(request, 'Failed to generate PDF. Please try again.')
        return redirect('assessments:results', pk=pk)
