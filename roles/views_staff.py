from django.contrib.auth.models import User
from django.http import HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from core.models import Profile, Skill
from .decorators import role_required
from .models import (
    StaffDetail, Opportunity, CareerEvent, MentorshipRequest,
    GuidanceRequest, ResumeReview, StudentActivity,
)


def _staff_detail(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    detail, _ = StaffDetail.objects.get_or_create(profile=profile)
    return profile, detail


@role_required('staff')
def dashboard(request):
    profile, detail = _staff_detail(request.user)
    students = Profile.objects.filter(role='student')
    total_students = students.count()
    needing_guidance = GuidanceRequest.objects.filter(status='open').count()
    pending_reviews = ResumeReview.objects.filter(status='pending').count()
    avg_readiness_val = round(sum(s.readiness_score for s in students) / total_students) if total_students else 0
    recent_activity = StudentActivity.objects.select_related('student').all()[:6]
    guidance_requests = GuidanceRequest.objects.select_related('student').filter(status='open')[:5]
    upcoming_events = CareerEvent.objects.filter(event_date__gte=timezone.now().date())[:4]

    context = dict(
        profile=profile, detail=detail, active='dashboard',
        total_students=total_students, needing_guidance=needing_guidance,
        pending_reviews=pending_reviews, avg_readiness=avg_readiness_val,
        recent_activity=recent_activity, guidance_requests=guidance_requests,
        upcoming_events=upcoming_events,
        chart_labels=["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        chart_values=[58, 63, 67, 71, avg_readiness_val or 74, avg_readiness_val or 76],
    )
    return render(request, 'staff/dashboard.html', context)


@role_required('staff')
def students(request):
    profile, detail = _staff_detail(request.user)
    student_list = Profile.objects.filter(role='student').select_related('user')
    context = dict(profile=profile, active='students', student_list=student_list)
    return render(request, 'staff/students.html', context)


@role_required('staff')
def student_profile(request, user_id):
    profile, detail = _staff_detail(request.user)
    # Staff may only open real student accounts, never other roles.
    student_user = get_object_or_404(User, id=user_id, profile__role='student')
    student_profile_obj, _ = Profile.objects.get_or_create(user=student_user)
    skills = student_profile_obj.skills.all()
    activities = StudentActivity.objects.filter(student=student_user)[:8]
    context = dict(profile=profile, active='students', student=student_user,
                    student_profile=student_profile_obj, skills=skills, activities=activities)
    return render(request, 'staff/student_profile.html', context)


@role_required('staff')
def student_progress(request):
    profile, detail = _staff_detail(request.user)
    students_qs = Profile.objects.filter(role='student').select_related('user')
    context = dict(profile=profile, active='progress', students=students_qs)
    return render(request, 'staff/student_progress.html', context)


@role_required('staff')
def resume_review(request):
    profile, detail = _staff_detail(request.user)
    if request.method == 'POST':
        review_id = request.POST.get('review_id')
        review = get_object_or_404(ResumeReview, id=review_id)
        review.status = 'reviewed'
        review.notes = request.POST.get('notes', '')
        review.reviewer = request.user
        review.save()
        return redirect('staff:resume_review')
    reviews = ResumeReview.objects.select_related('student').all()
    context = dict(profile=profile, active='resume_review', reviews=reviews)
    return render(request, 'staff/resume_review.html', context)


@role_required('staff')
def skill_analysis(request):
    profile, detail = _staff_detail(request.user)
    skills = Skill.objects.select_related('profile__user').filter(profile__role='student')
    low_skills = skills.order_by('current')[:8]
    context = dict(profile=profile, active='skill_analysis', low_skills=low_skills)
    return render(request, 'staff/skill_analysis.html', context)


@role_required('staff')
def career_guidance(request):
    profile, detail = _staff_detail(request.user)
    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        gr = get_object_or_404(GuidanceRequest, id=req_id)
        new_status = request.POST.get('status', '')
        if new_status not in dict(GuidanceRequest.STATUS_CHOICES):
            return HttpResponseBadRequest("Invalid status.")
        gr.status = new_status
        gr.staff = request.user
        gr.save()
        return redirect('staff:career_guidance')
    requests_qs = GuidanceRequest.objects.select_related('student').all()
    context = dict(profile=profile, active='guidance', requests_qs=requests_qs)
    return render(request, 'staff/career_guidance.html', context)


@role_required('staff')
def opportunities(request):
    profile, detail = _staff_detail(request.user)
    opps = Opportunity.objects.all()[:30]
    context = dict(profile=profile, active='opportunities', opportunities=opps)
    return render(request, 'staff/opportunities.html', context)


@role_required('staff')
def events(request):
    profile, detail = _staff_detail(request.user)
    events_qs = CareerEvent.objects.all()
    context = dict(profile=profile, active='events', events=events_qs)
    return render(request, 'staff/events.html', context)


@role_required('staff')
def reports(request):
    profile, detail = _staff_detail(request.user)
    students_qs = Profile.objects.filter(role='student')
    total = students_qs.count()
    placed_ready = students_qs.filter(readiness_score__gte=80).count()
    context = dict(
        profile=profile, active='reports', total_students=total, placed_ready=placed_ready,
        chart_labels=["Technical", "Soft Skills", "Leadership", "Domain"],
        chart_values=[62, 74, 55, 68],
    )
    return render(request, 'staff/reports.html', context)


@role_required('staff')
def staff_profile(request):
    profile, detail = _staff_detail(request.user)
    context = dict(profile=profile, detail=detail, active='profile')
    return render(request, 'staff/profile.html', context)
