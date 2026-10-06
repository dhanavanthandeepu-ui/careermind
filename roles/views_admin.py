from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from core.models import Profile
from .decorators import role_required
from .models import (
    AdminDetail, StaffDetail, AlumniDetail, Opportunity, CareerEvent,
    Course, MentorshipRequest, Notification,
)


def _admin_detail(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    detail, _ = AdminDetail.objects.get_or_create(profile=profile)
    return profile, detail


@role_required('admin')
def dashboard(request):
    profile, detail = _admin_detail(request.user)
    total_students = Profile.objects.filter(role='student').count()
    total_staff = Profile.objects.filter(role='staff').count()
    total_alumni = Profile.objects.filter(role='alumni').count()
    active_users = User.objects.filter(is_active=True).count()
    jobs = Opportunity.objects.filter(kind='job').count()
    internships = Opportunity.objects.filter(kind='internship').count()
    pending_approvals = Opportunity.objects.filter(status='pending').count()
    events_count = CareerEvent.objects.filter(event_date__gte=timezone.now().date()).count()

    students_qs = Profile.objects.filter(role='student')
    avg_placement = round(sum(s.readiness_score for s in students_qs) / total_students) if total_students else 0

    recent_activity = [
        f"{u.first_name} {u.last_name} joined as {p.role}"
        for p, u in [(p, p.user) for p in Profile.objects.select_related('user').order_by('-id')[:6]]
    ]

    context = dict(
        profile=profile, detail=detail, active='dashboard',
        total_students=total_students, total_staff=total_staff, total_alumni=total_alumni,
        active_users=active_users, jobs=jobs, internships=internships,
        pending_approvals=pending_approvals, events_count=events_count,
        avg_placement=avg_placement, recent_activity=recent_activity,
        chart_labels=["Students", "Staff", "Alumni"],
        chart_values=[total_students, total_staff, total_alumni],
    )
    return render(request, 'admin_panel/dashboard.html', context)


@role_required('admin')
def students(request):
    profile, detail = _admin_detail(request.user)
    student_list = Profile.objects.filter(role='student').select_related('user')
    context = dict(profile=profile, active='students', student_list=student_list)
    return render(request, 'admin_panel/students.html', context)


@role_required('admin')
def staff(request):
    profile, detail = _admin_detail(request.user)
    staff_list = Profile.objects.filter(role='staff').select_related('user')
    context = dict(profile=profile, active='staff', staff_list=staff_list)
    return render(request, 'admin_panel/staff.html', context)


@role_required('admin')
def alumni(request):
    profile, detail = _admin_detail(request.user)
    alumni_list = Profile.objects.filter(role='alumni').select_related('user')
    context = dict(profile=profile, active='alumni', alumni_list=alumni_list)
    return render(request, 'admin_panel/alumni.html', context)


@role_required('admin')
def user_management(request):
    profile, detail = _admin_detail(request.user)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        target = get_object_or_404(User, id=user_id)
        target_profile, _ = Profile.objects.get_or_create(user=target)
        if action == 'deactivate' and target.pk == request.user.pk:
            messages.error(request, "You can't deactivate your own account.")
            return redirect('admin_panel:user_management')
        if action == 'deactivate':
            target.is_active = False
            target.save()
        elif action == 'activate':
            target.is_active = True
            target.save()
        elif action == 'approve':
            target_profile.is_approved = True
            target_profile.save()
        return redirect('admin_panel:user_management')
    all_profiles = Profile.objects.select_related('user').all()
    context = dict(profile=profile, active='users', all_profiles=all_profiles)
    return render(request, 'admin_panel/user_management.html', context)


@role_required('admin')
def opportunities(request):
    profile, detail = _admin_detail(request.user)
    if request.method == 'POST':
        opp_id = request.POST.get('opp_id')
        action = request.POST.get('action')
        opp = get_object_or_404(Opportunity, id=opp_id)
        if action == 'approve':
            opp.status = 'open'
        elif action == 'reject':
            opp.status = 'rejected'
        elif action == 'close':
            opp.status = 'closed'
        else:
            messages.error(request, "Unknown action.")
            return redirect('admin_panel:opportunities')
        opp.reviewed_by = request.user
        opp.reviewed_at = timezone.now()
        opp.save()
        return redirect('admin_panel:opportunities')
    opps = Opportunity.objects.select_related('posted_by_alumni').all()
    context = dict(profile=profile, active='opportunities', opportunities=opps)
    return render(request, 'admin_panel/opportunities.html', context)


@role_required('admin')
def courses(request):
    profile, detail = _admin_detail(request.user)
    if request.method == 'POST':
        Course.objects.create(
            title=request.POST.get('title'), provider=request.POST.get('provider', 'CareerMind Learning'),
            category=request.POST.get('category', 'Technical'),
            duration_weeks=request.POST.get('duration_weeks') or 4,
        )
        return redirect('admin_panel:courses')
    course_list = Course.objects.all()
    context = dict(profile=profile, active='courses', course_list=course_list)
    return render(request, 'admin_panel/courses.html', context)


@role_required('admin')
def mentorship(request):
    profile, detail = _admin_detail(request.user)
    requests_qs = MentorshipRequest.objects.select_related('student', 'alumni').all()
    context = dict(profile=profile, active='mentorship', requests_qs=requests_qs)
    return render(request, 'admin_panel/mentorship.html', context)


@role_required('admin')
def events(request):
    profile, detail = _admin_detail(request.user)
    if request.method == 'POST':
        CareerEvent.objects.create(
            title=request.POST.get('title'), description=request.POST.get('description', ''),
            event_date=request.POST.get('event_date'), location=request.POST.get('location', 'Campus Auditorium'),
            organizer=request.POST.get('organizer', 'Placement Cell'),
        )
        return redirect('admin_panel:events')
    events_qs = CareerEvent.objects.all()
    context = dict(profile=profile, active='events', events=events_qs)
    return render(request, 'admin_panel/events.html', context)


@role_required('admin')
def reports(request):
    profile, detail = _admin_detail(request.user)
    students_qs = Profile.objects.filter(role='student')
    total = students_qs.count()
    placed_ready = students_qs.filter(readiness_score__gte=80).count()
    context = dict(
        profile=profile, active='reports', total_students=total, placed_ready=placed_ready,
        chart_labels=["Q1", "Q2", "Q3", "Q4"],
        chart_values=[62, 68, 74, 80],
    )
    return render(request, 'admin_panel/reports.html', context)


@role_required('admin')
def notifications(request):
    profile, detail = _admin_detail(request.user)
    notes = Notification.objects.filter(recipient=request.user)
    context = dict(profile=profile, active='notifications', notifications=notes)
    return render(request, 'admin_panel/notifications.html', context)


@role_required('admin')
def settings_view(request):
    profile, detail = _admin_detail(request.user)
    if request.method == 'POST':
        detail.designation = request.POST.get('designation', detail.designation)
        detail.save()
        return redirect('admin_panel:settings')
    context = dict(profile=profile, detail=detail, active='settings')
    return render(request, 'admin_panel/settings.html', context)
