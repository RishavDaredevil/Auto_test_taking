import csv
from .models import Section, QuestionMeta

def process_answer_key(exam_instance):
    # Read CSV file
    # We need to ensure we are at the beginning of the file if it was read before
    exam_instance.answer_key_file.open()
    decoded_file = exam_instance.answer_key_file.read().decode('utf-8').splitlines()
    reader = csv.DictReader(decoded_file)

    # Strip whitespace from headers just in case
    reader.fieldnames = [name.strip() for name in reader.fieldnames]

    questions_to_create = []

    for row in reader:
        # Get or Create Section
        # We strip whitespace from values
        section_name = row['Section'].strip()
        section, _ = Section.objects.get_or_create(
            exam=exam_instance,
            name=section_name
        )

        # Determine Question Type logic
        q_type = row['Type'].strip().upper()

        # Handle potential key names
        correct_answer = row.get('Key/Range', row.get('Key', '')).strip()

        # Create Question Object
        q = QuestionMeta(
            exam=exam_instance,
            section=section,
            question_number=int(row['Question No']),
            question_type=q_type,
            correct_answer=correct_answer,
            marks_positive=float(row['Marks']),
            marks_negative=float(row['Negative'])
        )
        questions_to_create.append(q)

    # Bulk create for performance
    QuestionMeta.objects.bulk_create(questions_to_create)
