import time
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from ..models import Prompt
from .. import services


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


class PromptCreationTests(APITestCase):
    """Tests for Phase 3: Auto-generation of responses and embeddings."""

    def setUp(self):
        """Initialize test user and client."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        token = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        }).data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_create_prompt_with_only_prompt_text(self):
        """Test that prompt creation auto-generates response and embedding."""
        response = self.client.post('/prompts/', {
            'prompt_text': 'What is artificial intelligence?'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['prompt_text'], 'What is artificial intelligence?')
        self.assertIn('response_text', response.data)
        self.assertIsNotNone(response.data['response_text'])
        self.assertIn('embedding', response.data)
        self.assertIsNotNone(response.data['embedding'])
        self.assertEqual(len(response.data['embedding']), 384)

    def test_create_prompt_with_websocket_flag(self):
        """Test that websocket flag is accepted (Phase 4 preparation)."""
        response = self.client.post('/prompts/', {
            'prompt_text': 'Hello there',
            'websocket': True
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['prompt_text'], 'Hello there')

    def test_create_prompt_with_empty_text_fails(self):
        """Test that empty prompt text is rejected."""
        response = self.client.post('/prompts/', {
            'prompt_text': ''
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_prompt_with_whitespace_only_fails(self):
        """Test that whitespace-only prompt text is rejected."""
        response = self.client.post('/prompts/', {
            'prompt_text': '   '
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_created_prompt_is_added_to_faiss_index(self):
        """Test that created prompts are automatically indexed."""
        # Initialize index
        services.initialize_index()
        initial_count = services.get_faiss_index().ntotal
        
        response = self.client.post('/prompts/', {
            'prompt_text': 'Test indexing'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_count = services.get_faiss_index().ntotal
        self.assertEqual(new_count, initial_count + 1)

    def test_response_generation_varies_by_content(self):
        """Test that different prompts generate different responses."""
        response1 = self.client.post('/prompts/', {
            'prompt_text': 'Hello world'
        })
        response2 = self.client.post('/prompts/', {
            'prompt_text': 'What is Python?'
        })
        
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(
            response1.data['response_text'],
            response2.data['response_text']
        )


class SimilaritySearchTests(APITestCase):
    """Tests for Phase 3: Semantic similarity search."""

    def setUp(self):
        """Initialize test user, client, and test prompts."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        token = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        }).data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Create test prompts with embeddings
        services.initialize_index()
        
    def test_similar_endpoint_requires_prompt_parameter(self):
        """Test that similar endpoint requires 'prompt' query parameter."""
        response = self.client.get('/prompts/similar/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_similar_endpoint_rejects_empty_prompt(self):
        """Test that similar endpoint rejects empty prompt parameter."""
        response = self.client.get('/prompts/similar/?prompt=')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_similar_endpoint_returns_empty_list_when_no_prompts(self):
        """Test that similar endpoint returns empty list when no prompts exist."""
        response = self.client.get('/prompts/similar/?prompt=test')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_similar_endpoint_finds_related_prompts(self):
        """Test that similar endpoint finds semantically related prompts."""
        # Create multiple prompts
        self.client.post('/prompts/', {'prompt_text': 'What is Python programming?'})
        self.client.post('/prompts/', {'prompt_text': 'How to learn Python?'})
        self.client.post('/prompts/', {'prompt_text': 'Best practices in coding'})
        
        # Search for similar prompts
        response = self.client.get('/prompts/similar/?prompt=Python programming language')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        
        # Check that results include similarity scores
        for result in response.data:
            self.assertIn('similarity_score', result)
            self.assertIn('prompt_text', result)
            self.assertIn('response_text', result)

    def test_similar_endpoint_returns_top_5_results(self):
        """Test that similar endpoint returns at most 5 results."""
        # Create 10 prompts
        for i in range(10):
            self.client.post('/prompts/', {'prompt_text': f'Test prompt number {i}'})
        
        response = self.client.get('/prompts/similar/?prompt=Test prompt')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data), 5)

    def test_similar_endpoint_only_shows_user_prompts(self):
        """Test that users only see their own prompts in similarity search."""
        # Create prompt for user1
        self.client.post('/prompts/', {'prompt_text': 'User 1 prompt'})
        
        # Create second user and their prompt
        user2 = User.objects.create_user(username='user2', password='pass123')
        token2 = self.client.post('/login/', {
            'username': 'user2',
            'password': 'pass123'
        }).data['access']
        
        client2 = APIClient()
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        
        # User2 searches - should not see user1's prompts
        response = client2.get('/prompts/similar/?prompt=User 1 prompt')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class ThrottlingTests(APITestCase):
    """Tests for Phase 3: API throttling."""

    def setUp(self):
        """Initialize test user and client."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        token = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        }).data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_prompt_creation_throttle_one_per_second(self):
        """Test that prompt creation is throttled to 1 per second."""
        # First request should succeed
        response1 = self.client.post('/prompts/', {
            'prompt_text': 'First prompt'
        })
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Immediate second request should be throttled
        response2 = self.client.post('/prompts/', {
            'prompt_text': 'Second prompt'
        })
        self.assertEqual(response2.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Wait 1 second and retry
        time.sleep(1.1)
        response3 = self.client.post('/prompts/', {
            'prompt_text': 'Third prompt'
        })
        self.assertEqual(response3.status_code, status.HTTP_201_CREATED)

    def test_other_endpoints_not_affected_by_prompt_throttle(self):
        """Test that other endpoints use different throttle settings."""
        # Create a prompt (uses prompt throttle)
        self.client.post('/prompts/', {'prompt_text': 'Test'})
        
        # List prompts (uses user throttle, should still work)
        response = self.client.get('/prompts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

