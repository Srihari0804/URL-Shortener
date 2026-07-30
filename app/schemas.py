from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Optional
from datetime import datetime

class CreateUser(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

class CreateShortURL(BaseModel):
    original_url: HttpUrl
    expires_at: Optional[datetime] = None

class URLSReturn(BaseModel):
    id: int
    short_code: str
    original_url: str
    created_at: datetime
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}