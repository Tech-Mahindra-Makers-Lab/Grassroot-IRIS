from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_landing, name='home'),
    path('login/', views.login_view, name='login'),
    path('challenges/', views.challenge_list, name='challenge_list'),
    path('challenges/<uuid:challenge_id>/', views.challenge_detail, name='challenge_detail'),
    path('logout/', views.logout_view, name='logout'),
    path('post-challenge/', views.post_challenge, name='post_challenge'),
    path('manage-panels/<uuid:challenge_id>/', views.manage_panels, name='manage_panels'),
    path('manage-mentors/<uuid:challenge_id>/', views.manage_mentors, name='manage_mentors'),
    path('submit-challenge/<uuid:challenge_id>/', views.submit_challenge, name='submit_challenge'),
    path('my-ideas/', views.my_ideas, name='my_ideas'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    # Review and Evaluation Dashboard
    path('review-dashboard/', views.review_dashboard, name='review_dashboard'),
    path('review-dashboard/idea-detail/<uuid:idea_id>/', views.idea_detail, name='view_idea_detail'),
    path('reviewer-idea-page/<uuid:idea_id>/', views.reviewer_idea_page, name='reviewer_idea_page'),
    path('submit-evaluation/<uuid:idea_id>/', views.submit_evaluation, name='submit_evaluation'),
    # Admin Dashboard
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('challenge-view/<uuid:challenge_id>/', views.view_challenge_admin, name='view_challenge_admin'),
    path('update-challenge-admin/<uuid:challenge_id>/', views.updateChallengeByAdmin, name='updateChallengeByAdmin'),
    path('delete-challenge-admin/<uuid:challenge_id>/', views.deleteChallengeByAdmin, name='deleteChallengeByAdmin'),

    path('manage-panel/<uuid:challenge_id>/', views.managepanel, name='managepanel'),
    path('download-challenge-summary/<uuid:challenge_id>/', views.download_challenge_summary, name='download_challenge_summary'),

    path('idea-details/<uuid:challenge_id>/', views.idea_details, name='idea_details'),
    path('submit-idea/<uuid:challenge_id>/', views.submit_idea, name='submit_idea'),
    path('challenge-register/<uuid:challenge_id>/', views.challenge_register, name='challenge_register'),
    path('submit-registration/<uuid:challenge_id>/', views.submit_registration, name='submit_registration'),
    path('registernow/<uuid:challenge_id>/', views.registernow, name='registernow'),
    path('employee_search/', views.employee_search, name='employee_search'),

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
    path('ibu-search/', views.ibu_search, name='ibu_search'),
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/mark-read/<uuid:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_as_read, name='mark_all_notifications_as_read'),
    path('reports/', views.reports_view, name='reports_view'),
    path('reports/export/', views.export_report_csv, name='export_report_csv'),
    path('view-user-idea/<uuid:idea_id>/', views.viewuseridea, name='viewuseridea'),
]
