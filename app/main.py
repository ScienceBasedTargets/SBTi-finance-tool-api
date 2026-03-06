from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import health, providers, temperature, coverage, whatif, upload


DESCRIPTION = """
REST API for the SBTi Finance Temperature Alignment Tool.

Wraps the [sbti-finance-tool](https://github.com/ScienceBasedTargets/SBTi-finance-tool)
Python package. Provides endpoints for temperature scoring, portfolio coverage,
what-if scenario analysis, and file upload scoring.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="SBTi Finance Temperature Alignment Tool API",
    description=DESCRIPTION,
    version="2.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "deny"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-cache"
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


app.include_router(health.router, tags=["Health"])
app.include_router(providers.router, prefix="/v1", tags=["Data Providers"])
app.include_router(temperature.router, prefix="/v1/temperature", tags=["Temperature Score"])
app.include_router(coverage.router, prefix="/v1", tags=["Portfolio Coverage"])
app.include_router(whatif.router, prefix="/v1/temperature", tags=["What-If Analysis"])
app.include_router(upload.router, prefix="/v1/upload", tags=["File Upload"])
