from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from .models import Submission, CategoryScore
from .services import ScoringEngine
import json
import logging

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

                # Create submission
                submission = Submission.objects.create(
                    full_name=full_name,
                    petition_type_interest=petition_type_interest,
                    email=email,
                    phone=phone,
                    raw_answers=raw_answers,
                    total_score=result['total_score'],
                    readiness_band=result['readiness_band']
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

            # Send Emails (outside transaction to prevent holding locks during network I/O)
            try:
                from django.core.mail import EmailMultiAlternatives
                from django.template.loader import render_to_string
                from django.conf import settings
                
                # 1. Send User Summary Email
                user_subject = "Your EB1/EB2 Profile Intelligence Report"
                user_text = f"Hi {submission.full_name},\n\nYour score is {submission.total_score}/100 ({submission.readiness_band})."
                user_html = render_to_string('emails/user_summary.html', {'submission': submission})
                
                user_msg = EmailMultiAlternatives(
                    subject=user_subject,
                    body=user_text,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@immigrationintel.com'),
                    to=[submission.email]
                )
                user_msg.attach_alternative(user_html, "text/html")
                user_msg.send()

                # 2. Send Admin Notification Email
                admin_subject = f"New Submission: {submission.full_name} - Score: {submission.total_score}"
                admin_text = f"New submission from {submission.full_name} ({submission.email}). Score: {submission.total_score}."
                admin_html = render_to_string('emails/admin_notification.html', {'submission': submission})
                
                admin_msg = EmailMultiAlternatives(
                    subject=admin_subject,
                    body=admin_text,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@immigrationintel.com'),
                    to=['admin@immigrationintel.com'] # Placeholder admin email
                )
                admin_msg.attach_alternative(admin_html, "text/html")
                admin_msg.send()

                # 3. Update Submission
                submission.email_sent = True
                submission.save(update_fields=['email_sent'])
                
            except Exception as email_err:
                logger.error(f"Failed to send emails: {str(email_err)}")
                # We continue anyway to ensure the user reaches the results page.

            # Store engine result in session to avoid passing heavy params, or rely on db for results page
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
        'endeavor': 'Refine and clearly articulate your proposed endeavor and strictly document its national importance.'
    }

    context = {
        'submission': submission,
        'pk': pk,
        'result': result,
        'action_mapping': action_mapping
    }
    return render(request, 'assessments/results.html', context)
