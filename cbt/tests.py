from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from cbt.models import Exam, Section, QuestionMeta, Attempt, Response
from cbt.scoring_logic import calculate_score
import json

class CBTTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')

        # Create a dummy PDF
        self.pdf_content = b'%PDF-1.4 mock pdf content'
        self.pdf_file = SimpleUploadedFile("test.pdf", self.pdf_content, content_type="application/pdf")

        # Create a dummy CSV key
        self.csv_content = b"""Section, Question No, Type, Key, Marks, Negative
Section A, 1, MCQ, A, 1, 0.33
Section A, 2, MSQ, A;B, 2, 0
Section B, 3, NAT, 5.0:5.2, 2, 0
"""
        self.csv_file = SimpleUploadedFile("key.csv", self.csv_content, content_type="text/csv")

        self.exam = Exam.objects.create(
            title="Test Exam",
            slug="test-exam",
            description="A test exam",
            question_paper=self.pdf_file,
            answer_key_file=self.csv_file,
            duration_minutes=60
        )

        # Manually trigger process_answer_key because signals might not fire reliably in setUp or if key isn't saved yet
        # Actually signals should fire on create. Let's verify.
        # But wait, I set `answer_key_file` in create, so post_save should catch it.
        # However, `process_answer_key` logic opens the file.

    def test_exam_creation_and_parsing(self):
        self.assertEqual(Exam.objects.count(), 1)
        self.assertEqual(Section.objects.count(), 2) # Section A and B
        self.assertEqual(QuestionMeta.objects.count(), 3)

        q1 = QuestionMeta.objects.get(question_number=1)
        self.assertEqual(q1.question_type, 'MCQ')
        self.assertEqual(q1.correct_answer, 'A')

    def test_attempt_flow(self):
        # Start attempt
        response = self.client.post(f'/cbt/exam/{self.exam.slug}/start/')
        self.assertEqual(response.status_code, 302)

        attempt = Attempt.objects.get(user=self.user, exam=self.exam)
        self.assertFalse(attempt.is_submitted)

        # Interact
        url = f'/cbt/attempt/{attempt.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Sync state
        state = {
            'responses': {
                str(QuestionMeta.objects.get(question_number=1).id): {'value': 'A', 'status': 'answered'},
                str(QuestionMeta.objects.get(question_number=2).id): {'value': 'A,B', 'status': 'answered'}, # Matching "A;B" but checking logic
                str(QuestionMeta.objects.get(question_number=3).id): {'value': '5.1', 'status': 'answered'}
            }
        }
        self.client.post(f'{url}sync/', data=state, content_type='application/json')

        # Submit
        self.client.post(f'{url}submit/')

        attempt.refresh_from_db()
        self.assertTrue(attempt.is_submitted)

        # Check scoring
        # Q1: MCQ A == A -> Correct (+1)
        # Q2: MSQ A,B == A;B -> Correct (+2)
        # Q3: NAT 5.1 in 5.0:5.2 -> Correct (+2)
        # Total = 5
        self.assertEqual(attempt.total_score, 5.0)

    def test_scoring_logic_details(self):
        # Create attempt
        attempt = Attempt.objects.create(user=self.user, exam=self.exam)

        q1 = QuestionMeta.objects.get(question_number=1)
        q2 = QuestionMeta.objects.get(question_number=2)
        q3 = QuestionMeta.objects.get(question_number=3)

        # Incorrect MCQ
        Response.objects.create(attempt=attempt, question=q1, user_input='B', status='answered')
        # Partially correct MSQ (Wrong)
        Response.objects.create(attempt=attempt, question=q2, user_input='A', status='answered')
        # Incorrect NAT
        Response.objects.create(attempt=attempt, question=q3, user_input='6.0', status='answered')

        calculate_score(attempt.id)
        attempt.refresh_from_db()

        # Q1: -0.33
        # Q2: 0
        # Q3: 0
        # Total: -0.33
        self.assertAlmostEqual(float(attempt.total_score), -0.33)
