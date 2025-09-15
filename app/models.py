from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional

class Voter(BaseModel):
    voter_id: int
    name: str
    email: EmailStr
    age: int = Field(..., ge=18, description="Voter must be at least 18 years old")

    # Optional: extra validator for more control
    @validator("age")
    def check_age(cls, value):
        if value < 18:
            raise ValueError("Voter must be at least 18 years old to register.")
        return value

class Candidate(BaseModel):
    candidate_id: int
    name: str
    party: Optional[str] = None