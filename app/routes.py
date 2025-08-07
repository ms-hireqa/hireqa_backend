from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.supabase_client import supabase
from datetime import datetime, timezone
import uuid
import bcrypt

router = APIRouter()

@router.post("/signup/jobseeker")
async def jobseeker_signup(
    full_name: str = Form(...),
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
        raise HTTPException(status_code=400, detail="User with given email, username, or phone number already exists")

    # 🔐 Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # 📤 Upload resume to Supabase Storage
    resume_content = await resume_uploaded.read()
    resume_filename = f"{username}_{resume_uploaded.filename}"
    storage_path = f"resumes/{resume_filename}"

    upload_response = supabase.storage.from_("resumes").upload(storage_path, resume_content)

    if hasattr(upload_response, "error") and upload_response.error:
        raise HTTPException(status_code=500, detail="Failed to upload resume")

    # 🌐 Get public URL
    resume_url = supabase.storage.from_("resumes").get_public_url(storage_path)

    # 📝 Insert into jobseeker_signup table
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
        raise HTTPException(status_code=500, detail="Failed to create jobseeker")

    return {
        "message": "Jobseeker signed up successfully",
        "resume_url": resume_url
    }
