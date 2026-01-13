from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import img2pdf
from PIL import Image
import io
import os
from django.core.files.base import ContentFile

class Exam(models.Model):
    """
    Represents the exam paper container.
    """
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    # The static artifact
    question_paper = models.FileField(
        upload_to='exams/pdfs/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'zip'])]
    )

    # Configuration
    duration_minutes = models.PositiveIntegerField(help_text="Duration in minutes")
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100.00)

    # The Answer Key File (CSV/JSON) acts as the blueprint
    answer_key_file = models.FileField(upload_to='exams/keys/')

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Check if question_paper is an image and convert to PDF
        if self.question_paper:
            ext = os.path.splitext(self.question_paper.name)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png']:
                try:
                    # Read content
                    if hasattr(self.question_paper, 'open'):
                         self.question_paper.open()
                    image_content = self.question_paper.read()

                    # Ensure pointer is reset if we need to read it again (though we just consume it)
                    # Use BytesIO to help PIL identify it if needed, or img2pdf directly

                    # Convert to PDF bytes using img2pdf directly on the image bytes
                    pdf_bytes = img2pdf.convert(image_content)

                    # Save as new PDF file
                    base_name = os.path.splitext(os.path.basename(self.question_paper.name))[0]
                    new_filename = f"{base_name}.pdf"

                    self.question_paper.save(new_filename, ContentFile(pdf_bytes), save=False)
                except Exception as e:
                    print(f"Error converting image to PDF: {e}")
                    pass

        super().save(*args, **kwargs)


class Section(models.Model):
    """
    Exams often have sections (e.g., General Aptitude, Core Subject).
    This allows grouping of questions in the palette.
    """
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=100)  # e.g., "Section A"
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']


class QuestionMeta(models.Model):
    """
    Metadata for each question derived from the Answer Key.
    Does NOT store question text, but stores the logic needed for scoring.
    """
    TYPE_CHOICES = (
        ('MCQ', 'Multiple Choice - Single Correct'),
        ('MSQ', 'Multiple Select - Multiple Correct'),
        ('NAT', 'Numerical Answer Type'),
    )

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='questions', null=True)

    question_number = models.PositiveIntegerField()
    question_type = models.CharField(max_length=3, choices=TYPE_CHOICES)

    # Storing the correct answer.
    # For MCQ: "A"
    # For MSQ: "A,B,D" (sorted string)
    # For NAT: "5.0:5.2" (Range format min:max)
    correct_answer = models.CharField(max_length=255)

    marks_positive = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    marks_negative = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)

    # Optional: If you want to map Q5 to Page 3 of the PDF
    pdf_page_number = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('exam', 'question_number')
        ordering = ['question_number']


class Attempt(models.Model):
    """
    Tracks a user's session for a specific exam.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attempts')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Score is nullable until calculated
    total_score = models.DecimalField(max_digits=6, decimal_places=2, null=True)

    # Status tracking
    is_submitted = models.BooleanField(default=False)

    # JSONField to store the 'State' of the exam (timer remaining, palette status)
    # This allows resuming an exam if the browser crashes.
    current_state = models.JSONField(default=dict, blank=True)


class Response(models.Model):
    """
    Individual answers given by the student.
    """
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(QuestionMeta, on_delete=models.CASCADE)

    # The actual input provided by user
    user_input = models.CharField(max_length=255, blank=True, null=True)

    # Status for the Palette (Answered, Marked for Review, etc.)
    status = models.CharField(max_length=50, default='not_visited')

    time_spent_seconds = models.PositiveIntegerField(default=0)

    # Scoring details (populated after submission)
    is_correct = models.BooleanField(null=True)
    marks_awarded = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    class Meta:
        unique_together = ('attempt', 'question')
