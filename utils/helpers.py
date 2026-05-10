"""
YTGrab Backend — Helpers
General utility functions and system operations.
"""
import time
from pathlib import Path
from config import TMP_DIR_PATH, FILE_EXPIRY_SECONDS


def cleanup_old_files():
    """Remove converted files older than FILE_EXPIRY_SECONDS from the temp directory."""
    tmp_dir = Path(TMP_DIR_PATH)
    if not tmp_dir.exists():
        return

    now = time.time()
    for f in tmp_dir.glob("*"):
        try:
            if now - f.stat().st_mtime > FILE_EXPIRY_SECONDS:
                f.unlink()
        except OSError:
            pass


def standard_response(data=None, error=None):
    """Format API response to standard {success, data, error} schema."""
    if error:
        return {"success": False, "data": None, "error": str(error)}
    return {"success": True, "data": data or {}, "error": None}
