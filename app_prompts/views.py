from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Prompt
from .serializers import PromptSerializer


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

    def perform_create(self, serializer):
        """Save the prompt with the authenticated user."""
        serializer.save(user=self.request.user)
