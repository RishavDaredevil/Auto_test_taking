import csv


def process_answer_key(exam_instance):
    # Read CSV file
    decoded_file = exam_instance.answer_key_file.read().decode('utf-8').splitlines()
    reader = csv.DictReader(decoded_file)

    questions_to_create =

    for row in reader:
        # Get or Create Section
        section, _ = Section.objects.get_or_create(
            exam=exam_instance,
            name=row
        )

        # Determine Question Type logic
        q_type = row.strip().upper()

        # Create Question Object
        q = QuestionMeta(
            exam=exam_instance,
            section=section,
            question_number=int(row['Question No']),
            question_type=q_type,
            correct_answer=row,
            marks_positive=float(row['Marks']),
            marks_negative=float(row['Negative'])
        )
        questions_to_create.append(q)

    # Bulk create for performance
    QuestionMeta.objects.bulk_create(questions_to_create)