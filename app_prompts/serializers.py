from rest_framework import serializers
from .models import Prompt


class PromptSerializer(serializers.ModelSerializer):
    """Serializer for Prompt model."""
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Prompt
        fields = ['id', 'user', 'prompt_text', 'response_text', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


