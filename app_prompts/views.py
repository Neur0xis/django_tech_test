import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Prompt
from .serializers import PromptSerializer, PromptCreateSerializer, SimilarPromptSerializer
from . import services

logger = logging.getLogger(__name__)


class PromptThrottle(UserRateThrottle):
    """Custom throttle for prompt creation: 1 request per second."""
    scope = 'prompt'


class PromptViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user prompts.
    All endpoints require authentication.
    """
    serializer_class = PromptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return prompts for the authenticated user only."""
        return Prompt.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return PromptCreateSerializer
        return PromptSerializer

    def get_throttles(self):
        """Apply custom throttle only for create action."""
        if self.action == 'create':
            return [PromptThrottle()]
        return super().get_throttles()

    def create(self, request, *args, **kwargs):
        """
        Create a new prompt with auto-generated response and embedding.
        Accepts: prompt_text (required), websocket (optional, default False)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        prompt_text = serializer.validated_data['prompt_text']
        websocket = serializer.validated_data.get('websocket', False)

        # Generate response using service layer
        response_text = services.generate_response(prompt_text)

        # Compute embedding
        embedding = services.get_embedding(prompt_text)

        # Save to database
        prompt = Prompt.objects.create(
            user=request.user,
            prompt_text=prompt_text,
            response_text=response_text,
            embedding=embedding
        )

        # Add to FAISS index
        services.add_to_index(prompt.id, embedding)

        # Log the creation
        logger.info(f"Created prompt ID={prompt.id} for user={request.user.username}")

        # Prepare response data
        response_serializer = PromptSerializer(prompt)
        response_data = response_serializer.data

        # Send via WebSocket if requested
        if websocket:
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"user_{request.user.username}",
                    {
                        "type": "send_prompt_response",
                        "data": response_data,
                    },
                )
                logger.info(f"Sent prompt ID={prompt.id} via WebSocket to user={request.user.username}")
            except Exception as e:
                logger.error(f"Failed to send WebSocket message for prompt ID={prompt.id}: {e}")

        # Return the created prompt
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='similar')
    def similar(self, request):
        """
        Find similar prompts based on semantic similarity.
        Query parameter: prompt (required)
        Returns: List of similar prompts with similarity scores
        """
        prompt_query = request.query_params.get('prompt', None)

        if not prompt_query:
            return Response(
                {'error': 'Query parameter "prompt" is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not prompt_query.strip():
            return Response(
                {'error': 'Query parameter "prompt" cannot be empty.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Compute embedding for the query
        query_embedding = services.get_embedding(prompt_query)

        # Find similar prompts (returns list of (prompt_id, distance) tuples)
        similar_results = services.find_similar(query_embedding, top_k=5)

        if not similar_results:
            logger.info(f"Similarity search by user={request.user.username}, found 0 results")
            return Response([], status=status.HTTP_200_OK)

        # Fetch prompt objects and filter by user's access
        prompt_ids = [prompt_id for prompt_id, _ in similar_results]
        prompts = Prompt.objects.filter(
            id__in=prompt_ids,
            user=request.user  # Only return user's own prompts
        )

        # Create a mapping of prompt_id to distance
        distance_map = {prompt_id: distance for prompt_id, distance in similar_results}

        # Add similarity scores to prompts
        prompts_with_scores = []
        for prompt in prompts:
            prompt.similarity_score = distance_map.get(prompt.id, 0.0)
            prompts_with_scores.append(prompt)

        # Sort by similarity (lower distance = more similar)
        prompts_with_scores.sort(key=lambda p: p.similarity_score)

        # Serialize and return
        serializer = SimilarPromptSerializer(prompts_with_scores, many=True)
        
        logger.info(f"Similarity search by user={request.user.username}, found {len(prompts_with_scores)} results")
        
        return Response(serializer.data, status=status.HTTP_200_OK)
