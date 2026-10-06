from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from core.models import Profile
from .decorators import role_required
from .models import (
    AlumniDetail, Opportunity, CareerEvent, MentorshipRequest,
    Referral, Message,
)


def _alumni_detail(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    detail, _ = AlumniDetail.objects.get_or_create(profile=profile)
    return profile, detail


@role_required('alumni')
def dashboard(request):
    profile, detail = _alumni_detail(request.user)
    mentorship_requests = MentorshipRequest.objects.filter(alumni=request.user, status='pending').select_related('student')
    connected_students = MentorshipRequest.objects.filter(alumni=request.user, status='accepted').select_related('student')
    opportunities = Opportunity.objects.filter(posted_by_alumni=request.user)[:5]
    upcoming_events = CareerEvent.objects.filter(event_date__gte=timezone.now().date())[:4]
    recent_messages = Message.objects.filter(recipient=request.user).select_related('sender')[:5]
    context = dict(
        profile=profile, detail=detail, active='dashboard',
        mentorship_requests=mentorship_requests, connected_students=connected_students,
        opportunities=opportunities, upcoming_events=upcoming_events, recent_messages=recent_messages,
    )
    return render(request, 'alumni/dashboard.html', context)


@role_required('alumni')
def profile_view(request):
    profile, detail = _alumni_detail(request.user)
    if request.method == 'POST':
        detail.current_company = request.POST.get('current_company', detail.current_company)
        detail.designation = request.POST.get('designation', detail.designation)
        detail.industry = request.POST.get('industry', detail.industry)
        detail.bio = request.POST.get('bio', detail.bio)
        detail.save()
        return redirect('alumni:profile')
    context = dict(profile=profile, detail=detail, active='profile')
    return render(request, 'alumni/profile.html', context)


@role_required('alumni')
def career_journey(request):
    profile, detail = _alumni_detail(request.user)
    context = dict(profile=profile, detail=detail, active='journey')
    return render(request, 'alumni/career_journey.html', context)


@role_required('alumni')
def skills(request):
    profile, detail = _alumni_detail(request.user)
    context = dict(profile=profile, detail=detail, active='skills', skills=profile.skills.all())
    return render(request, 'alumni/skills.html', context)


@role_required('alumni')
def mentorship(request):
    profile, detail = _alumni_detail(request.user)
    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        action = request.POST.get('action')
        mr = get_object_or_404(MentorshipRequest, id=req_id, alumni=request.user)
        mr.status = 'accepted' if action == 'accept' else 'declined'
        mr.save()
        return redirect('alumni:mentorship')
    all_requests = MentorshipRequest.objects.filter(alumni=request.user).select_related('student')
    context = dict(profile=profile, detail=detail, active='mentorship', requests_qs=all_requests)
    return render(request, 'alumni/mentorship.html', context)


@role_required('alumni')
def students(request):
    profile, detail = _alumni_detail(request.user)
    student_list = Profile.objects.filter(role='student').select_related('user')[:30]
    context = dict(profile=profile, active='students', student_list=student_list)
    return render(request, 'alumni/students.html', context)


@role_required('alumni')
def opportunities(request):
    profile, detail = _alumni_detail(request.user)
    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        company = (request.POST.get('company') or '').strip()
        kind = request.POST.get('kind', 'job')
        if not title or not company or kind not in ('job', 'internship'):
            messages.error(request, "Title, company and a valid type are required.")
            return redirect('alumni:opportunities')
        # Alumni posts never go live on their own: they wait for Admin approval.
        Opportunity.objects.create(
            title=title[:150], company=company[:120], kind=kind,
            location=(request.POST.get('location') or 'Remote').strip()[:120],
            pay=(request.POST.get('pay') or '').strip()[:80],
            status='pending', posted_by_alumni=request.user,
        )
        messages.success(request, "Submitted for admin approval. It will be visible to students once approved.")
        return redirect('alumni:opportunities')
    my_opps = Opportunity.objects.filter(posted_by_alumni=request.user)
    all_opps = Opportunity.objects.exclude(posted_by_alumni=request.user)[:15]
    context = dict(profile=profile, active='opportunities', my_opps=my_opps, all_opps=all_opps)
    return render(request, 'alumni/opportunities.html', context)


@role_required('alumni')
def referrals(request):
    profile, detail = _alumni_detail(request.user)
    referral_list = Referral.objects.filter(alumni=request.user).select_related('student', 'opportunity')
    context = dict(profile=profile, active='referrals', referral_list=referral_list)
    return render(request, 'alumni/referrals.html', context)


@role_required('alumni')
def events(request):
    profile, detail = _alumni_detail(request.user)
    events_qs = CareerEvent.objects.all()
    context = dict(profile=profile, active='events', events=events_qs)
    return render(request, 'alumni/events.html', context)


@role_required('alumni')
def messages_view(request):
    profile, detail = _alumni_detail(request.user)
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        body = request.POST.get('body')
        if recipient_id and body:
            Message.objects.create(sender=request.user, recipient_id=recipient_id, body=body)
        return redirect('alumni:messages')
    inbox = Message.objects.filter(recipient=request.user).select_related('sender')
    sent = Message.objects.filter(sender=request.user).select_related('recipient')
    context = dict(profile=profile, active='messages', inbox=inbox, sent=sent)
    return render(request, 'alumni/messages.html', context)


@role_required('alumni')
def settings_view(request):
    profile, detail = _alumni_detail(request.user)
    if request.method == 'POST':
        detail.willing_to_mentor = bool(request.POST.get('willing_to_mentor'))
        detail.save()
        return redirect('alumni:settings')
    context = dict(profile=profile, detail=detail, active='settings')
    return render(request, 'alumni/settings.html', context)
