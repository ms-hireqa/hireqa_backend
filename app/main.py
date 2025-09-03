# app/main.py - Updated for Render deployment
import os
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
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
    # Get port from environment (Render sets PORT automatically)
    port = int(os.environ.get("PORT", 8000))
    
    app = FastAPI(
        title="HireQA API",
        description="Backend API for HireQA Job Portal",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # CORS middleware - Updated for production
    origins = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "https://your-frontend-domain.com",  # Add your actual frontend domain
        "https://*.onrender.com",  # Allow all Render subdomains
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=600
    )

    # Include API router
    app.include_router(api_router, prefix="/api", tags=["API"])

    # Root endpoint - Handle both GET and HEAD requests
    @app.get("/")
    @app.head("/")
    async def root():
        return {
            "message": "Welcome to HireQA API 🎯",
            "status": "running",
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "production"),
            "available_routes": {
                "docs": "/docs",
                "redoc": "/redoc", 
                "health": "/api/health",
                "login": "/api/login",
                "signup": "/api/signup/jobseeker"
            }
        }

    # Health check endpoints
    @app.get("/api/health")
    @app.head("/api/health")
    async def health_check():
        return {"status": "healthy", "version": "1.0.0", "port": port}

    @app.get("/api/health/ready")
    async def health_check_ready():
        try:
            # Test Supabase connection
            from app.supabase_client import supabase
            test_result = supabase.table("jobseeker").select("*").limit(1).execute()
            
            return {
                "status": "ready", 
                "database": "connected", 
                "port": port,
                "supabase": "connected"
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service unavailable: {str(e)}"
            )

    # Protected route
    @app.get("/api/users/me", response_model=UserResponse)
    async def read_users_me(current_user: UserResponse = Depends(get_current_user)):
        return current_user

    # Exception handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        print(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    return app

# Instantiate the app
app = create_app()

# Health check for Render
@app.get("/health")
async def health():
    return {"status": "ok"}

# For local development
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
