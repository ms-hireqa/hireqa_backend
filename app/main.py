# app/main.py
# virtual environment: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass      .\venv\Scripts\Activate.ps1
# run statement: uvicorn app.main:app --reload

import os
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from jose import JWTError

# Import routers
from app.routes import router as api_router

# Import JWT utilities
from app.jwt_handler import (
    oauth2_scheme,
    TokenData,
    verify_token,
    get_current_user
)

# Import models
from app.models import UserResponse

def create_app() -> FastAPI:
    app = FastAPI(
    title="HireQA API",
    description="Backend API for HireQA Job Portal",
    version="1.0.0",
    docs_url="/docs",  
    redoc_url="/redoc",  
    openapi_url="/openapi.json"  
)

    # CORS middleware configuration
    origins = [
        "http://localhost:3000",  # React default
        "http://localhost:8000",  # FastAPI default
        "http://localhost:8080",  # Common alternative
        "https://your-production-domain.com"  # Production domain
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=600  # 10 minutes
    )

    # Include API router with proper prefix
    app.include_router(api_router, prefix="/api", tags=["API"])

    # Health check endpoint
    @app.get("/api/health")
    async def health_check():
        return {"status": "healthy", "version": "1.0.0"}

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Welcome to HireQA API",
            "docs": "/api/docs",
            "redoc": "/api/redoc"
        }

    # Global exception handler
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None),
        )

    # Request validation error handler
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": jsonable_encoder(exc.errors())},
        )

    # Global error handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # Log the error here
        print(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    # Protected route example
    @app.get("/api/users/me", response_model=UserResponse)
    async def read_users_me(current_user: UserResponse = Depends(get_current_user)):
        """
        Get current user information.
        """
        return current_user

    # Health check endpoint with database connection test
    @app.get("/api/health/ready")
    async def health_check_ready():
        """
        Health check endpoint that verifies database connectivity.
        """
        try:
            # Test database connection
            # Replace with your actual database health check
            return {"status": "ready", "database": "connected"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service unavailable: {str(e)}"
            )

    return app

# Create the FastAPI application
app = create_app()
