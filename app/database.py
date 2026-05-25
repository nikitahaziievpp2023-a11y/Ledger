import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "expense_tracker.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                username  TEXT UNIQUE NOT NULL,
                email     TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                hashed_pw TEXT NOT NULL,
                role      TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                amount      REAL NOT NULL,
                category    TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                date        TEXT NOT NULL,
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)

        # Seed demo users if none exist
        row = conn.execute("SELECT COUNT(*) as n FROM users").fetchone()
        if row["n"] == 0:
            from app.auth_utils import hash_password
            seed_users = [
                ("admin",  "admin@example.com",  "Admin",       hash_password("admin123"),  "admin"),
                ("alice",  "alice@example.com",  "Alice Walker", hash_password("alice123"), "user"),
                ("bob",    "bob@example.com",    "Bob Smith",    hash_password("bob123"),   "user"),
            ]
            conn.executemany(
                "INSERT INTO users (username, email, full_name, hashed_pw, role) VALUES (?,?,?,?,?)",
                seed_users,
            )
            conn.commit()

            # Seed demo expenses
            alice_id = conn.execute("SELECT id FROM users WHERE username='alice'").fetchone()["id"]
            bob_id   = conn.execute("SELECT id FROM users WHERE username='bob'").fetchone()["id"]
            seed_expenses = [
                (alice_id, 42.50,  "food",          "Weekly groceries",        "2025-04-28"),
                (alice_id, 120.00, "transport",     "Monthly bus pass",        "2025-04-01"),
                (alice_id, 850.00, "housing",       "Rent",                    "2025-04-01"),
                (alice_id,  18.90, "entertainment", "Netflix subscription",    "2025-04-05"),
                (alice_id,  65.00, "health",        "Pharmacy",                "2025-04-12"),
                (alice_id,  33.00, "food",          "Restaurant dinner",       "2025-05-02"),
                (alice_id,  14.50, "food",          "Coffee & croissant",      "2025-05-08"),
                (bob_id,   200.00, "shopping",      "New shoes",               "2025-04-20"),
                (bob_id,   950.00, "housing",       "Rent",                    "2025-04-01"),
                (bob_id,    55.00, "food",          "Groceries",               "2025-04-14"),
                (bob_id,    90.00, "utilities",     "Electricity bill",        "2025-04-10"),
                (bob_id,    35.00, "entertainment", "Cinema tickets",          "2025-04-22"),
            ]
            conn.executemany(
                "INSERT INTO expenses (user_id, amount, category, description, date) VALUES (?,?,?,?,?)",
                seed_expenses,
            )
            conn.commit()
