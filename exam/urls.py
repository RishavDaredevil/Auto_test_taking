from django.urls import path
from django.views.generic import TemplateView
from .views import (
    ExamListView, ExamDetailView, StartAttemptView, AttemptView,
    SubmitAttemptView, AttemptHistoryView, AttemptResultView
)

urlpatterns = [
    path('', ExamListView.as_view(), name='exam_list'),
    path('exam/<slug:slug>/', ExamDetailView.as_view(), name='exam_detail'),
    path('exam/<slug:slug>/start/', StartAttemptView.as_view(), name='start_attempt'),
    path('attempt/<int:attempt_id>/', AttemptView.as_view(), name='attempt'),
    path('attempt/<int:attempt_id>/submit/', SubmitAttemptView.as_view(), name='submit_attempt'),
    path('history/', AttemptHistoryView.as_view(), name='attempt_history'),
    path('result/<int:attempt_id>/', AttemptResultView.as_view(), name='attempt_result'),
    path('calculator/', TemplateView.as_view(template_name='exam/calculator.html'), name='calculator'),
]
