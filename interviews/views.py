import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Count

from .models import (
    Resume, ExtractedSkill, InterviewSession, InterviewQuestion,
    CandidateAnswer, AnswerEvaluation, LearningRecommendation
)
from .forms import ResumeUploadForm, InterviewSetupForm
from .resume_parser import parse_resume
from .groq_service import (
    generate_interview_questions,
    evaluate_candidate_answer,
    generate_learning_roadmap_ai
)


@login_required
def resume_upload_view(request):
    """Handles resume PDF upload, PyPDF text extraction, and skill extraction."""
    existing_resume = Resume.objects.filter(user=request.user).first()

    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user
            resume.filename = request.FILES['pdf_file'].name
            resume.save()

            # Parse PDF using PyPDF and NLP extractor
            parsed = parse_resume(resume.pdf_file.path)
            resume.raw_text = parsed['raw_text']
            resume.education_data = parsed['education']
            resume.experience_data = parsed['experience']
            resume.projects_data = parsed['projects']
            resume.certifications_data = parsed['certifications']
            resume.missing_sections = parsed['missing_sections']
            resume.overall_score = parsed['score']
            resume.analysis_summary = parsed['summary']
            resume.save()

            # Delete old skills and save freshly extracted skills
            resume.skills.all().delete()
            for skill_item in parsed['skills']:
                ExtractedSkill.objects.create(
                    resume=resume,
                    name=skill_item['name'],
                    category=skill_item['category'],
                    proficiency=skill_item.get('proficiency', 'Intermediate')
                )

            messages.success(request, f"Resume '{resume.filename}' parsed successfully! Found {len(parsed['skills'])} skills.")
            return redirect('resume_detail', resume_id=resume.id)
    else:
        form = ResumeUploadForm()

    return render(request, 'interviews/resume_upload.html', {
        'form': form,
        'existing_resume': existing_resume
    })


@login_required
def resume_detail_view(request, resume_id):
    """Displays in-depth resume analysis report and technical skills breakdown."""
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    skills = resume.skills.all()

    # Group skills by category for display
    skills_by_category = {}
    for skill in skills:
        skills_by_category.setdefault(skill.get_category_display(), []).append(skill.name)

    return render(request, 'interviews/resume_detail.html', {
        'resume': resume,
        'skills_by_category': skills_by_category,
        'total_skills_count': skills.count()
    })


@login_required
def interview_setup_view(request):
    """Configures interview parameters (Category, Topic, Difficulty, Question count)."""
    resume = Resume.objects.filter(user=request.user).first()
    category_param = request.GET.get('category', 'technical')

    if request.method == 'POST':
        form = InterviewSetupForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            if resume:
                session.resume = resume
            session.save()

            # Prepare resume data for AI question grounding
            resume_data = None
            if resume:
                resume_data = {
                    'skills': list(resume.skills.values_list('name', flat=True)),
                    'projects': resume.projects_data
                }

            # Generate questions via Groq LLM
            generated_questions = generate_interview_questions(
                category=session.category,
                subject=session.subject,
                difficulty=session.difficulty,
                num_questions=session.target_questions_count,
                resume_data=resume_data
            )

            # Store questions in database
            for q_data in generated_questions:
                InterviewQuestion.objects.create(
                    session=session,
                    question_number=q_data.get('question_number', 1),
                    question_text=q_data.get('question_text', ''),
                    category=q_data.get('category', session.category),
                    difficulty=q_data.get('difficulty', session.difficulty),
                    ideal_answer_summary=q_data.get('ideal_answer_summary', '')
                )

            return redirect('interview_room', session_id=session.id)
    else:
        initial_data = {'category': category_param}
        if category_param == 'hr':
            initial_data['subject'] = 'HR Behavioral & STAR Interview'
        elif category_param == 'aptitude':
            initial_data['subject'] = 'Quantitative Aptitude'
        form = InterviewSetupForm(initial=initial_data)

    return render(request, 'interviews/interview_setup.html', {
        'form': form,
        'resume': resume
    })


