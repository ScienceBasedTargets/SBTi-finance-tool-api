from fastapi import APIRouter

router = APIRouter()

API_VERSION = "2.0.0"


@router.get("/health", summary="Liveness check")
def health():
    return {"status": "ok"}


@router.get("/health/ready", summary="Readiness check")
def health_ready():
    """Returns API version. Use for readiness probes."""
    return {"status": "ok", "version": API_VERSION}
