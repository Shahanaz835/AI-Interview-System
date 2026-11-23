from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Candidate Profile'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_target_role', 'get_experience', 'is_staff')

    def get_target_role(self, instance):
        return instance.profile.target_role if hasattr(instance, 'profile') else '-'
    get_target_role.short_description = 'Target Role'

    def get_experience(self, instance):
        return instance.profile.experience_level if hasattr(instance, 'profile') else '-'
    get_experience.short_description = 'Experience Level'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile)
