"""
Custom middleware for request logging and monitoring.
Provides structured logging for all HTTP requests without exposing sensitive data.
"""
import logging
import time

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """
    Middleware that logs each HTTP request with method, path, user, and response status.
    
    Security considerations:
    - Does not log request bodies (may contain passwords)
    - Does not log Authorization headers or tokens
    - Does not log cookie data
    - Only logs basic request metadata and response status
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Capture request start time for performance monitoring
        start_time = time.time()
        
        # Get user information (handle unauthenticated requests)
        user = "anonymous"
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user.username
        
        # Process the request
        response = self.get_response(request)
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Build log message with structured data
        log_message = (
            f"method={request.method} "
            f"path={request.path} "
            f"user={user} "
            f"status={response.status_code} "
            f"duration={duration:.3f}s"
        )
        
        # Log at appropriate level based on response status
        if response.status_code < 400:
            # Success (2xx, 3xx)
            logger.info(log_message)
        elif response.status_code < 500:
            # Client error (4xx)
            logger.warning(log_message)
        else:
            # Server error (5xx)
            logger.error(log_message)
        
        return response

