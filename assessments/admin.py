import csv
from django.contrib import admin
from django.http import HttpResponse
from .models import Submission, CategoryScore, ScoringRule

@admin.action(description='Export Selected to CSV')
def export_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="submissions.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Email', 'Score', 'Band', 'EB1 Eligibility', 'Created At'])
    for obj in queryset:
        writer.writerow([obj.pk, obj.full_name, obj.email, obj.total_score, obj.readiness_band, obj.get_eb1_eligibility_display(), obj.created_at])
    return response

class CategoryScoreInline(admin.TabularInline):
    model = CategoryScore
    extra = 0
    readonly_fields = ('category_name', 'score', 'max_score')
    can_delete = False

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'total_score', 'readiness_band', 'eb1_eligibility', 'created_at')
    list_filter = ('readiness_band', 'eb1_eligibility', 'petition_type_interest', 'created_at')
    search_fields = ('full_name', 'email')
    readonly_fields = ('created_at', 'raw_answers', 'total_score', 'readiness_band')
    inlines = [CategoryScoreInline]
    actions = [export_to_csv]
    
    fieldsets = (
        ('Applicant Information', {
            'fields': ('full_name', 'email', 'phone', 'petition_type_interest')
        }),
        ('Assessment Results', {
            'fields': ('total_score', 'readiness_band', 'eb1_eligibility', 'email_sent')
        }),
        ('Raw Validation Data', {
            'fields': ('raw_answers',),
            'classes': ('collapse',),
            'description': 'Full JSON dump of the raw assessment form answers.'
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )

@admin.register(CategoryScore)
class CategoryScoreAdmin(admin.ModelAdmin):
    list_display = ('submission', 'category_name', 'score', 'max_score')
    search_fields = ('submission__full_name', 'category_name')

@admin.register(ScoringRule)
class ScoringRuleAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'rule_name', 'points')
    search_fields = ('category_name', 'rule_name')
    list_filter = ('category_name',)


