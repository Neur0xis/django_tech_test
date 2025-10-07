"""
Views for the core app module.
"""

from rest_framework.decorators import throttle_classes
from rest_framework_simplejwt.views import TokenObtainPairView


@throttle_classes([])
class LoginView(TokenObtainPairView):
    """
    JWT login endpoint with throttling disabled.
    
    Throttling is excluded from login as per technical specification -
    only POST /prompts requires rate limiting (1 per second).
    """
    pass

