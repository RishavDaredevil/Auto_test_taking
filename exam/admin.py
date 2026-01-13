from django.contrib import admin
from .models import Exam, Section, QuestionMeta, Attempt, Response

class SectionInline(admin.TabularInline):
    model = Section
    extra = 0

class QuestionMetaInline(admin.TabularInline):
    model = QuestionMeta
    extra = 0
    fields = ('question_number', 'question_type', 'correct_answer', 'marks_positive', 'marks_negative')
    readonly_fields = ('question_number', 'question_type', 'correct_answer')
    can_delete = False
    max_num = 0

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'duration_minutes', 'total_marks', 'is_active')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [SectionInline, QuestionMetaInline]

@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'exam', 'started_at', 'is_submitted', 'total_score')
    list_filter = ('is_submitted', 'exam')

admin.site.register(QuestionMeta)
admin.site.register(Response)
