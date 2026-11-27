"""
WSGI config for mealmate project (root entrypoint).
"""
import os
import sys
from pathlib import Path

# Add inner mealmate folder to sys.path
base_dir = Path(__file__).resolve().parent
inner_mealmate = base_dir / 'mealmate'
if str(inner_mealmate) not in sys.path:
    sys.path.insert(0, str(inner_mealmate))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mealmate.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
