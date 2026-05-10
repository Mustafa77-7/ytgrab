"""
YTGrab Backend — Configuration
Centralized settings loaded from environment variables.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()

# ─── Environment & CORS ─────────────────────────────
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# Parse comma-separated domains
_origins_str = os.getenv("ALLOWED_ORIGINS", "https://ytgrab.com,https://www.ytgrab.com")
ALLOWED_ORIGINS = [origin.strip() for origin in _origins_str.split(",") if origin.strip()]

# ─── File Settings ──────────────────────────────────
TMP_DIR_PATH = os.getenv("TMP_DIR_PATH", "/tmp/ytgrab")

try:
    MAX_VIDEO_DURATION = int(os.getenv("MAX_VIDEO_DURATION", "900"))
except ValueError:
    MAX_VIDEO_DURATION = 900

try:
    FILE_EXPIRY_SECONDS = int(os.getenv("FILE_EXPIRY_SECONDS", "1800"))
except ValueError:
    FILE_EXPIRY_SECONDS = 1800

# ─── Quality Presets ────────────────────────────────
VALID_AUDIO_QUALITIES = ("128", "192", "320")
VALID_VIDEO_QUALITIES = ("360", "720", "1080")
VALID_FORMATS = ("mp3", "mp4")
DEFAULT_AUDIO_QUALITY = "192"
DEFAULT_VIDEO_QUALITY = "720"
