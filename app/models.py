from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Union, Dict, Any
from datetime import datetime, date
from enum import Enum

# Enums
class RoleType(str, Enum):
    JOBSEEKER = "jobseeker"
    RECRUITER = "recruiter"
    ADMIN = "admin"

class ContractType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class MaritalStatus(str, Enum):
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    SEPARATED = "separated"

# Base Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None

# User Models
class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    phone_number: Optional[str] = Field(None, max_length=20)
    linkedin_url: Optional[str] = None
    summary: Optional[str] = None
    middle_name: Optional[str] = None
    current_job_location: Optional[str] = None
    preferred_job_locations: Optional[List[str]] = []
    role_type: RoleType = RoleType.JOBSEEKER

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    linkedin_url: Optional[str] = None
    summary: Optional[str] = None
    middle_name: Optional[str] = None
    current_job_location: Optional[str] = None
    preferred_job_locations: Optional[List[str]] = None

class UserInDB(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    candidate_id: int
    is_email_verified: bool = False
    accepted_terms: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None

# Authentication Models
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    candidate_id: int
    is_email_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

# Availability Models
class AvailabilityBase(BaseModel):
    current_ctc: Optional[int] = None
    expected_ctc: Optional[int] = None
    notice_period_days: Optional[int] = None
    current_contract_type: Optional[ContractType] = None
    expected_contract_type: Optional[ContractType] = None
    resignation_date: Optional[date] = None
    is_serving_notice_period: Optional[bool] = None
    last_working_day: Optional[date] = None

# Education Models
class EducationBase(BaseModel):
    degree: str
    institution_name: str
    field_of_study: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    gpa: Optional[float] = None
    is_current: bool = False
    relevant_projects: Optional[str] = None

class EducationCreate(EducationBase):
    pass

class EducationUpdate(BaseModel):
    degree: Optional[str] = None
    institution_name: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gpa: Optional[float] = None
    is_current: Optional[bool] = None
    relevant_projects: Optional[str] = None

class EducationInDB(EducationBase):
    model_config = ConfigDict(from_attributes=True)
    
    education_id: int
    candidate_id: int

# Work Experience Models
class WorkExperienceBase(BaseModel):
    job_title: str
    company_name: str
    location: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None
    is_current: bool = False

class WorkExperienceCreate(WorkExperienceBase):
    pass

class WorkExperienceUpdate(BaseModel):
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    is_current: Optional[bool] = None

class WorkExperienceInDB(WorkExperienceBase):
    model_config = ConfigDict(from_attributes=True)
    
    experience_id: int
    candidate_id: int
