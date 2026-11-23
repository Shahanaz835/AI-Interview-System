from django.contrib import admin
from .models import (
    Resume, ExtractedSkill, InterviewSession, InterviewQuestion,
    CandidateAnswer, AnswerEvaluation, LearningRecommendation
)

class ExtractedSkillInline(admin.TabularInline):
    model = ExtractedSkill
    extra = 0

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('user', 'filename', 'overall_score', 'uploaded_at')
    inlines = [ExtractedSkillInline]

class InterviewQuestionInline(admin.TabularInline):
    model = InterviewQuestion
    extra = 0

@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'subject', 'difficulty', 'final_score', 'status', 'created_at')
    list_filter = ('category', 'difficulty', 'status')
    inlines = [InterviewQuestionInline]

@admin.register(AnswerEvaluation)
class AnswerEvaluationAdmin(admin.ModelAdmin):
    list_display = ('answer', 'score', 'technical_correctness', 'relevance', 'created_at')

admin.site.register(CandidateAnswer)
admin.site.register(LearningRecommendation)
