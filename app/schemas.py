from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class JobSeekerSignup(BaseModel):
    full_name: str
    email_id: EmailStr
    phone_number: str  # Must be string for varchar(10)
    accepted_terms_policy: bool
    password: str
    username: str
    gender: str
    location: str
    dob: date
    role_type: str