# Updated routes.py with enhanced debugging and fixes

import uuid
import bcrypt
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from zxcvbn import zxcvbn as zxcvbn_check
from pydantic import BaseModel

from app.supabase_client import supabase
from app.email_service import email_service
from app.jwt_handler import create_access_token, verify_token, oauth2_scheme, TokenData, SECRET_KEY, ALGORITHM
from app.models import Token, UserBase as User, UserInDB, UserResponse

# Password hashing - FIXED: Use consistent configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt"""
    try:
        # Debug print
        print(f"Verifying password...")
        print(f"Plain password length: {len(plain_password)}")
        print(f"Hashed password starts with: {hashed_password[:10]}...")
        
        result = pwd_context.verify(plain_password, hashed_password)
        print(f"Password verification result: {result}")
        return result
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    result = supabase.table("jobseeker").select("*").eq("email", email).execute()
    if not result.data:
        raise credentials_exception
    return result.data[0]

# Create router instance
router = APIRouter()

# Simple login model
class SimpleLogin(BaseModel):
    email: str
    password: str

# DEBUG ENDPOINT: Check user exists and password hash
@router.post("/debug/check-user")
async def debug_check_user(login_data: SimpleLogin):
    """Debug endpoint to check user data"""
    try:
        print(f"=== DEBUG CHECK USER ===")
        print(f"Looking for email: {login_data.email}")
        
        # Get user from database
        result = supabase.table("jobseeker").select("*").eq("email", login_data.email).execute()
        
        if not result.data:
            return {
                "status": "user_not_found",
                "email": login_data.email,
                "message": "No user found with this email"
            }
        
        user = result.data[0]
        
        # Check password verification
        password_match = verify_password(login_data.password, user["password"])
        
        return {
            "status": "user_found",
            "email": user["email"],
            "candidate_id": user["candidate_id"],
            "is_email_verified": user.get("is_email_verified", False),
            "password_match": password_match,
            "password_hash_prefix": user["password"][:20] + "...",
            "created_at": user.get("created_at"),
            "has_password": bool(user.get("password"))
        }
        
    except Exception as e:
        print(f"Debug error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

# ENHANCED LOGIN ENDPOINT with better debugging
@router.post("/login", response_model=Token)
async def login_for_access_token(login_data: SimpleLogin):
    """
    Enhanced login endpoint with comprehensive debugging
    """
    print(f"=== LOGIN ATTEMPT ===")
    print(f"Email: {login_data.email}")
    print(f"Password length: {len(login_data.password)}")
    
    try:
        # Step 1: Get user from database
        print("Step 1: Querying database...")
        result = supabase.table("jobseeker").select("*").eq("email", login_data.email).execute()
        print(f"Database query result: {len(result.data) if result.data else 0} records found")
        
        if not result.data:
            print("ERROR: No user found with this email")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
            
        user = result.data[0]
        print(f"User found - ID: {user['candidate_id']}, Email: {user['email']}")
        print(f"Email verified: {user.get('is_email_verified', False)}")
        print(f"Has password: {bool(user.get('password'))}")
        
        # Step 2: Verify password
        print("Step 2: Verifying password...")
        if not user.get("password"):
            print("ERROR: User has no password hash stored")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account setup incomplete. Please contact support.",
            )
            
        password_match = verify_password(login_data.password, user["password"])
        print(f"Password verification result: {password_match}")
        
        if not password_match:
            print("ERROR: Password verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        
        # Step 3: Check if email is verified
        print("Step 3: Checking email verification...")
        if not user.get("is_email_verified", False):
            print("ERROR: Email not verified")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified. Please check your email for verification link."
            )
        
        # Step 4: Create access token
        print("Step 4: Creating access token...")
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user["email"]}, 
            expires_delta=access_token_expires
        )
        
        print("LOGIN SUCCESS!")
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"UNEXPECTED ERROR during login: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

# UTILITY ENDPOINT: Reset user password (for testing)
@router.post("/debug/reset-password")
async def debug_reset_password(email: str = Form(...), new_password: str = Form(...)):
    """Debug endpoint to reset a user's password"""
    try:
        # Find user
        result = supabase.table("jobseeker").select("*").eq("email", email).execute()
        if not result.data:
            return {"error": "User not found"}
        
        # Hash new password
        new_hash = get_password_hash(new_password)
        
        # Update password
        update_result = supabase.table("jobseeker").update({
            "password": new_hash
        }).eq("email", email).execute()
        
        if update_result.data:
            return {
                "status": "success",
                "message": "Password updated successfully",
                "new_hash_prefix": new_hash[:20] + "..."
            }
        else:
            return {"error": "Failed to update password"}
            
    except Exception as e:
        return {"error": str(e)}

