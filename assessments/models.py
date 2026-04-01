from django.db import models

class Submission(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, null=True)
    
    PETITION_CHOICES = [
        ('EB1A', 'EB1A'),
        ('EB2_NIW', 'EB2 NIW'),
        ('NOT_SURE', 'Not sure')
    ]
    petition_type_interest = models.CharField(max_length=50, choices=PETITION_CHOICES, default='NOT_SURE')
    
    raw_answers = models.JSONField(default=dict, blank=True)
    total_score = models.IntegerField(default=0)
    readiness_band = models.CharField(max_length=100, blank=True, null=True)
    
    ELIGIBILITY_CHOICES = [
        ('LIKELY_EB1A', 'Likely EB1A'),
        ('LIKELY_EB2_NIW', 'Likely EB2 NIW'),
        ('BOTH_POSSIBLE', 'Both possible'),
        ('NOT_READY', 'Not ready')
    ]
    eb1_eligibility = models.CharField(max_length=50, choices=ELIGIBILITY_CHOICES, blank=True, null=True)
    email_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} - {self.email}"

class CategoryScore(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='category_scores')
    category_name = models.CharField(max_length=255)
    score = models.IntegerField(default=0)
    max_score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.submission.full_name} - {self.category_name} ({self.score}/{self.max_score})"

class ScoringRule(models.Model):
    category_name = models.CharField(max_length=255)
    rule_name = models.CharField(max_length=255)
    condition = models.TextField(help_text="Text or JSON logic for the condition")
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.category_name}: {self.rule_name} (+{self.points})"

