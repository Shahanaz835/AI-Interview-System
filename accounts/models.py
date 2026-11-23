from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    EXPERIENCE_CHOICES = [
        ('Fresher', 'Fresher / Student (0 years)'),
        ('Junior', 'Junior Developer (1-2 years)'),
        ('Mid-Level', 'Mid-Level Developer (3-5 years)'),
        ('Senior', 'Senior Developer (5+ years)'),
    ]

    TARGET_ROLE_CHOICES = [
        ('Software Engineer', 'Software Engineer / Developer'),
        ('Full Stack Developer', 'Full Stack Developer'),
        ('Frontend Developer', 'Frontend Developer'),
        ('Backend Developer', 'Backend Developer'),
        ('Python Developer', 'Python Developer'),
        ('Java Developer', 'Java Developer'),
        ('Data Scientist / AI Engineer', 'Data Scientist / AI Engineer'),
        ('DevOps Engineer', 'DevOps / Cloud Engineer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    target_role = models.CharField(max_length=100, choices=TARGET_ROLE_CHOICES, default='Software Engineer')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='Fresher')
    bio = models.TextField(max_length=500, blank=True, null=True, help_text="Brief summary of your background and goals.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile - {self.target_role} ({self.experience_level})"


# Signals to automatically create & save UserProfile whenever a User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
