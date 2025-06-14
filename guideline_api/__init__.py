# guideline_api/__init__.py
from .celery import app as celery_app

__all__ = ('celery_app',)

# jobs/__init__.py
# This file makes Python treat the directory as a package