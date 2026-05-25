from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List
from app.schemas import ExpenseCreate, ExpenseUpdate, ExpenseOut, ExpenseSummary
from app.database import get_conn
from app.dependencies import get_current_user, require_admin

router = APIRouter()


def _row_to_out(row) -> dict:
    return dict(row)


@router.get("/", response_model=List[ExpenseOut])
def list_expenses(
    category: Optional[str] = None,
    month: Optional[str] = None,       # YYYY-MM
    user_id: Optional[int] = None,     # admin only filter
    limit: int = Query(200, le=500),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
):
    q = """
        SELECT e.*, u.username, u.full_name
        FROM expenses e JOIN users u ON e.user_id = u.id
        WHERE 1=1
    """
    params = []

    # Non-admins only see their own
    if current_user["role"] != "admin":
        q += " AND e.user_id = ?"
        params.append(current_user["id"])
    elif user_id:
        q += " AND e.user_id = ?"
        params.append(user_id)

    if category:
        q += " AND e.category = ?"
        params.append(category)
    if month:
        q += " AND strftime('%Y-%m', e.date) = ?"
        params.append(month)

    q += " ORDER BY e.date DESC, e.id DESC LIMIT ? OFFSET ?"
    params += [limit, offset]

    with get_conn() as conn:
        rows = conn.execute(q, params).fetchall()
    return [dict(r) for r in rows]


@router.get("/summary", response_model=ExpenseSummary)
def summary(
    month: Optional[str] = None,
    user_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
):
    base = "FROM expenses e WHERE 1=1"
    params = []

    if current_user["role"] != "admin":
        base += " AND e.user_id = ?"
        params.append(current_user["id"])
    elif user_id:
        base += " AND e.user_id = ?"
        params.append(user_id)

    if month:
        base += " AND strftime('%Y-%m', e.date) = ?"
        params.append(month)

    with get_conn() as conn:
        total_row = conn.execute(f"SELECT COALESCE(SUM(amount),0) as t, COUNT(*) as c {base}", params).fetchone()
        cat_rows  = conn.execute(f"SELECT category, COALESCE(SUM(amount),0) as s {base} GROUP BY category", params).fetchall()
        month_rows= conn.execute(
            f"SELECT strftime('%Y-%m', e.date) as m, COALESCE(SUM(amount),0) as s {base} GROUP BY m ORDER BY m",
            params,
        ).fetchall()

    return ExpenseSummary(
        total=round(total_row["t"], 2),
        count=total_row["c"],
        by_category={r["category"]: round(r["s"], 2) for r in cat_rows},
        by_month={r["m"]: round(r["s"], 2) for r in month_rows},
    )


@router.post("/", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(body: ExpenseCreate, current_user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO expenses (user_id, amount, category, description, date) VALUES (?,?,?,?,?)",
            (current_user["id"], body.amount, body.category, body.description, body.date),
        )
        conn.commit()
        row = conn.execute(
            "SELECT e.*, u.username, u.full_name FROM expenses e JOIN users u ON e.user_id=u.id WHERE e.id=?",
            (cur.lastrowid,),
        ).fetchone()
    return dict(row)


@router.put("/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: int, body: ExpenseUpdate, current_user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM expenses WHERE id=?", (expense_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Expense not found")
        if current_user["role"] != "admin" and row["user_id"] != current_user["id"]:
            raise HTTPException(403, "Not your expense")

        updates = {k: v for k, v in body.model_dump().items() if v is not None}
        if updates:
            updates["updated_at"] = "datetime('now')"
            set_clause = ", ".join(
                f"{k} = datetime('now')" if k == "updated_at" else f"{k} = ?"
                for k in updates
            )
            vals = [v for k, v in updates.items() if k != "updated_at"]
            vals.append(expense_id)
            conn.execute(f"UPDATE expenses SET {set_clause} WHERE id=?", vals)
            conn.commit()

        updated = conn.execute(
            "SELECT e.*, u.username, u.full_name FROM expenses e JOIN users u ON e.user_id=u.id WHERE e.id=?",
            (expense_id,),
        ).fetchone()
    return dict(updated)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, current_user: dict = Depends(get_current_user)):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM expenses WHERE id=?", (expense_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Expense not found")
        if current_user["role"] != "admin" and row["user_id"] != current_user["id"]:
            raise HTTPException(403, "Not your expense")
        conn.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        conn.commit()
