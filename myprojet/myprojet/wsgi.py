import os
import sys
from pathlib import Path

# Add the directory containing manage.py to the Python path
# so Vercel can locate "myprojet.settings"
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myprojet.settings')

application = get_wsgi_application()

app = application
