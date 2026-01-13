from django.urls import path
from . import views

urlpatterns = [
    path('', views.exam_list, name='exam_list'),
    path('exam/<slug:slug>/', views.exam_detail, name='exam_detail'),
    path('exam/<slug:slug>/start/', views.start_attempt, name='start_attempt'),
    path('attempt/<int:attempt_id>/', views.exam_interface, name='exam_interface'),
    path('attempt/<int:attempt_id>/sync/', views.sync_attempt, name='sync_attempt'),
    path('attempt/<int:attempt_id>/submit/', views.submit_attempt, name='submit_attempt'),
    path('attempt/<int:attempt_id>/result/', views.exam_result, name='exam_result'),
]
