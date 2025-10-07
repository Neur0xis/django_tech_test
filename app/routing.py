"""
WebSocket routing configuration for the app.
Defines URL patterns for WebSocket connections.
"""
from django.urls import re_path
from app_prompts.consumers import PromptConsumer

websocket_urlpatterns = [
    re_path(r'ws/prompts/(?P<username>\w+)/$', PromptConsumer.as_asgi()),
]

