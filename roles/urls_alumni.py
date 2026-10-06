from django.urls import path
from . import views_alumni as v

urlpatterns = [
    path('', v.dashboard, name='dashboard'),
    path('profile/', v.profile_view, name='profile'),
    path('career-journey/', v.career_journey, name='career_journey'),
    path('skills/', v.skills, name='skills'),
    path('mentorship/', v.mentorship, name='mentorship'),
    path('students/', v.students, name='students'),
    path('opportunities/', v.opportunities, name='opportunities'),
    path('referrals/', v.referrals, name='referrals'),
    path('events/', v.events, name='events'),
    path('messages/', v.messages_view, name='messages'),
    path('settings/', v.settings_view, name='settings'),
]
