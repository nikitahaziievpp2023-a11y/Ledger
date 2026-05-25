from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas import LoginRequest, TokenResponse, UserOut
from app.auth_utils import verify_password, create_access_token
from app.database import get_conn
from app.dependencies import get_current_user

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (req.username, req.username),
        ).fetchone()
    if not row or not verify_password(req.password, row["hashed_pw"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": row["id"], "role": row["role"]})
    user = UserOut(
        id=row["id"], username=row["username"], email=row["email"],
        full_name=row["full_name"], role=row["role"], created_at=row["created_at"],
    )
    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=UserOut)
def me(current_user: dict = Depends(get_current_user)):
    return UserOut(**current_user)
