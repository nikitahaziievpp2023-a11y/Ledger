from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.schemas import UserCreate, UserUpdate, UserOut
from app.auth_utils import hash_password
from app.database import get_conn
from app.dependencies import get_current_user, require_admin

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: UserCreate):
    """Public registration – always creates a regular user account."""
    with get_conn() as conn:
        exists = conn.execute(
            "SELECT id FROM users WHERE username=? OR email=?",
            (body.username, body.email),
        ).fetchone()
        if exists:
            raise HTTPException(status.HTTP_409_CONFLICT, "Username or email already taken")
        cur = conn.execute(
            "INSERT INTO users (username, email, full_name, hashed_pw, role) VALUES (?,?,?,?,?)",
            (body.username, body.email, body.full_name, hash_password(body.password), "user"),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone()
    return UserOut(**dict(row))


@router.get("/", response_model=List[UserOut])
def list_users(_: dict = Depends(require_admin)):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    return [UserOut(**dict(r)) for r in rows]


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin" and current_user["id"] != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not row:
        raise HTTPException(404, "User not found")
    return UserOut(**dict(row))


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: UserUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin" and current_user["id"] != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if "password" in updates:
        updates["hashed_pw"] = hash_password(updates.pop("password"))
    # Only admin can change roles
    if "role" in updates and current_user["role"] != "admin":
        del updates["role"]
    if not updates:
        with get_conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return UserOut(**dict(row))
    set_clause = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [user_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE users SET {set_clause} WHERE id=?", vals)
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return UserOut(**dict(row))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, current_user: dict = Depends(require_admin)):
    if user_id == current_user["id"]:
        raise HTTPException(400, "Cannot delete yourself")
    with get_conn() as conn:
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