# Alternative form-based login endpoint
@router.post("/login-form", response_model=Token)
async def login_form(
    email: str = Form(...),
    password: str = Form(...)
):
    """
    Login endpoint that accepts form data (email and password)
    """
    # Use the same logic as the main login endpoint
    login_data = SimpleLogin(email=email, password=password)
    return await login_for_access_token(login_data)

# Protected route example
@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# Test endpoint to verify Supabase connection
@router.get("/test-connection", response_model=Dict[str, Any])
async def test_connection():
    """Test endpoint to verify Supabase connection."""
    try:
        # Try to fetch a single record from the jobseeker table
        response = supabase.table("jobseeker").select("*").limit(1).execute()
        return {
            "status": "success",
            "message": "Successfully connected to Supabase",
            "record_count": len(response.data) if response.data else 0
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Failed to connect to Supabase: {str(e)}",
                "error_details": str(e)
            }
        )

# Simplified password validation using zxcvbn
def validate_password(password: str):
    """
    Validate password strength using zxcvbn
    Requires minimum score of 2 (out of 4) for acceptable strength
    """
    result = zxcvbn_check(password)
    
    # zxcvbn scores: 0 (too guessable) to 4 (very unguessable)
    # We require at least score 2 for signup
    if result["score"] < 2:
        raise HTTPException(status_code=400, detail={
            "error_code": "SIGNUP_009",
            "message": "Password is too weak",
            "feedback": result["feedback"]["suggestions"],
            "score": result["score"]
        })

# Updated signup endpoint with email verification
@router.post("/signup/jobseeker")
async def jobseeker_signup(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email_id: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    phone_number: str = Form(...),
    gender: str = Form(...),
    role_type: str = Form(...),
    location: str = Form(...),
    dob: str = Form(...),
    accepted_terms_policy: bool = Form(...),
    middle_name: str = Form(""),
    resume_uploaded: UploadFile = File(...)
):
    """Jobseeker signup with email verification"""
    try:
        print("=== SIGNUP WITH EMAIL VERIFICATION ===")
        print(f"Email: {email_id}")
        print(f"Name: {first_name} {last_name}")
        
        # Step 1: Validate password strength
        try:
            validate_password(password)
        except HTTPException as e:
            return JSONResponse(status_code=400, content=e.detail)
        
        # Step 2: Check if email already exists
        existing_user = supabase.table("jobseeker").select("email").eq("email", email_id).execute()
        if existing_user.data:
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "SIGNUP_001",
                    "message": "Email already registered"
                }
            )
        
        # Step 3: Check if username already exists
        existing_username = supabase.table("jobseeker").select("username").eq("username", username).execute()
        if existing_username.data:
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "SIGNUP_002", 
                    "message": "Username already taken"
                }
            )
        
        # Step 4: Parse date
        try:
            dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
        except ValueError as ve:
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "SIGNUP_003",
                    "message": "Invalid date format. Use YYYY-MM-DD"
                }
            )
        
        # Step 5: Hash password using the SAME method as login verification
        print("Hashing password...")
        hashed_password = get_password_hash(password)
        print(f"Password hashed successfully: {hashed_password[:20]}...")
        
        # Step 6: Generate verification token
        verification_token = email_service.generate_verification_token()
        token_expiry = datetime.now(timezone.utc) + timedelta(hours=24)
        
        # Step 7: Insert jobseeker data
        jobseeker_data = {
            "first_name": first_name,
            "middle_name": middle_name if middle_name else None,
            "last_name": last_name,
            "email": email_id,
            "username": username,
            "password": hashed_password,
            "phone_number": phone_number,
            "accepted_TandC": accepted_terms_policy,
            "is_email_verified": False,
            "current_job_location": location,
            "role_type": role_type,
            "email_verification_token": verification_token,
            "email_verification_token_expires": token_expiry.isoformat()
        }
        
        print(f"Inserting jobseeker data...")
        
        response = supabase.table("jobseeker").insert(jobseeker_data).execute()
        
        if not response.data:
            return JSONResponse(
                status_code=500,
                content={
                    "error_code": "SIGNUP_004",
                    "message": "Failed to create user account"
                }
            )
        
        candidate_id = response.data[0].get("candidate_id")
        print(f"Jobseeker created with ID: {candidate_id}")
        
        # Step 8: Insert personal details
        personal_data = {
            "candidate_id": candidate_id,
            "DOB": dob_date.isoformat(),
            "gender": gender
        }
        
        personal_response = supabase.table("jobseeker_personal_details").insert(personal_data).execute()
        
        if not personal_response.data:
            # Rollback - delete the jobseeker record
            supabase.table("jobseeker").delete().eq("candidate_id", candidate_id).execute()
            return JSONResponse(
                status_code=500,
                content={
                    "error_code": "SIGNUP_005",
                    "message": "Failed to create personal details"
                }
            )
        
        # Step 9: Send verification email
        email_result = email_service.send_verification_email(
            recipient_email=email_id,
            first_name=first_name,
            verification_token=verification_token
        )
        
        if not email_result["success"]:
            print(f"Email sending failed: {email_result['message']}")
        
        # Step 10: Handle resume upload (placeholder)
        resume_content = await resume_uploaded.read()
        print(f"Resume received: {resume_uploaded.filename}, size: {len(resume_content)} bytes")
        
        return {
            "status": "success",
            "message": "Signup successful! Please check your email to verify your account.",
            "candidate_id": candidate_id,
            "email_sent": email_result["success"],
            "email_message": email_result["message"]
        }
            
    except Exception as e:
        print(f"Signup error: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "SIGNUP_006",
                "message": "Internal server error during signup",
                "details": str(e)
            }
        )

