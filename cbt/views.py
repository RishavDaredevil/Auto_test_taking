from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Exam, Attempt, QuestionMeta, Response
from .scoring_logic import calculate_score
import json

@login_required
def exam_list(request):
    exams = Exam.objects.filter(is_active=True)
    return render(request, 'cbt/exam_list.html', {'exams': exams})

@login_required
def exam_detail(request, slug):
    exam = get_object_or_404(Exam, slug=slug)
    return render(request, 'cbt/exam_detail.html', {'exam': exam})

@login_required
def start_attempt(request, slug):
    exam = get_object_or_404(Exam, slug=slug)
    if request.method == 'POST':
        # Create attempt
        attempt = Attempt.objects.create(user=request.user, exam=exam)
        return redirect('exam_interface', attempt_id=attempt.id)
    return redirect('exam_detail', slug=slug)

@login_required
def exam_interface(request, attempt_id):
    attempt = get_object_or_404(Attempt, id=attempt_id, user=request.user)
    if attempt.is_submitted:
        return redirect('exam_result', attempt_id=attempt.id)

    questions = attempt.exam.questions.all().order_by('question_number')

    # Serialize questions for JS
    questions_json = []
    for q in questions:
        questions_json.append({
            'id': q.id,
            'number': q.question_number,
            'type': q.question_type,
            'section': q.section.name if q.section else ''
        })

    context = {
        'exam': attempt.exam,
        'attempt': attempt,
        'questions_json': json.dumps(questions_json)
    }
    return render(request, 'cbt/exam_interface.html', context)

@login_required
def sync_attempt(request, attempt_id):
    if request.method == 'POST':
        attempt = get_object_or_404(Attempt, id=attempt_id, user=request.user)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'invalid json'}, status=400)

        # Update state
        attempt.current_state = data
        attempt.save()

        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def submit_attempt(request, attempt_id):
    if request.method == 'POST':
        attempt = get_object_or_404(Attempt, id=attempt_id, user=request.user)
        if attempt.is_submitted:
            return JsonResponse({'status': 'already_submitted'})

        # Get final state from DB
        state = attempt.current_state
        responses_data = state.get('responses', {})

        for q_id, r_data in responses_data.items():
            question = get_object_or_404(QuestionMeta, id=q_id)
            val = r_data.get('value')
            status = r_data.get('status', 'not_answered')

            # Create or update Response object
            Response.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    'user_input': val,
                    'status': status
                }
            )

        attempt.completed_at = timezone.now()
        attempt.is_submitted = True
        attempt.save()

        # Trigger Scoring
        calculate_score(attempt.id)

        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def exam_result(request, attempt_id):
    attempt = get_object_or_404(Attempt, id=attempt_id, user=request.user)
    if not attempt.is_submitted:
        return redirect('exam_interface', attempt_id=attempt.id)

    responses = attempt.responses.select_related('question').all().order_by('question__question_number')

    return render(request, 'cbt/exam_result.html', {'attempt': attempt, 'responses': responses})
