from django.urls import path
from . import views

urlpatterns = [
    # Resume Management & NLP Extraction
    path('resume/upload/', views.resume_upload_view, name='resume_upload'),
    path('resume/<int:resume_id>/', views.resume_detail_view, name='resume_detail'),

    # Interview Setup & Live Room
    path('setup/', views.interview_setup_view, name='interview_setup'),
    path('room/<int:session_id>/', views.interview_room_view, name='interview_room'),
    path('result/<int:session_id>/', views.interview_result_view, name='interview_result'),

    # History & Analytics
    path('history/', views.interview_history_view, name='interview_history'),
    path('performance/', views.performance_dashboard_view, name='performance_dashboard'),
    path('roadmap/', views.learning_roadmap_view, name='learning_roadmap'),

    # AJAX / Voice APIs
    path('api/submit-answer/', views.api_submit_answer, name='api_submit_answer'),
    path('api/end-interview/', views.api_end_interview, name='api_end_interview'),
]
