from django.test import TestCase, Client
from django.contrib.auth.models import User
from accounts.models import UserProfile

class AccountsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testcandidate',
            email='candidate@example.com',
            password='TestPassword123!',
            first_name='John',
            last_name='Doe'
        )

    def test_user_profile_signal_creation(self):
        """Verify that UserProfile is automatically created via signals."""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertEqual(self.user.profile.target_role, 'Software Engineer')
        self.assertEqual(self.user.profile.experience_level, 'Fresher')

    def test_landing_page(self):
        """Verify landing page loads for unauthenticated user."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Master Technical, HR & Aptitude Interviews with AI")

    def test_registration_flow(self):
        """Verify new user registration and redirection to dashboard."""
        response = self.client.post('/register/', {
            'username': 'newcoder',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane@example.com',
            'target_role': 'Python Developer',
            'experience_level': 'Junior',
            'password1': 'SecurePassword123!',
            'password2': 'SecurePassword123!'
        })
        self.assertEqual(response.status_code, 302)  # Redirects to dashboard
        user = User.objects.get(username='newcoder')
        self.assertEqual(user.profile.target_role, 'Python Developer')
        self.assertEqual(user.profile.experience_level, 'Junior')

    def test_login_flow(self):
        """Verify authentication and dashboard access."""
        response = self.client.post('/login/', {
            'username': 'testcandidate',
            'password': 'TestPassword123!'
        })
        self.assertEqual(response.status_code, 302)
        
        # Follow to dashboard
        dash_response = self.client.get('/dashboard/')
        self.assertEqual(dash_response.status_code, 200)
        self.assertContains(dash_response, "Welcome, John!")
