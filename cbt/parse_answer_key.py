import csv
from .models import Section, QuestionMeta

def process_answer_key(exam_instance):
    exam_instance.answer_key_file.open()
    # Handle UTF-8 decoding properly
    decoded_file = exam_instance.answer_key_file.read().decode('utf-8').splitlines()
    reader = csv.DictReader(decoded_file)

    # Strip whitespace from headers
    reader.fieldnames = [name.strip() for name in reader.fieldnames]

    questions_to_create = []

    # Track existing sections to assign order
    existing_sections = {}
    current_order = 1

    for row in reader:
        # Skip empty rows
        if not row or not row.get('Section'):
            continue

        # Clean data
        section_name = row['Section'].strip()
        q_type = row['Type'].strip().upper() if row.get('Type') else 'MCQ'
        # Handle 'Key' or 'Key/Range' column name variation
        key_col = 'Key' if 'Key' in row else 'Key/Range'
        correct_answer = row[key_col].strip()

        # Handle Section Logic
        if section_name not in existing_sections:
            section, created = Section.objects.get_or_create(
                exam=exam_instance,
                name=section_name,
                defaults={'order': current_order}
            )
            if not created:
                # If section existed (e.g. from previous run), use its order
                current_order = section.order
            else:
                current_order += 1
            existing_sections[section_name] = section

        section = existing_sections[section_name]

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

    # Clear old questions to prevent duplicates on re-upload
    QuestionMeta.objects.filter(exam=exam_instance).delete()
    QuestionMeta.objects.bulk_create(questions_to_create)
