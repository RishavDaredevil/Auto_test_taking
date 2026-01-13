from django import forms
from .models import Exam

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['title', 'slug', 'description', 'duration_minutes', 'total_marks', 'question_paper', 'answer_key_file']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'duration_minutes': forms.NumberInput(attrs={'min': 1}),
        }