@login_required
def interview_room_view(request, session_id):
    """Live voice interview room where AI and candidate interact in real-time."""
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)

    if session.status == 'completed':
        return redirect('interview_result', session_id=session.id)

    questions = list(session.questions.all().order_by('question_number'))
    if not questions:
        messages.error(request, "No questions found for this interview session.")
        return redirect('interview_setup')

    # Find the current unanswered question
    current_question = None
    for q in questions:
        if not hasattr(q, 'candidate_answer'):
            current_question = q
            break

    if not current_question:
        # All questions answered, wrap up session
        return redirect('interview_result', session_id=session.id)

    total_questions = len(questions)
    current_index = current_question.question_number
    progress_percentage = int(((current_index - 1) / total_questions) * 100)

    return render(request, 'interviews/interview_room.html', {
        'session': session,
        'current_question': current_question,
        'total_questions': total_questions,
        'progress_percentage': progress_percentage
    })


@login_required
@require_POST
def api_submit_answer(request):
    """
    API endpoint: receives candidate's voice transcript, evaluates via Groq,
    and returns evaluation scores + conversational voice feedback for the browser to speak.
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        question_id = data.get('question_id')
        recognized_text = data.get('recognized_text', '').strip()
        time_taken = int(data.get('time_taken', 0))

        session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
        question = get_object_or_404(InterviewQuestion, id=question_id, session=session)

        # Save candidate answer
        answer, _ = CandidateAnswer.objects.update_or_create(
            question=question,
            session=session,
            defaults={
                'recognized_text': recognized_text or "(No answer provided)",
                'time_taken_seconds': time_taken
            }
        )

        # Gather context of previous Q&A for dynamic follow-ups
        previous_answers = []
        for prev_q in session.questions.filter(question_number__lt=question.question_number):
            if hasattr(prev_q, 'candidate_answer'):
                previous_answers.append({
                    'question': prev_q.question_text,
                    'answer': prev_q.candidate_answer.recognized_text
                })

        # Evaluate answer via Groq LLM
        eval_result = evaluate_candidate_answer(
            question_text=question.question_text,
            candidate_answer=answer.recognized_text,
            interview_context=previous_answers,
            difficulty=question.difficulty
        )

        # Save evaluation record
        evaluation, _ = AnswerEvaluation.objects.update_or_create(
            answer=answer,
            defaults={
                'score': float(eval_result.get('score', 5.0)),
                'technical_correctness': eval_result.get('technical_correctness', 'Moderate'),
                'relevance': eval_result.get('relevance', 'Moderate'),
                'completeness': eval_result.get('completeness', 'Moderate'),
                'clarity': eval_result.get('clarity', 'Moderate'),
                'positive_points': eval_result.get('positive_points', []),
                'missing_concepts': eval_result.get('missing_concepts', []),
                'mistakes': eval_result.get('mistakes', []),
                'correct_explanation': eval_result.get('correct_explanation', ''),
                'improved_answer': eval_result.get('improved_answer', ''),
                'spoken_feedback': eval_result.get('spoken_feedback', ''),
                'follow_up_question_text': eval_result.get('follow_up_question', '')
            }
        )

        # Check if more questions exist
        next_question = session.questions.filter(question_number__gt=question.question_number).first()

        # If adaptive difficulty and high/low score, inject adaptive follow-up
        if next_question and session.difficulty == 'adaptive' and eval_result.get('follow_up_question'):
            # Adapt the next question text slightly based on the candidate's last performance
            next_question.is_follow_up = True
            next_question.save()

        is_finished = next_question is None

        if is_finished:
            # Wrap up session
            session.status = 'completed'
            session.completed_at = timezone.now()
            all_evals = AnswerEvaluation.objects.filter(answer__session=session)
            if all_evals.exists():
                session.final_score = round(all_evals.aggregate(Avg('score'))['score__avg'], 1)
            else:
                session.final_score = 0.0

            # Generate Learning Recommendation
            user_profile = getattr(request.user, 'profile', None)
            if user_profile:
                roadmap_data = generate_learning_roadmap_ai(user_profile, session, all_evals)
                LearningRecommendation.objects.create(
                    user=request.user,
                    session=session,
                    subject=session.subject,
                    weak_areas=roadmap_data.get('weak_areas', []),
                    recommended_topics=roadmap_data.get('recommended_topics', []),
                    practice_questions=roadmap_data.get('practice_questions', []),
                    action_plan=roadmap_data.get('action_plan', '')
                )

            session.save()

        return JsonResponse({
            'status': 'success',
            'score': evaluation.score,
            'spoken_feedback': evaluation.spoken_feedback,
            'positive_points': evaluation.positive_points,
            'missing_concepts': evaluation.missing_concepts,
            'mistakes': evaluation.mistakes,
            'improved_answer': evaluation.improved_answer,
            'is_finished': is_finished,
            'next_question': {
                'id': next_question.id,
                'number': next_question.question_number,
                'text': next_question.question_text
            } if next_question else None,
            'redirect_url': f"/interviews/result/{session.id}/" if is_finished else None
        })

    except Exception as e:
        print(f"Error in api_submit_answer: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def api_end_interview(request):
    """Allows candidates to terminate the interview early and calculate final score."""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        session = get_object_or_404(InterviewSession, id=session_id, user=request.user)

        session.status = 'completed'
        session.completed_at = timezone.now()
        all_evals = AnswerEvaluation.objects.filter(answer__session=session)
        if all_evals.exists():
            session.final_score = round(all_evals.aggregate(Avg('score'))['score__avg'], 1)
        else:
            session.final_score = 0.0
        session.save()

        return JsonResponse({'status': 'success', 'redirect_url': f"/interviews/result/{session.id}/"})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def interview_result_view(request, session_id):
    """Detailed performance report showing question breakdown, scores, and feedback."""
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    questions = session.questions.all().order_by('question_number')
    roadmap = LearningRecommendation.objects.filter(session=session).first()

    return render(request, 'interviews/interview_result.html', {
        'session': session,
        'questions': questions,
        'roadmap': roadmap
    })


@login_required
def interview_history_view(request):
    """Displays chronological history of all mock interviews taken by the candidate."""
    category_filter = request.GET.get('category', '')
    sessions = InterviewSession.objects.filter(user=request.user).order_by('-created_at')

    if category_filter:
        sessions = sessions.filter(category=category_filter)

    return render(request, 'interviews/interview_history.html', {
        'sessions': sessions,
        'selected_category': category_filter
    })


@login_required
def performance_dashboard_view(request):
    """Chart.js analytics showing candidate performance trends, categories, and strengths."""
    user = request.user
    sessions = InterviewSession.objects.filter(user=user, status='completed').order_by('created_at')

    total_interviews = sessions.count()
    overall_avg = round(sessions.aggregate(Avg('final_score'))['final_score__avg'] or 0.0, 1)

    # Category breakdowns
    tech_sessions = sessions.filter(category='technical')
    tech_avg = round(tech_sessions.aggregate(Avg('final_score'))['final_score__avg'] or 0.0, 1)

    hr_sessions = sessions.filter(category='hr')
    hr_avg = round(hr_sessions.aggregate(Avg('final_score'))['final_score__avg'] or 0.0, 1)

    apt_sessions = sessions.filter(category='aptitude')
    apt_avg = round(apt_sessions.aggregate(Avg('final_score'))['final_score__avg'] or 0.0, 1)

    # Subject performance
    subjects = list(sessions.values('subject').annotate(avg_score=Avg('final_score'), count=Count('id')).order_by('-avg_score'))
    strongest_subject = subjects[0]['subject'] if subjects else "None yet"
    weakest_subject = subjects[-1]['subject'] if len(subjects) > 1 else "None yet"

    # Data for Chart.js
    timeline_labels = [s.created_at.strftime('%d %b') for s in sessions]
    timeline_scores = [s.final_score or 0 for s in sessions]

    return render(request, 'interviews/performance_dashboard.html', {
        'total_interviews': total_interviews,
        'overall_avg': overall_avg,
        'tech_avg': tech_avg,
        'hr_avg': hr_avg,
        'apt_avg': apt_avg,
        'strongest_subject': strongest_subject,
        'weakest_subject': weakest_subject,
        'subjects': subjects,
        'timeline_labels_json': json.dumps(timeline_labels),
        'timeline_scores_json': json.dumps(timeline_scores),
        'category_scores_json': json.dumps([tech_avg, hr_avg, apt_avg]),
    })


@login_required
def learning_roadmap_view(request):
    """Personalized learning plan with topics, practice questions, and study schedule."""
    roadmaps = LearningRecommendation.objects.filter(user=request.user).order_by('-created_at')
    latest_roadmap = roadmaps.first()

    return render(request, 'interviews/learning_roadmap.html', {
        'roadmaps': roadmaps,
        'latest_roadmap': latest_roadmap
    })
