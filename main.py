"""
YTGrab Backend — FastAPI Application Entry Point
Deploy on Railway.app or any ASGI host.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from contextlib import asynccontextmanager

from config import ALLOWED_ORIGINS
from api.routes import router as api_router
from utils.helpers import standard_response, cleanup_old_files
from utils.logger import logger

# ─── Background Tasks ────────────────────────────────

async def cleanup_loop():
    """Continuously clean up old files in the background."""
    while True:
        try:
            cleanup_old_files()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        await asyncio.sleep(300)  # Run every 5 minutes

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI to run background tasks."""
    task = asyncio.create_task(cleanup_loop())
    yield
    task.cancel()

# ─── App ─────────────────────────────────────────────

app = FastAPI(
    title="YTGrab API",
    version="1.1.0",
    description="YouTube to MP3/MP4 converter API with Standardized Responses",
    lifespan=lifespan,
)

# ─── CORS & Rate Limit Middleware ────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_size_limiter(request: Request, call_next):
    """Reject requests with payloads larger than 1MB to prevent DoS."""
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 1_048_576:  # 1MB
        return JSONResponse(
            status_code=413,
            content=standard_response(error="Payload too large. Max allowed size is 1MB.")
        )
    return await call_next(request)

@app.middleware("http")
async def rate_limit_placeholder(request: Request, call_next):
    """
    Placeholder for IP-based rate limiting.
    You can integrate libraries like slowapi or fastapi-limiter here.
    """
    # client_ip = request.client.host
    # if is_rate_limited(client_ip):
    #     return JSONResponse(status_code=429, content=standard_response(error="Rate limit exceeded"))
    return await call_next(request)

# ─── Exception Handlers ──────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all for unexpected errors."""
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=standard_response(error="An internal server error occurred.")
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle business logic / validation errors."""
    return JSONResponse(
        status_code=400,
        content=standard_response(error=str(exc))
    )

@app.exception_handler(TimeoutError)
async def timeout_error_handler(request: Request, exc: TimeoutError):
    """Handle long-running process timeouts."""
    logger.warning(f"Timeout exception: {exc}")
    return JSONResponse(
        status_code=408,
        content=standard_response(error=str(exc))
    )

# ─── Routes ──────────────────────────────────────────

app.include_router(api_router)


# ─── Health Check ────────────────────────────────────

@app.get("/")
async def health():
    return standard_response(data={"status": "ok", "service": "YTGrab API", "version": "1.1.0"})
