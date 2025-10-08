"""
Test settings for app project.

This configuration is specifically designed for running tests in complete isolation
from external services. It uses SQLite in-memory database instead of PostgreSQL,
ensuring that:

1. Tests run without Docker or any external database service
2. No network dependencies or environment variables required
3. Database is created and destroyed automatically in memory
4. Tests are fast, isolated, and reproducible

All other settings (middleware, installed apps, authentication, etc.) are inherited
from base.py to maintain consistency with production/development environments.
"""

import os

# Set required environment variables before importing base settings
# This prevents ImproperlyConfigured errors when base.py calls get_env_variable()
os.environ.setdefault('SECRET_KEY', 'test-secret-key-not-for-production-use-only')

from .base import *

# Disable debug mode in tests for more realistic behavior
DEBUG = False

# Allow all hosts in test environment
ALLOWED_HOSTS = ['*']

# Override database configuration to use SQLite in-memory
# This is the core change that makes tests independent of PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # In-memory database, created and destroyed per test run
    }
}

# Use in-memory channel layers for WebSocket testing
# No Redis or external message broker required
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# Configure cache backend for tests
# Uses local memory cache to persist throttle counters between requests during test execution
# This enables throttling tests to correctly detect rate limit violations (429 responses)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-throttle-test-cache"
    }
}

# Disable password hashing for faster test execution
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Simplify logging for test environment
LOGGING['root']['level'] = 'ERROR'
LOGGING['loggers']['django']['level'] = 'ERROR'

