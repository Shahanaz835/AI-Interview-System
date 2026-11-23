import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from interviews.models import (
    Resume, ExtractedSkill, InterviewSession, InterviewQuestion,
    CandidateAnswer, AnswerEvaluation, LearningRecommendation
)
from interviews.resume_parser import extract_skills_from_text, extract_sections, calculate_resume_score
from interviews.groq_service import get_fallback_questions, get_fallback_evaluation

class InterviewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='interviewee',
            email='interviewee@example.com',
            password='TestPassword123!',
            first_name='Alex'
        )
        self.client.login(username='interviewee', password='TestPassword123!')

    def test_resume_parser_heuristics(self):
        sample_text = """
        John Doe
        Skills: Python, Java, SQL, Django, React, MongoDB
        Projects: Built an Online Banking Portal with secure auth and payment gateway.
        Education: B.Tech in Computer Science and Engineering, CGPA 8.5
        Certifications: AWS Certified Solutions Architect
        """
        skills = extract_skills_from_text(sample_text)
        skill_names = [s['name'] for s in skills]
        self.assertIn('Python', skill_names)
        self.assertIn('Java', skill_names)
        self.assertIn('SQL', skill_names)
        self.assertIn('Django', skill_names)

        sections = extract_sections(sample_text)
        self.assertTrue(len(sections['projects']) > 0)
        self.assertTrue(len(sections['education']) > 0)

        score, summary = calculate_resume_score(skills, sections)
        self.assertTrue(score >= 70)

    def test_fallback_question_generation(self):
        questions = get_fallback_questions('technical', 'Python & General CSE', 'intermediate', 5)
        self.assertEqual(len(questions), 5)
        self.assertEqual(questions[0]['question_number'], 1)
        self.assertIn('question_text', questions[0])
        self.assertIn('ideal_answer_summary', questions[0])

    def test_fallback_evaluation_engine(self):
        # Short answer
        eval_short = get_fallback_evaluation("What is polymorphism?", "It means many forms.")
        self.assertLessEqual(eval_short['score'], 5.0)
        self.assertIn('spoken_feedback', eval_short)

        # Detailed answer
        eval_long = get_fallback_evaluation(
            "What is polymorphism?",
            "Polymorphism allows objects of different classes to be treated through a common interface. In Java and Python, it includes compile-time polymorphism like method overloading and runtime polymorphism like method overriding using dynamic method dispatch."
        )
        self.assertGreaterEqual(eval_long['score'], 7.0)
        self.assertIn('spoken_feedback', eval_long)
        self.assertIn('improved_answer', eval_long)

    def test_interview_full_flow(self):
        # 1. Setup interview
        session = InterviewSession.objects.create(
            user=self.user,
            category='technical',
            subject='Python & Backend Development',
            difficulty='adaptive',
            target_questions_count=2
        )
        q1 = InterviewQuestion.objects.create(
            session=session,
            question_number=1,
            question_text="Explain Python list comprehensions.",
            difficulty='intermediate'
        )
        q2 = InterviewQuestion.objects.create(
            session=session,
            question_number=2,
            question_text="How do generators work in Python?",
            difficulty='intermediate'
        )

        # 2. Access room view
        room_response = self.client.get(f'/interviews/room/{session.id}/')
        self.assertEqual(room_response.status_code, 200)
        self.assertContains(room_response, "Explain Python list comprehensions.")

        # 3. Submit Answer 1 via API
        api_res1 = self.client.post('/interviews/api/submit-answer/', data=json.dumps({
            'session_id': session.id,
            'question_id': q1.id,
            'recognized_text': 'List comprehensions provide a concise way to create lists using expressions inside brackets.',
            'time_taken': 15
        }), content_type='application/json')
        self.assertEqual(api_res1.status_code, 200)
        data1 = api_res1.json()
        self.assertEqual(data1['status'], 'success')
        self.assertFalse(data1['is_finished'])
        self.assertIsNotNone(data1['spoken_feedback'])

        # 4. Submit Answer 2 via API (Completes Session)
        api_res2 = self.client.post('/interviews/api/submit-answer/', data=json.dumps({
            'session_id': session.id,
            'question_id': q2.id,
            'recognized_text': 'Generators yield values one at a time using the yield keyword without loading the entire collection into memory.',
            'time_taken': 20
        }), content_type='application/json')
        self.assertEqual(api_res2.status_code, 200)
        data2 = api_res2.json()
        self.assertEqual(data2['status'], 'success')
        self.assertTrue(data2['is_finished'])
        self.assertIn(f'/interviews/result/{session.id}/', data2['redirect_url'])

        # Refresh session
        session.refresh_from_db()
        self.assertEqual(session.status, 'completed')
        self.assertIsNotNone(session.final_score)

        # 5. Access Results View
        result_response = self.client.get(f'/interviews/result/{session.id}/')
        self.assertEqual(result_response.status_code, 200)
        self.assertContains(result_response, "Interview Performance Report")

        # 6. Access History View
        hist_response = self.client.get('/interviews/history/')
        self.assertEqual(hist_response.status_code, 200)
        self.assertContains(hist_response, "Python &amp; Backend Development")

        # 7. Access Analytics Performance Dashboard
        perf_response = self.client.get('/interviews/performance/')
        self.assertEqual(perf_response.status_code, 200)
        self.assertContains(perf_response, "Performance Analytics")

        # 8. Access Learning Roadmap
        roadmap_response = self.client.get('/interviews/roadmap/')
        self.assertEqual(roadmap_response.status_code, 200)
        self.assertContains(roadmap_response, "Personalized Learning Roadmap")
