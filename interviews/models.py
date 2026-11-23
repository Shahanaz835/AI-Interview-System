from django.db import models
from django.contrib.auth.models import User
import json

class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    pdf_file = models.FileField(upload_to='resumes/')
    filename = models.CharField(max_length=255)
    raw_text = models.TextField(blank=True, default='')
    
    # Structured extracted sections (stored as JSON)
    education_data = models.JSONField(default=list, blank=True)
    experience_data = models.JSONField(default=list, blank=True)
    projects_data = models.JSONField(default=list, blank=True)
    certifications_data = models.JSONField(default=list, blank=True)
    missing_sections = models.JSONField(default=list, blank=True)
    
    overall_score = models.IntegerField(default=75, help_text="Resume completeness score out of 100")
    analysis_summary = models.TextField(blank=True, default='')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.user.username} - {self.filename} ({self.uploaded_at.strftime('%Y-%m-%d')})"


class ExtractedSkill(models.Model):
    CATEGORY_CHOICES = [
        ('Language', 'Programming Language'),
        ('Framework', 'Framework / Library'),
        ('Database', 'Database / Storage'),
        ('Tool', 'Tool / Platform / Cloud'),
        ('Concept', 'Core CS Concept'),
    ]

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Language')
    proficiency = models.CharField(max_length=50, default='Intermediate')

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.category})"


class InterviewSession(models.Model):
    CATEGORY_CHOICES = [
        ('technical', 'Technical Interview'),
        ('hr', 'HR Behavioral Interview'),
        ('aptitude', 'Aptitude & Reasoning Interview'),
    ]

    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner / Entry Level'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('adaptive', 'Adaptive (AI Adjusts Dynamically)'),
    ]

    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interview_sessions')
    resume = models.ForeignKey(Resume, on_delete=models.SET_NULL, null=True, blank=True, related_name='interviews')
    
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='technical')
    subject = models.CharField(max_length=100, default='Python & General CSE', help_text="E.g., Python, Java, DSA, DBMS, Web Development")
    difficulty = models.CharField(max_length=30, choices=DIFFICULTY_CHOICES, default='adaptive')
    
    target_questions_count = models.IntegerField(default=5)
    duration_minutes = models.IntegerField(default=15)
    current_question_index = models.IntegerField(default=0)
    
    final_score = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    
    overall_feedback = models.TextField(blank=True, default='')
    strengths_summary = models.TextField(blank=True, default='')
    weaknesses_summary = models.TextField(blank=True, default='')
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_category_display()} ({self.subject}) - Score: {self.final_score or 'N/A'}"


class InterviewQuestion(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name='questions')
    question_number = models.IntegerField(default=1)
    question_text = models.TextField()
    category = models.CharField(max_length=50, default='General')
    difficulty = models.CharField(max_length=30, default='intermediate')
    ideal_answer_summary = models.TextField(blank=True, default='')
    is_follow_up = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['question_number']

    def __str__(self):
        return f"Q{self.question_number}: {self.question_text[:60]}..."


class CandidateAnswer(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name='answers')
    question = models.OneToOneField(InterviewQuestion, on_delete=models.CASCADE, related_name='candidate_answer')
    recognized_text = models.TextField(help_text="Transcript captured via Web Speech API or typed fallback")
    time_taken_seconds = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer to Q{self.question.question_number} by {self.session.user.username}"


class AnswerEvaluation(models.Model):
    answer = models.OneToOneField(CandidateAnswer, on_delete=models.CASCADE, related_name='evaluation')
    score = models.FloatField(default=0.0, help_text="Score out of 10")
    technical_correctness = models.CharField(max_length=50, default='Moderate')
    relevance = models.CharField(max_length=50, default='Moderate')
    completeness = models.CharField(max_length=50, default='Moderate')
    clarity = models.CharField(max_length=50, default='Moderate')
    
    positive_points = models.JSONField(default=list, blank=True)
    missing_concepts = models.JSONField(default=list, blank=True)
    mistakes = models.JSONField(default=list, blank=True)
    
    correct_explanation = models.TextField(blank=True, default='')
    improved_answer = models.TextField(blank=True, default='')
    spoken_feedback = models.TextField(blank=True, default='', help_text="Short conversational feedback spoken by AI TTS")
    
    follow_up_question_text = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evaluation for Q{self.answer.question.question_number}: {self.score}/10"


class LearningRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_roadmaps')
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name='roadmaps', null=True, blank=True)
    subject = models.CharField(max_length=100)
    weak_areas = models.JSONField(default=list, blank=True)
    recommended_topics = models.JSONField(default=list, blank=True)
    practice_questions = models.JSONField(default=list, blank=True)
    action_plan = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Roadmap for {self.user.username} - {self.subject}"
