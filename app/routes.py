from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.supabase_client import supabase
from datetime import datetime, timezone
import uuid
import bcrypt
from password_strength import PasswordPolicy
from zxcvbn import zxcvbn

router = APIRouter()

# Define password policy
policy = PasswordPolicy.from_names(
    length=8,            # min length: 8
    uppercase=1,         # need min. 1 uppercase letter
    numbers=1,           # need min. 1 digit
    special=1,           # need min. 1 special character
    nonletters=1         # need min. 1 non-letter (digit or special)
)

def validate_password(password: str):
    errors = policy.test(password)
    if errors:
        error_messages = [str(e) for e in errors]
        raise HTTPException(status_code=400, detail={
            "error_code": "SIGNUP_009",
            "message": "Password validation failed",
            "issues": error_messages
        })

@router.post("/signup/jobseeker")
async def jobseeker_signup(
    first_name: str = Form(...),
    middle_name: str = Form(""),
    last_name: str = Form(...),
    email_id: str = Form(...),
    phone_number: str = Form(...),
    accepted_terms_policy: bool = Form(...),
    password: str = Form(...),
    username: str = Form(...),
    gender: str = Form(...),
    location: str = Form(...),
    dob: str = Form(...),
    role_type: str = Form(...),
    resume_uploaded: UploadFile = File(...)
):
    # 🔍 Check for existing user
    existing_email = supabase.table("jobseeker_signup").select("*").eq("email_id", email_id).execute()
    existing_username = supabase.table("jobseeker_signup").select("*").eq("username", username).execute()
    existing_phone = supabase.table("jobseeker_signup").select("*").eq("phone_number", phone_number).execute()

    if existing_email.data or existing_username.data or existing_phone.data:
        raise HTTPException(status_code=400, detail={
            "error_code": "SIGNUP_006",
            "message": "User with given email, username, or phone number already exists"
        })

    # 🔐 Validate and hash password
    validate_password(password)
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # 📤 Upload resume to Supabase Storage
    resume_content = await resume_uploaded.read()
    resume_filename = f"{username}_{resume_uploaded.filename}"
    storage_path = f"resumes/{resume_filename}"

    upload_response = supabase.storage.from_("resumes").upload(storage_path, resume_content)

    if hasattr(upload_response, "error") and upload_response.error:
        raise HTTPException(status_code=500, detail={
            "error_code": "SIGNUP_007",
            "message": "Failed to upload resume"
        })

    # 🌐 Get public URL
    resume_url = supabase.storage.from_("resumes").get_public_url(storage_path)

    # 📝 Insert into jobseeker_signup table
    full_name = f"{first_name} {middle_name + ' ' if middle_name else ''}{last_name}"

    seeker_response = supabase.table("jobseeker_signup").insert([{
        "id": str(uuid.uuid4()),
        "full_name": full_name,
        "email_id": email_id,
        "phone_number": phone_number,
        "resume_uploaded": resume_url,
        "accepted_terms_policy": accepted_terms_policy,
        "Password_hash": hashed_password,
        "username": username,
        "gender": gender,
        "location": location,
        "DOB": dob,
        "Role_type": role_type,
        "updates_at": datetime.now(timezone.utc).isoformat(),
        "login_id": str(uuid.uuid4())
    }]).execute()

    if hasattr(seeker_response, "error") and seeker_response.error:
        raise HTTPException(status_code=500, detail={
            "error_code": "SIGNUP_008",
            "message": "Failed to create jobseeker"
        })

    return {
        "message": "Jobseeker signed up successfully",
        "resume_url": resume_url
    }

# 🧪 Password strength check endpoint using zxcvbn
@router.post("/password-strength-check")
def check_password_strength(password: str = Form(...)):
    result = zxcvbn(password)
    return {
        "score": result["score"],  # 0 (weak) to 4 (strong)
        "feedback": result["feedback"],
        "crack_time_estimate": result["crack_times_display"]
    }
