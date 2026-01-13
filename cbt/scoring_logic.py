from .models import Attempt, Response

def calculate_score(attempt_id):
    attempt = Attempt.objects.get(id=attempt_id)
    responses = attempt.responses.all()
    total_score = 0
    responses_to_update = []

    for response in responses:
        q_meta = response.question
        user_val = response.user_input
        correct_val = q_meta.correct_answer

        is_correct = False

        if not user_val:
            # Not answered
            pass

        # MCQ Logic: Exact Match
        elif q_meta.question_type == 'MCQ':
            if user_val.strip().upper() == correct_val.strip().upper():
                is_correct = True

        # MSQ Logic: Set Comparison (Order independent)
        elif q_meta.question_type == 'MSQ':
            # Assuming user_val and correct_val are sorted strings like "A,C"
            # Split, sort, and compare lists
            u_set = set(x.strip().upper() for x in user_val.split(','))
            c_set = set(x.strip().upper() for x in correct_val.split(',')) # Assuming Answer Key uses comma or semicolon? Blueprint said "A;C" in one place, "A,B,D" in another.
            # Blueprint example: "Core, 3, MSQ, A;C, 2, 0"
            # Blueprint text: "For MSQ: 'A,B,D' (sorted string)"
            # I will handle both comma and semicolon

            c_vals = correct_val.replace(';', ',').split(',')
            c_set = set(x.strip().upper() for x in c_vals)

            if u_set == c_set:
                is_correct = True

        # NAT Logic: Range Comparison
        elif q_meta.question_type == 'NAT':
            try:
                u_float = float(user_val)
                # correct_val format "min:max" e.g., "5.1:5.3"
                if ':' in correct_val:
                    min_val, max_val = map(float, correct_val.split(':'))
                    # Inclusive comparison with tolerance
                    if min_val <= u_float <= max_val:
                        is_correct = True
                else:
                    # Exact match (single value)
                    if abs(u_float - float(correct_val)) < 1e-6:
                        is_correct = True
            except (ValueError, AttributeError):
                is_correct = False

        # Apply Marks
        if is_correct:
            marks = q_meta.marks_positive
            total_score += marks
        else:
            # Negative marking only applies if attempted (status!= not_answered)
            # And typically only for MCQs in GATE
            if response.status == 'answered' and q_meta.question_type == 'MCQ':
                marks = -q_meta.marks_negative
                total_score += marks
            else:
                marks = 0

        # Save per-question result
        response.is_correct = is_correct
        response.marks_awarded = marks
        responses_to_update.append(response)

    Response.objects.bulk_update(responses_to_update, ['is_correct', 'marks_awarded'])

    attempt.total_score = total_score
    attempt.save()
