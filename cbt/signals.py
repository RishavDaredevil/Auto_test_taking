from django.db.models.signals import post_save
from django.dispatch import receiver
from .parse_answer_key import process_answer_key
from .models import Exam

@receiver(post_save, sender=Exam)
def exam_post_save(sender, instance, created, **kwargs):
    if created and instance.answer_key_file:
        process_answer_key(instance)
