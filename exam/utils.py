import csv
from .models import Section, QuestionMeta, Attempt

def process_answer_key(exam_instance):
    # Read CSV file
    # Ensure file pointer is at the beginning
    exam_instance.answer_key_file.seek(0)
    decoded_file = exam_instance.answer_key_file.read().decode('utf-8').splitlines()

    # Use standard CSV reader to handle quoting correctly
    reader = csv.DictReader(decoded_file, skipinitialspace=True)

    # Strip whitespace from headers
    if reader.fieldnames:
        reader.fieldnames = [name.strip() for name in reader.fieldnames]

    # Clear existing questions to prevent duplicates if re-processed
    # Note: This deletes all questions for this exam!
    QuestionMeta.objects.filter(exam=exam_instance).delete()
    Section.objects.filter(exam=exam_instance).delete()

    questions_to_create = []

    for row in reader:
        # Clean row data
        row = {k: (v.strip() if v else '') for k, v in row.items() if k is not None}

        # Get or Create Section
        section_name = row.get('Section', 'Default')
        section, _ = Section.objects.get_or_create(
            exam=exam_instance,
            name=section_name
        )

        # Determine Question Type logic
        q_type = row.get('Type', 'MCQ').strip().upper()

        # Create Question Object
        try:
             q = QuestionMeta(
                exam=exam_instance,
                section=section,
                question_number=int(row['Question No']),
                question_type=q_type,
                correct_answer=row.get('Key/Range', ''),
                marks_positive=float(row.get('Marks', 1.0)),
                marks_negative=float(row.get('Negative', 0.0))
            )
             questions_to_create.append(q)
        except ValueError as e:
            print(f"Skipping invalid row {row}: {e}")
            continue

    # Bulk create for performance
    QuestionMeta.objects.bulk_create(questions_to_create)

def calculate_score(attempt_id):
    attempt = Attempt.objects.get(id=attempt_id)
    responses = attempt.responses.all()
    total_score = 0

    for response in responses:
        q_meta = response.question
        user_val = response.user_input
        correct_val = q_meta.correct_answer

        is_correct = False

        if not user_val:
            # Skip scoring if no input
            response.is_correct = False
            response.marks_awarded = 0
            response.save()
            continue

        # MCQ Logic: Exact Match
        if q_meta.question_type == 'MCQ':
            if user_val == correct_val:
                is_correct = True

        # MSQ Logic: Set Comparison (Order independent)
        elif q_meta.question_type == 'MSQ':
            # Assuming user_val and correct_val are sorted strings like "A,C"
            # Normalize strings by splitting, stripping, sorting, and joining
            u_set = set(x.strip() for x in user_val.split(','))
            c_set = set(x.strip() for x in correct_val.split(','))
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
                     # Exact value match with small tolerance
                     if abs(u_float - float(correct_val)) < 1e-9:
                         is_correct = True
            except (ValueError, AttributeError):
                is_correct = False

        # Apply Marks
        if is_correct:
            marks = q_meta.marks_positive
            total_score += marks
        else:
            # Negative marking only applies if attempted (status!= not_answered)
            # And typically only for MCQs in GATE (but can be generalized)
            # If status is "answered" or "marked_for_review_answered"
            if 'answered' in response.status and q_meta.marks_negative > 0:
                marks = -q_meta.marks_negative
                total_score += marks
            else:
                marks = 0

        # Save per-question result
        response.is_correct = is_correct
        response.marks_awarded = marks
        response.save()

    attempt.total_score = total_score
    attempt.save()
