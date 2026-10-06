from django.contrib.auth.models import User
from django.db import models

from core.models import Profile


# ---------------------------------------------------------------- profiles
class StudentDetail(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='student_detail')
    register_number = models.CharField(max_length=50, blank=True, default='')
    department = models.CharField(max_length=120, blank=True, default='')
    year = models.CharField(max_length=20, blank=True, default='')

    def __str__(self):
        return f"StudentDetail<{self.profile.user.username}>"


class StaffDetail(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='staff_detail')
    employee_id = models.CharField(max_length=50, blank=True, default='')
    department = models.CharField(max_length=120, default='Placement Cell')
    designation = models.CharField(max_length=120, default='Career Counselor')
    students_assigned = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"StaffDetail<{self.profile.user.username}>"


class AlumniDetail(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='alumni_detail')
    current_company = models.CharField(max_length=120, default='—')
    designation = models.CharField(max_length=120, default='—')
    graduation_year = models.PositiveIntegerField(default=2022)
    experience_years = models.PositiveIntegerField(default=1)
    industry = models.CharField(max_length=120, default='Technology')
    bio = models.TextField(blank=True, default='')
    willing_to_mentor = models.BooleanField(default=True)

    def __str__(self):
        return f"AlumniDetail<{self.profile.user.username}>"


class AdminDetail(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='admin_detail')
    designation = models.CharField(max_length=120, default='Platform Administrator')

    def __str__(self):
        return f"AdminDetail<{self.profile.user.username}>"


# ---------------------------------------------------------------- shared platform data
class Opportunity(models.Model):
    KIND_CHOICES = [('job', 'Job'), ('internship', 'Internship')]
    # 'open' == Published (kept as the stored value so existing rows/queries
    # keep working). Approval flow: pending -> open (approved) | rejected.
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'), ('open', 'Published'),
        ('rejected', 'Rejected'), ('closed', 'Closed'),
    ]

    title = models.CharField(max_length=150)
    company = models.CharField(max_length=120)
    kind = models.CharField(max_length=12, choices=KIND_CHOICES, default='job')
    location = models.CharField(max_length=120, default='Remote')
    pay = models.CharField(max_length=80, blank=True, default='')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='open')
    posted_by_alumni = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='posted_opportunities')
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Added for alumni posting + skill-based recommendations.
    skills = models.CharField(max_length=300, blank=True, default='',
                              help_text="Comma-separated, e.g. Python, SQL, Django")
    eligibility = models.CharField(max_length=200, blank=True, default='')
    description = models.TextField(blank=True, default='')
    application_url = models.URLField(blank=True, default='')
    review_note = models.CharField(max_length=300, blank=True, default='')
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_opportunities')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def skill_list(self):
        return [x.strip() for x in self.skills.split(',') if x.strip()]

    def __str__(self):
        return f"{self.title} @ {self.company}"


class CareerEvent(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, default='')
    event_date = models.DateField()
    location = models.CharField(max_length=120, default='Campus Auditorium')
    organizer = models.CharField(max_length=120, default='Placement Cell')

    class Meta:
        ordering = ['event_date']

    def __str__(self):
        return self.title


class Course(models.Model):
    title = models.CharField(max_length=150)
    provider = models.CharField(max_length=120, default='CareerMind Learning')
    category = models.CharField(max_length=80, default='Technical')
    duration_weeks = models.PositiveIntegerField(default=4)
    enrolled_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title


class MentorshipRequest(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined'), ('completed', 'Completed')]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentorship_requests_made')
    alumni = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='mentorship_requests_received')
    topic = models.CharField(max_length=150, default='Career Guidance')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class GuidanceRequest(models.Model):
    STATUS_CHOICES = [('open', 'Open'), ('in_progress', 'In Progress'), ('resolved', 'Resolved')]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guidance_requests')
    staff = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='guidance_assigned')
    topic = models.CharField(max_length=150, default='Career Guidance')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class ResumeReview(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'), ('reviewed', 'Reviewed'),
        ('changes_requested', 'Improvement Requested'),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resume_reviews')
    # The specific resume the student submitted for review (null for rows
    # created before this field existed).
    resume = models.ForeignKey('core.Resume', null=True, blank=True, on_delete=models.SET_NULL, related_name='reviews')
    reviewer = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviews_done')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, default='')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']


class StudentActivity(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    description = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Student activities'


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=200)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Referral(models.Model):
    STATUS_CHOICES = [('submitted', 'Submitted'), ('in_review', 'In Review'), ('hired', 'Hired'), ('rejected', 'Rejected')]
    alumni = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_made')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_received')
    opportunity = models.ForeignKey(Opportunity, null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='submitted')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
