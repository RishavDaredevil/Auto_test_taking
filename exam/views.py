from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from .models import Exam, Attempt, Response, QuestionMeta
from .utils import calculate_score
import json

class ExamListView(ListView):
    model = Exam
    template_name = 'exam/exam_list.html'
    context_object_name = 'exams'
    queryset = Exam.objects.filter(is_active=True)

class ExamDetailView(DetailView):
    model = Exam
    template_name = 'exam/exam_detail.html'
    context_object_name = 'exam'

class StartAttemptView(LoginRequiredMixin, View):
    def post(self, request, slug):
        exam = get_object_or_404(Exam, slug=slug)
        # Check if unfinished attempt exists
        unfinished_attempt = Attempt.objects.filter(
            user=request.user,
            exam=exam,
            is_submitted=False
        ).first()

        if unfinished_attempt:
            return redirect('attempt', attempt_id=unfinished_attempt.id)

        # Create new attempt
        attempt = Attempt.objects.create(user=request.user, exam=exam)

        # Initialize Responses for all questions
        questions = QuestionMeta.objects.filter(exam=exam)
        responses = [Response(attempt=attempt, question=q) for q in questions]
        Response.objects.bulk_create(responses)

        return redirect('attempt', attempt_id=attempt.id)

class AttemptView(LoginRequiredMixin, DetailView):
    model = Attempt
    template_name = 'exam/attempt.html'
    context_object_name = 'attempt'
    pk_url_kwarg = 'attempt_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Serialize questions and responses for JS
        responses = self.object.responses.select_related('question', 'question__section').all()

        # Group questions by section
        sections = {}
        for r in responses:
            sec_name = r.question.section.name if r.question.section else "General"
            if sec_name not in sections:
                sections[sec_name] = []
            sections[sec_name].append(r)

        context['sections'] = sections

        # Create a clean JSON structure for the frontend state
        exam_data = {
            'questions': {},
            'duration_seconds': self.object.exam.duration_minutes * 60,
            'current_state': self.object.current_state
        }

        for r in responses:
            exam_data['questions'][r.question.question_number] = {
                'id': r.question.id,
                'type': r.question.question_type,
                'status': r.status,
                'user_input': r.user_input,
                'section': r.question.section.name if r.question.section else "General"
            }

        context['exam_data_json'] = json.dumps(exam_data)
        return context

    def post(self, request, *args, **kwargs):
        # Handle heartbeat / auto-save
        attempt = self.get_object()
        data = json.loads(request.body)

        # Update current state (timer, etc)
        if 'current_state' in data:
            attempt.current_state = data['current_state']
            attempt.save(update_fields=['current_state'])

        # Update specific response
        if 'question_id' in data:
            response = get_object_or_404(Response, attempt=attempt, question_id=data['question_id'])
            response.user_input = data.get('user_input')
            response.status = data.get('status', 'not_visited')
            response.save()

        return JsonResponse({'status': 'saved'})

class SubmitAttemptView(LoginRequiredMixin, View):
    def post(self, request, attempt_id):
        attempt = get_object_or_404(Attempt, id=attempt_id, user=request.user)
        attempt.is_submitted = True
        attempt.save()

        calculate_score(attempt.id)

        return redirect('attempt_result', attempt_id=attempt.id)

class AttemptHistoryView(LoginRequiredMixin, ListView):
    model = Attempt
    template_name = 'exam/attempt_history.html'
    context_object_name = 'attempts'

    def get_queryset(self):
        return Attempt.objects.filter(user=self.request.user, is_submitted=True).order_by('-started_at')

class AttemptResultView(LoginRequiredMixin, DetailView):
    model = Attempt
    template_name = 'exam/attempt_result.html'
    context_object_name = 'attempt'
    pk_url_kwarg = 'attempt_id'
