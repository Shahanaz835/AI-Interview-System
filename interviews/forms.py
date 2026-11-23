from django import forms
from .models import Resume, InterviewSession

class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['pdf_file']
        widgets = {
            'pdf_file': forms.FileInput(attrs={
                'class': 'form-control form-control-lg',
                'accept': '.pdf',
                'id': 'resumeFileInput'
            })
        }

    def clean_pdf_file(self):
        uploaded_file = self.cleaned_data.get('pdf_file')
        if not uploaded_file:
            raise forms.ValidationError("Please select a PDF file to upload.")

        # Check extension
        if not uploaded_file.name.lower().endswith('.pdf'):
            raise forms.ValidationError("Only PDF files (.pdf) are supported.")

        # Check file size (max 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            raise forms.ValidationError("File size must not exceed 10 MB.")

        return uploaded_file


class InterviewSetupForm(forms.ModelForm):
    SUBJECT_CHOICES = [
        # Technical
        ('Python & Backend Development', 'Python & Backend Development'),
        ('Java & Enterprise Systems', 'Java & Enterprise Systems'),
        ('Data Structures & Algorithms (DSA)', 'Data Structures & Algorithms (DSA)'),
        ('DBMS & SQL Databases', 'DBMS & SQL Databases'),
        ('C & C++ Programming', 'C & C++ Programming'),
        ('Web Development (HTML/CSS/JS/React)', 'Web Development (HTML/CSS/JS/React)'),
        ('Operating Systems & Networks', 'Operating Systems & Networks'),
        ('Object Oriented Programming (OOP)', 'Object Oriented Programming (OOP)'),
        # HR
        ('HR Behavioral & STAR Interview', 'HR Behavioral & STAR Interview'),
        ('Leadership & Conflict Management', 'Leadership & Conflict Management'),
        # Aptitude
        ('Quantitative Aptitude', 'Quantitative Aptitude'),
        ('Logical & Analytical Reasoning', 'Logical & Analytical Reasoning'),
    ]

    subject = forms.ChoiceField(
        choices=SUBJECT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'subjectSelect'})
    )

    class Meta:
        model = InterviewSession
        fields = ['category', 'subject', 'difficulty', 'target_questions_count', 'duration_minutes']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'categorySelect'}),
            'difficulty': forms.Select(attrs={'class': 'form-select', 'id': 'difficultySelect'}),
            'target_questions_count': forms.Select(
                choices=[(3, '3 Questions (Quick Test)'), (5, '5 Questions (Standard Practice)'), (8, '8 Questions (Comprehensive)'), (10, '10 Questions (Full Mock)')],
                attrs={'class': 'form-select'}
            ),
            'duration_minutes': forms.Select(
                choices=[(10, '10 Minutes'), (15, '15 Minutes'), (20, '20 Minutes'), (30, '30 Minutes')],
                attrs={'class': 'form-select'}
            ),
        }
