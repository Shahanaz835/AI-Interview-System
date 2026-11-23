from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import (
    CandidateRegistrationForm, 
    CandidateLoginForm, 
    UserUpdateForm, 
    UserProfileUpdateForm
)

def landing_view(request):
    """Public home/landing page introducing the AI Interviewer platform."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/landing.html')


def register_view(request):
    """Handles new candidate account creation."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CandidateRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to AI Interviewer, {user.first_name}! Your account has been created.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below to register.")
    else:
        form = CandidateRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Handles candidate authentication."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CandidateLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next')
            return redirect(next_url if next_url else 'dashboard')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = CandidateLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Logs out the candidate and redirects to the login page."""
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('login')


@login_required
def dashboard_view(request):
    """
    Main candidate portal.
    Displays user profile status, resume readiness, and quick-start interview options.
    """
    profile = getattr(request.user, 'profile', None)
    
    # We will hook these into the interviews app models in subsequent phases
    context = {
        'profile': profile,
        'total_interviews': 0,
        'avg_score': 0,
        'has_resume': False,
        'recent_interviews': [],
    }
    
    # Check if a resume model exists and has been uploaded for this user
    try:
        from interviews.models import Resume, InterviewSession
        resume = Resume.objects.filter(user=request.user).first()
        if resume:
            context['has_resume'] = True
            context['resume'] = resume
            
        sessions = InterviewSession.objects.filter(user=request.user).order_by('-created_at')
        context['total_interviews'] = sessions.count()
        context['recent_interviews'] = sessions[:5]
        
        # Calculate average score if sessions exist
        completed_sessions = [s for s in sessions if s.final_score is not None]
        if completed_sessions:
            context['avg_score'] = round(sum(s.final_score for s in completed_sessions) / len(completed_sessions), 1)
    except Exception:
        # Before interviews models are migrated, keep safe defaults
        pass

    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    """Allows candidates to view and update their profile details."""
    user = request.user
    profile = getattr(user, 'profile', None)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileUpdateForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('profile')
        else:
            messages.error(request, "Please check the form for errors.")
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileUpdateForm(instance=profile)

    return render(request, 'accounts/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
    })
