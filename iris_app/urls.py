from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_landing, name='home'),
    path('login/', views.login_view, name='login'),
    path('challenges/', views.challenge_list, name='challenge_list'),
    path('logout/', views.logout_view, name='logout'),
    path('post-challenge/', views.post_challenge, name='post_challenge'),
    path('manage-panels/<uuid:challenge_id>/', views.manage_panels, name='manage_panels'),
    path('manage-mentors/<uuid:challenge_id>/', views.manage_mentors, name='manage_mentors'),
    path('submit-challenge/<uuid:challenge_id>/', views.submit_challenge, name='submit_challenge'),
    path('my-ideas/', views.my_ideas, name='my_ideas'),
    path('submit-idea/<uuid:challenge_id>/', views.submit_idea, name='submit_idea'),
    
    # Grassroot Idea Flow
    path('submit-grassroot-idea/', views.submit_grassroot_idea, name='submit_grassroot_idea'),
    path('get-subcategories/', views.get_subcategories, name='get_subcategories'),
    path('grassroot-dashboard/', views.grassroot_dashboard, name='grassroot_dashboard'),
    path('rm-dashboard/', views.rm_dashboard, name='rm_dashboard'),
    path('ibu-dashboard/', views.ibu_dashboard, name='ibu_dashboard'),
    path('evaluate-grassroot/<uuid:idea_id>/', views.evaluate_grassroot, name='evaluate_grassroot'),
    path('rework-grassroot/<uuid:idea_id>/', views.rework_grassroot, name='rework_grassroot'),
    path('customer-input/<uuid:idea_id>/', views.customer_input, name='customer_input'),
    path('challenge-suggestions/', views.challenge_suggestions, name='challenge_suggestions'),
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/mark-read/<uuid:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('reports/', views.reports_view, name='reports_view'),
    path('reports/export/', views.export_report_csv, name='export_report_csv'),
]
