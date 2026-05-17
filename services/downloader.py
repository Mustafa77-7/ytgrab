"""
Convert-YT Backend — Downloader Service
Handles metadata extraction, thumbnails, and preflight checks.
"""
import os
import base64
import yt_dlp
import asyncio
from config import MAX_VIDEO_DURATION

COOKIES_PATH = "/tmp/yt_cookies.txt"


def _write_cookies():
    """Write YouTube cookies from base64 env variable to temp file."""
    b64 = os.getenv("YOUTUBE_COOKIES_B64", "")
    if b64:
        try:
            content = base64.b64decode(b64).decode("utf-8")
            with open(COOKIES_PATH, "w") as f:
                f.write(content)
            return True
        except Exception:
            pass
    return False


def _get_opts():
    """Return yt-dlp options with fresh cookies."""
    _write_cookies()
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["ios", "mweb"],
            }
        },
        "http_headers": {
            "User-Agent": "com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iPhone OS 17_5_1 like Mac OS X)",
        },
        "socket_timeout": 30,
        "retries": 5,
    }
    if os.path.exists(COOKIES_PATH):
        opts["cookiefile"] = COOKIES_PATH
    return opts


async def get_video_info(url: str, timeout: int = 15) -> dict:
    """Fetch YouTube video metadata asynchronously with timeout."""
    def _fetch():
        with yt_dlp.YoutubeDL(_get_opts()) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title", "Unknown"),
                "thumbnail": info.get("thumbnail", ""),
                "duration": info.get("duration", 0),
                "channel": info.get("uploader", "Unknown"),
                "view_count": info.get("view_count", 0),
            }

    try:
        return await asyncio.wait_for(asyncio.to_thread(_fetch), timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError("Failed to fetch video info within the timeout period.")


async def extract_thumbnail(url: str, timeout: int = 15) -> str:
    """Extract only the highest quality thumbnail URL."""
    info = await get_video_info(url, timeout=timeout)
    thumbnail = info.get("thumbnail")
    if not thumbnail:
        raise ValueError("Thumbnail not available for this video.")
    return thumbnail


def preflight_check(url: str) -> dict:
    """Synchronous preflight check used during conversion to validate duration."""
    with yt_dlp.YoutubeDL(_get_opts()) as ydl:
        info = ydl.extract_info(url, download=False)
        duration = info.get("duration", 0)
        title = info.get("title", "video")

    if duration and duration > MAX_VIDEO_DURATION:
        raise ValueError(
            f"Video is too long (max {MAX_VIDEO_DURATION // 60} minutes). "
            "Please try a shorter video."
        )
    return {"title": title, "duration": duration}