# Email verification endpoint
@router.get("/verify-email")
async def verify_email(token: str):
    """Verify user email using token"""
    try:
        # Find user with this token
        response = supabase.table("jobseeker").select("*").eq("email_verification_token", token).execute()
        
        if not response.data:
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "VERIFY_001",
                    "message": "Invalid verification token"
                }
            )
        
        user = response.data[0]
        
        # Check if token has expired
        token_expiry_str = user["email_verification_token_expires"]
        if token_expiry_str:
            # Handle different timestamp formats
            if 'Z' in token_expiry_str:
                token_expiry = datetime.fromisoformat(token_expiry_str.replace('Z', '+00:00'))
            else:
                token_expiry = datetime.fromisoformat(token_expiry_str)
                
            if datetime.now(timezone.utc) > token_expiry:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error_code": "VERIFY_002", 
                        "message": "Verification token has expired"
                    }
                )
        
        # Check if already verified
        if user["is_email_verified"]:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Email is already verified"
                }
            )
        
        # Update user as verified
        update_response = supabase.table("jobseeker").update({
            "is_email_verified": True,
            "email_verification_token": None,
            "email_verification_token_expires": None,
            "email_verified_at": datetime.now(timezone.utc).isoformat()
        }).eq("candidate_id", user["candidate_id"]).execute()
        
        if update_response.data:
            return {
                "status": "success",
                "message": "Email verified successfully! You can now log in to your account."
            }
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "error_code": "VERIFY_003",
                    "message": "Failed to update verification status"
                }
            )
            
    except Exception as e:
        print(f"Email verification error: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "VERIFY_004",
                "message": "Internal server error during verification"
            }
        )

# Resend verification email endpoint
@router.post("/resend-verification")
async def resend_verification_email(email: str = Form(...)):
    """Resend verification email to user"""
    try:
        # Find user by email
        response = supabase.table("jobseeker").select("*").eq("email", email).execute()
        
        if not response.data:
            return JSONResponse(
                status_code=404,
                content={
                    "error_code": "RESEND_001",
                    "message": "No account found with this email"
                }
            )
        
        user = response.data[0]
        
        # Check if already verified
        if user["is_email_verified"]:
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "RESEND_002",
                    "message": "Email is already verified"
                }
            )
        
        # Generate new token
        new_token = email_service.generate_verification_token()
        new_expiry = datetime.now(timezone.utc) + timedelta(hours=24)
        
        # Update token in database
        update_response = supabase.table("jobseeker").update({
            "email_verification_token": new_token,
            "email_verification_token_expires": new_expiry.isoformat()
        }).eq("candidate_id", user["candidate_id"]).execute()
        
        if not update_response.data:
            return JSONResponse(
                status_code=500,
                content={
                    "error_code": "RESEND_003",
                    "message": "Failed to generate new verification token"
                }
            )
        
        # Send new verification email
        email_result = email_service.send_verification_email(
            recipient_email=email,
            first_name=user["first_name"],
            verification_token=new_token
        )
        
        if email_result["success"]:
            return {
                "status": "success",
                "message": "Verification email sent successfully! Please check your inbox."
            }
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "error_code": "RESEND_004",
                    "message": f"Failed to send verification email: {email_result['message']}"
                }
            )
            
    except Exception as e:
        print(f"Resend verification error: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "RESEND_005",
                "message": "Internal server error"
            }
        )

# Password strength check endpoint
@router.post("/password-strength-check")
def check_password_strength(password: str = Form(...)):
    result = zxcvbn_check(password)
    return {
        "score": result["score"],
        "feedback": result["feedback"],
        "crack_time_estimate": result["crack_times_display"]
    }

# Verification success endpoint
@router.get("/verification-success")
async def verification_success():
    """Success page after email verification"""
    return {
        "status": "success",
        "message": "Email verification successful! You can now log in to your account.",
        "redirect_url": "http://localhost:3000/login"
    }
    
