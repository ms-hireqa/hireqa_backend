from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date
import uuid

class JobSeekerSignup(BaseModel):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    first_name: str
    middle_name: Optional[str] = ""
    last_name: str
    email_id: EmailStr
    phone_number: str  # Must be exactly 10 digits
    accepted_terms_policy: bool
    password: str  # Plaintext for validation; will be hashed before insert
    username: str
    gender: str  # Should match enum values in Supabase
    location: str
    dob: date
    role_type: str  # Should match enum values in Supabase
