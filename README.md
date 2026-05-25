# Ledger — Expense Tracker

A full-stack personal finance app built with **FastAPI** (Python) + **SQLite** + vanilla HTML/CSS/JS frontend.

---

## Project structure

```
expense-tracker/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, serves frontend
│   ├── database.py      # SQLite setup & seed data
│   ├── auth_utils.py    # JWT + password hashing
│   ├── schemas.py       # Pydantic models
│   ├── dependencies.py  # Auth middleware / DI
│   └── routers/
│       ├── auth.py      # POST /api/auth/login, GET /api/auth/me
│       ├── expenses.py  # CRUD /api/expenses/
│       └── users.py     # CRUD /api/users/
├── frontend/
│   └── index.html       # Single-page app
├── run.py
└── requirements.txt
```

---

## Quick start

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python run.py
```

Then open **http://localhost:8000** in your browser.

---

## Demo accounts

| Username | Password   | Role  |
|----------|------------|-------|
| admin    | admin123   | Admin |
| alice    | alice123   | User  |
| bob      | bob123     | User  |

---

## Features

### Auth
- JWT-based login / logout
- Public registration (creates regular user)
- Sessions persisted in `localStorage` — survives page refresh
- Switch accounts by signing out and back in

### Regular users
- View own dashboard: total spend, category breakdown, monthly bar chart
- Add / edit / delete expenses
- Filter by category or month

### Admin
- Dashboard shows **all users' data** combined
- Admin panel: User cards (join date, expense count, total spend)
- View, edit, delete **any** expense
- Delete users (cascades to their expenses)

### Data
- SQLite database (`expense_tracker.db`) created automatically on first run
- Each user's data is fully isolated at the API level
- All amounts stored as floats; currency formatted in UI

---

## API endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/auth/login | Public | Returns JWT |
| GET  | /api/auth/me | User | Current user info |
| POST | /api/users/register | Public | Create account |
| GET  | /api/users/ | Admin | List all users |
| PUT  | /api/users/{id} | User/Admin | Update profile |
| DELETE | /api/users/{id} | Admin | Delete user |
| GET  | /api/expenses/ | User | List expenses (filtered) |
| GET  | /api/expenses/summary | User | Aggregated stats |
| POST | /api/expenses/ | User | Create expense |
| PUT  | /api/expenses/{id} | User/Admin | Update expense |
| DELETE | /api/expenses/{id} | User/Admin | Delete expense |

Interactive API docs available at **http://localhost:8000/docs**

---

## Production notes

- Replace `SECRET_KEY` in `auth_utils.py` with a long random string (or set `SECRET_KEY` env var)
- Swap the HMAC-SHA256 password hashing for `passlib[bcrypt]` for stronger security
- Use PostgreSQL instead of SQLite for multi-process deployments
