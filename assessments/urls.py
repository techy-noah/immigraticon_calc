from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('assessment/', views.assessment_form, name='form'),
    path('submit-assessment/', views.submit_assessment, name='submit_assessment'),
    path('results/<int:pk>/', views.assessment_results, name='results'),
    path('results/<int:pk>/download-pdf/', views.download_results_pdf, name='download_pdf'),
    path('results/<int:pk>/resend-email/', views.resend_results_email, name='resend_email'),
]
