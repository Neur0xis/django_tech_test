from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Prompt


class JWTAuthenticationTests(APITestCase):
    """Tests for JWT authentication."""

    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()

    def test_login_returns_tokens(self):
        """Test that login endpoint returns access and refresh tokens."""
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_with_invalid_credentials(self):
        """Test that login fails with invalid credentials."""
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PromptEndpointTests(APITestCase):
    """Tests for protected prompt endpoints."""

    def setUp(self):
        """Create test users and prompts."""
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='pass123'
        )
        self.client = APIClient()

        # Create prompts for user1
        self.prompt1 = Prompt.objects.create(
            user=self.user1,
            prompt_text='Test prompt 1',
            response_text='Test response 1'
        )
        self.prompt2 = Prompt.objects.create(
            user=self.user1,
            prompt_text='Test prompt 2',
            response_text='Test response 2'
        )

    def get_auth_token(self, username, password):
        """Helper method to get JWT token."""
        response = self.client.post('/login/', {
            'username': username,
            'password': password
        })
        return response.data['access']

    def test_unauthenticated_list_prompts_returns_401(self):
        """Test that listing prompts without auth returns 401."""
        response = self.client.get('/prompts/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_create_prompt_returns_401(self):
        """Test that creating prompt without auth returns 401."""
        response = self.client.post('/prompts/', {
            'prompt_text': 'New prompt',
            'response_text': 'New response'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_retrieve_prompt_returns_401(self):
        """Test that retrieving prompt without auth returns 401."""
        response = self.client.get(f'/prompts/{self.prompt1.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_list_prompts(self):
        """Test that authenticated user can list their prompts."""
        token = self.get_auth_token('user1', 'pass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/prompts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_authenticated_create_prompt(self):
        """Test that authenticated user can create prompts."""
        token = self.get_auth_token('user1', 'pass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.post('/prompts/', {
            'prompt_text': 'New prompt',
            'response_text': 'New response'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['prompt_text'], 'New prompt')
        self.assertEqual(response.data['user'], 'user1')

    def test_authenticated_retrieve_prompt(self):
        """Test that authenticated user can retrieve their prompt."""
        token = self.get_auth_token('user1', 'pass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(f'/prompts/{self.prompt1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['prompt_text'], 'Test prompt 1')

    def test_user_cannot_access_other_user_prompts(self):
        """Test that users can only see their own prompts."""
        token = self.get_auth_token('user2', 'pass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # User2 should not see user1's prompts
        response = self.client.get('/prompts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        # User2 should not be able to retrieve user1's prompt
        response = self.client.get(f'/prompts/{self.prompt1.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_jwt_authentication_with_bearer_token(self):
        """Test that JWT authentication works with Bearer token format."""
        token = self.get_auth_token('user1', 'pass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/prompts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
