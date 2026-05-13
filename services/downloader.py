import yt_dlp
import asyncio


async def get_video_info(url: str, timeout: int = 10) -> dict:
    def _fetch():
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
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


async def extract_thumbnail(url: str, timeout: int = 10) -> str:
    info = await get_video_info(url, timeout=timeout)
    thumbnail = info.get("thumbnail")
    if not thumbnail:
        raise ValueError("Thumbnail not available for this video.")
    return thumbnail
