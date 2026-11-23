from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile

class CandidateRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=50, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=50, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    target_role = forms.ChoiceField(
        choices=UserProfile.TARGET_ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    experience_level = forms.ChoiceField(
        choices=UserProfile.EXPERIENCE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'target_role', 'experience_level']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})
        self.fields['username'].help_text = "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            # UserProfile is auto-created by signal, let's update profile fields
            profile = user.profile
            profile.target_role = self.cleaned_data.get('target_role')
            profile.experience_level = self.cleaned_data.get('experience_level')
            profile.save()
        return user


class CandidateLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password'
        })


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['target_role', 'experience_level', 'phone_number', 'bio']
        widgets = {
            'target_role': forms.Select(attrs={'class': 'form-select'}),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 9876543210'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tell us about your technical journey...'}),
        }
