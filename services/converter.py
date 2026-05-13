import uuid
import yt_dlp
import asyncio
from pathlib import Path
from config import (
    TMP_DIR_PATH,
    VALID_AUDIO_QUALITIES, VALID_VIDEO_QUALITIES,
    DEFAULT_AUDIO_QUALITY, DEFAULT_VIDEO_QUALITY,
    MAX_VIDEO_DURATION,
)

tmp_dir = Path(TMP_DIR_PATH)
tmp_dir.mkdir(exist_ok=True)


async def convert_to_mp3(url: str, quality: str, timeout: int = 300) -> dict:
    def _process():
        audio_quality = quality if quality in VALID_AUDIO_QUALITIES else DEFAULT_AUDIO_QUALITY
        file_id = str(uuid.uuid4())[:10]
        out_template = str(tmp_dir / f"{file_id}.%(ext)s")

        result = {}

        def extract_info(d):
            if d.get("status") == "finished":
                result["title"] = d.get("info_dict", {}).get("title", "Unknown")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": out_template,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": audio_quality,
            }],
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "progress_hooks": [extract_info],
            "match_filter": _duration_check,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            result["title"] = info.get("title", "Unknown")

        out_file = _find_output_file(file_id, "mp3")
        return {
            "title": result.get("title", "Unknown"),
            "download_url": f"/api/download/{out_file.name}",
            "filename": f"{result.get('title', 'audio')[:80]}.mp3",
            "format": "mp3",
            "quality": audio_quality,
        }

    try:
        return await asyncio.wait_for(asyncio.to_thread(_process), timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError("Conversion timed out. The video might be too long.")


async def convert_to_mp4(url: str, quality: str, timeout: int = 300) -> dict:
    def _process():
        height = quality if quality in VALID_VIDEO_QUALITIES else DEFAULT_VIDEO_QUALITY
        file_id = str(uuid.uuid4())[:10]
        out_template = str(tmp_dir / f"{file_id}.%(ext)s")

        ydl_opts = {
            "format": f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/best",
            "outtmpl": out_template,
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "match_filter": _duration_check,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "Unknown")

        out_file = _find_output_file(file_id, "mp4")
        return {
            "title": title,
            "download_url": f"/api/download/{out_file.name}",
            "filename": f"{title[:80]}.mp4",
            "format": "mp4",
            "quality": height,
        }

    try:
        return await asyncio.wait_for(asyncio.to_thread(_process), timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError("Conversion timed out. The video might be too long.")


def _duration_check(info, *, incomplete):
    duration = info.get("duration") or 0
    if duration > MAX_VIDEO_DURATION:
        raise ValueError(
            f"Video is too long (max {MAX_VIDEO_DURATION // 60} minutes)."
        )


def _find_output_file(file_id: str, expected_ext: str) -> Path:
    out_file = tmp_dir / f"{file_id}.{expected_ext}"
    if out_file.exists():
        return out_file
    matches = list(tmp_dir.glob(f"{file_id}.*"))
    if matches:
        return matches[0]
    raise FileNotFoundError("Output file not found. Conversion may have failed.")
