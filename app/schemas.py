from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import date


# ── Auth ──

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


# ── Users ──

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: str
    full_name: str = Field(..., min_length=1, max_length=80)
    password: str = Field(..., min_length=6)
    role: Literal["user", "admin"] = "user"

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[Literal["user", "admin"]] = None
    password: Optional[str] = None

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    created_at: str

    class Config:
        from_attributes = True


# ── Expenses ──

CATEGORIES = Literal[
    "food", "transport", "housing", "health",
    "entertainment", "shopping", "utilities", "other"
]

class ExpenseCreate(BaseModel):
    amount: float = Field(..., gt=0)
    category: CATEGORIES
    description: str = Field("", max_length=200)
    date: str  # ISO date string YYYY-MM-DD

class ExpenseUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[CATEGORIES] = None
    description: Optional[str] = Field(None, max_length=200)
    date: Optional[str] = None

class ExpenseOut(BaseModel):
    id: int
    user_id: int
    username: str
    full_name: str
    amount: float
    category: str
    description: str
    date: str
    created_at: str
    updated_at: str

class ExpenseSummary(BaseModel):
    total: float
    count: int
    by_category: dict[str, float]
    by_month: dict[str, float]
