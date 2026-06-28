import os
import sys

# Matplotlib needs a writable config directory; /tmp is writable on Vercel
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

# Ensure the project root is on sys.path so Django can find all modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "budget_planner.settings")

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()