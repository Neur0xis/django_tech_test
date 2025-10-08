from rest_framework import serializers
from .models import Prompt


class PromptSerializer(serializers.ModelSerializer):
    """Serializer for Prompt model - read-only with all fields."""
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Prompt
        fields = ['id', 'user', 'prompt_text', 'response_text', 'embedding', 'created_at']
        read_only_fields = ['id', 'user', 'prompt_text', 'response_text', 'embedding', 'created_at']


class PromptCreateSerializer(serializers.Serializer):
    """Serializer for creating prompts - only accepts prompt_text and optional websocket flag."""
    prompt_text = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="The prompt text to process"
    )
    websocket = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Whether to send response via WebSocket (for Phase 4)"
    )

    def validate_prompt_text(self, value):
        """Ensure prompt text is not empty after stripping."""
        if not value.strip():
            raise serializers.ValidationError("Prompt text cannot be empty.")
        return value


class PromptPublicSerializer(serializers.ModelSerializer):
    """Public serializer for Prompt model - excludes embedding field."""
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Prompt
        exclude = ['embedding']


class SimilarPromptSerializer(serializers.ModelSerializer):
    """Serializer for similar prompts with similarity score."""
    user = serializers.ReadOnlyField(source='user.username')
    similarity_score = serializers.FloatField(read_only=True)

    class Meta:
        model = Prompt
        fields = ['id', 'user', 'prompt_text', 'response_text', 'similarity_score', 'created_at']
        read_only_fields = ['id', 'user', 'prompt_text', 'response_text', 'similarity_score', 'created_at']

