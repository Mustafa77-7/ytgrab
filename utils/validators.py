"""
YTGrab Backend — Validators
URL validation, sanitization, and security checks.
"""
import re


def validate_youtube_url(url: str) -> bool:
    """Check if the given string is a valid YouTube URL."""
    if not url:
        return False
    # More strict pattern to prevent SSRF and injection
    pattern = r'^https?://(www\.)?(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)[\w-]{11}(&.*)?$'
    return bool(re.match(pattern, url))


def sanitize_filename(filename: str) -> str:
    """Remove path traversal characters and limit filename length."""
    if "/" in filename or "\\" in filename or ".." in filename:
        return ""
    # Only allow safe characters
    safe = re.sub(r'[<>:"/\\|?*]', '', filename)
    return safe.strip()


def format_safe_title(title: str, max_length: int = 80) -> str:
    """Truncate title for use in download filenames."""
    safe = sanitize_filename(title)
    return safe[:max_length].strip()
