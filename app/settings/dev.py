"""
Development settings for app project.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# Channel Layers configuration - using InMemory for development
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# Database defaults to localhost for local development
# Override with environment variables if needed
DATABASES['default']['HOST'] = os.getenv('DB_HOST', 'localhost')

