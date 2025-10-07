from django.db import models
from django.contrib.auth.models import User


class Prompt(models.Model):
    """Stores user prompts and their responses."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prompts')
    prompt_text = models.TextField()
    response_text = models.TextField()
    embedding = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.prompt_text[:50]}"
