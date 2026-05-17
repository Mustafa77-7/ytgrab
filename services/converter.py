"""
Convert-YT Backend — Converter Service
Handles video/audio extraction via yt-dlp.
"""
import os
import uuid
import yt_dlp
import asyncio
from pathlib import Path
from config import (
    TMP_DIR_PATH,
    VALID_AUDIO_QUALITIES, VALID_VIDEO_QUALITIES,
    DEFAULT_AUDIO_QUALITY, DEFAULT_VIDEO_QUALITY,
)
from services.downloader import preflight_check, _write_cookies, COOKIES_PATH

tmp_dir = Path(TMP_DIR_PATH)
tmp_dir.mkdir(exist_ok=True)


def _get_download_opts(extra: dict) -> dict:
    _write_cookies()
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "extractor_args": {
            "youtube": {"player_client": ["ios", "mweb"]}
        },
        "http_headers": {
            "User-Agent": "com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iPhone OS 17_5_1 like Mac OS X)",
        },
        "socket_timeout": 30,
        "retries": 5,
    }
    if os.path.exists(COOKIES_PATH):
        opts["cookiefile"] = COOKIES_PATH
    opts.update(extra)
    return opts


async def convert_to_mp3(url: str, quality: str, timeout: int = 300) -> dict:
    """Convert YouTube video to MP3 asynchronously with a timeout."""
    def _process():
        audio_quality = quality if quality in VALID_AUDIO_QUALITIES else DEFAULT_AUDIO_QUALITY
        file_id = str(uuid.uuid4())[:10]
        out_template = str(tmp_dir / f"{file_id}.%(ext)s")

        info = preflight_check(url)

        ydl_opts = _get_download_opts({
            "format": "bestaudio/best",
            "outtmpl": out_template,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": audio_quality,
            }],
        })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        out_file = _find_output_file(file_id, "mp3")
        return {
            "title": info["title"],
            "download_url": f"/api/download/{out_file.name}",
            "filename": f"{info['title'][:80]}.mp3",
            "format": "mp3",
            "quality": audio_quality,
        }

    try:
        return await asyncio.wait_for(asyncio.to_thread(_process), timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError("Conversion timed out. The video might be too long or YouTube is throttling.")


async def convert_to_mp4(url: str, quality: str, timeout: int = 300) -> dict:
    """Convert YouTube video to MP4 asynchronously with a timeout."""
    def _process():
        height = quality if quality in VALID_VIDEO_QUALITIES else DEFAULT_VIDEO_QUALITY
        file_id = str(uuid.uuid4())[:10]
        out_template = str(tmp_dir / f"{file_id}.%(ext)s")

        info = preflight_check(url)

        ydl_opts = _get_download_opts({
            "format": f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/best",
            "outtmpl": out_template,
            "merge_output_format": "mp4",
        })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        out_file = _find_output_file(file_id, "mp4")
        return {
            "title": info["title"],
            "download_url": f"/api/download/{out_file.name}",
            "filename": f"{info['title'][:80]}.mp4",
            "format": "mp4",
            "quality": height,
        }

    try:
        return await asyncio.wait_for(asyncio.to_thread(_process), timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError("Conversion timed out. The video might be too long or YouTube is throttling.")


def _find_output_file(file_id: str, expected_ext: str) -> Path:
    out_file = tmp_dir / f"{file_id}.{expected_ext}"
    if out_file.exists():
        return out_file
    matches = list(tmp_dir.glob(f"{file_id}.*"))
    if matches:
        return matches[0]
    raise FileNotFoundError("Output file not found. Conversion may have failed.")
