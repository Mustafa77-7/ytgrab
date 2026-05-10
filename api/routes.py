"""
YTGrab Backend — API Routes
All HTTP endpoint handlers.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from pathlib import Path

from config import TMP_DIR_PATH
from utils.validators import validate_youtube_url, sanitize_filename
from utils.helpers import cleanup_old_files, standard_response
from services.downloader import get_video_info, extract_thumbnail
from services.converter import convert_to_mp3, convert_to_mp4

router = APIRouter(prefix="/api")
tmp_dir = Path(TMP_DIR_PATH)


# ─── Request Models ──────────────────────────────────

class UrlRequest(BaseModel):
    url: str = Field(..., max_length=1500, description="The YouTube URL")

class ConvertRequest(BaseModel):
    url: str = Field(..., max_length=1500, description="The YouTube URL")
    quality: str = Field(..., max_length=10, description="The desired format quality")


# ─── Middleware / Deps ───────────────────────────────

def check_url(url: str):
    """Validate YouTube URL."""
    if not validate_youtube_url(url):
        raise ValueError("Invalid YouTube URL provided.")


# ─── Endpoints ───────────────────────────────────────

@router.post("/info")
async def video_info(req: UrlRequest):
    """Fetch YouTube video metadata."""
    check_url(req.url)
    data = await get_video_info(req.url)
    return standard_response(data=data)


@router.post("/thumbnail")
async def video_thumbnail(req: UrlRequest):
    """Fetch only the highest quality thumbnail URL."""
    check_url(req.url)
    thumb_url = await extract_thumbnail(req.url)
    return standard_response(data={"thumbnail": thumb_url})


@router.post("/convert/mp3")
async def convert_mp3_endpoint(req: ConvertRequest):
    """Convert YouTube video to MP3."""
    check_url(req.url)
    data = await convert_to_mp3(req.url, req.quality)
    return standard_response(data=data)


@router.post("/convert/mp4")
async def convert_mp4_endpoint(req: ConvertRequest):
    """Convert YouTube video to MP4."""
    check_url(req.url)
    data = await convert_to_mp4(req.url, req.quality)
    return standard_response(data=data)


@router.get("/download/{filename}")
async def download_file(filename: str):
    """Serve the converted file for download. Cannot use standard response due to binary payload."""
    safe_name = sanitize_filename(filename)
    if not safe_name:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = tmp_dir / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found or expired. Please convert again.")

    media_type = "audio/mpeg" if safe_name.endswith(".mp3") else "video/mp4"
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=safe_name,
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'}
    )
