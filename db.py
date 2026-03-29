"""SQLite database layer for WaitlistKit."""

import sqlite3
import os
from datetime import datetime, timezone
from contextlib import contextmanager

DB_PATH = os.environ.get("WAITLIST_DB_PATH", "/data/waitlist-kit/waitlist.db")


def _ensure_dir():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


@contextmanager
def get_db():
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS waitlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                tagline TEXT DEFAULT '',
                description TEXT DEFAULT '',
                color_theme TEXT DEFAULT 'gradient',
                redirect_url TEXT DEFAULT '',
                api_key TEXT NOT NULL,
                max_signups INTEGER DEFAULT 500,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS signups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                waitlist_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                name TEXT DEFAULT '',
                referral_code TEXT UNIQUE NOT NULL,
                referred_by TEXT DEFAULT NULL,
                position INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (waitlist_id) REFERENCES waitlists(id) ON DELETE CASCADE,
                UNIQUE(waitlist_id, email)
            );

            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_signup_id INTEGER NOT NULL,
                referee_signup_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (referrer_signup_id) REFERENCES signups(id) ON DELETE CASCADE,
                FOREIGN KEY (referee_signup_id) REFERENCES signups(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_signups_waitlist ON signups(waitlist_id);
            CREATE INDEX IF NOT EXISTS idx_signups_email ON signups(email);
            CREATE INDEX IF NOT EXISTS idx_signups_referral_code ON signups(referral_code);
            CREATE INDEX IF NOT EXISTS idx_signups_referred_by ON signups(referred_by);
            CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_signup_id);
        """)


# --- Waitlist CRUD ---

def create_waitlist(name: str, tagline: str = "", description: str = "",
                    color_theme: str = "gradient", redirect_url: str = "",
                    api_key: str = "") -> dict:
    import re
    import secrets
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    if not api_key:
        api_key = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        # Ensure slug uniqueness
        existing = conn.execute("SELECT id FROM waitlists WHERE slug=?", (slug,)).fetchone()
        if existing:
            slug = f"{slug}-{secrets.token_hex(3)}"

        cur = conn.execute(
            "INSERT INTO waitlists (slug, name, tagline, description, color_theme, redirect_url, api_key, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (slug, name, tagline, description, color_theme, redirect_url, api_key, now)
        )
        return {
            "id": cur.lastrowid, "slug": slug, "name": name, "tagline": tagline,
            "description": description, "color_theme": color_theme,
            "redirect_url": redirect_url, "api_key": api_key, "created_at": now
        }


def get_waitlist(waitlist_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM waitlists WHERE id=?", (waitlist_id,)).fetchone()
        return dict(row) if row else None


def get_waitlist_by_slug(slug: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM waitlists WHERE slug=?", (slug,)).fetchone()
        return dict(row) if row else None


def list_waitlists() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM waitlists ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]


# --- Signup CRUD ---

def create_signup(waitlist_id: int, email: str, name: str = "",
                  referred_by: str | None = None) -> dict:
    import secrets
    referral_code = secrets.token_urlsafe(8)
    now = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        # Check waitlist exists
        wl = conn.execute("SELECT * FROM waitlists WHERE id=?", (waitlist_id,)).fetchone()
        if not wl:
            raise ValueError("Waitlist not found")

        # Check signup limit
        count = conn.execute(
            "SELECT COUNT(*) as c FROM signups WHERE waitlist_id=?", (waitlist_id,)
        ).fetchone()["c"]
        if count >= wl["max_signups"]:
            raise ValueError("Waitlist is full")

        # Check duplicate
        existing = conn.execute(
            "SELECT * FROM signups WHERE waitlist_id=? AND email=?",
            (waitlist_id, email)
        ).fetchone()
        if existing:
            return dict(existing)

        position = count + 1

        # Validate referral code
        referrer_id = None
        if referred_by:
            referrer = conn.execute(
                "SELECT id FROM signups WHERE referral_code=? AND waitlist_id=?",
                (referred_by, waitlist_id)
            ).fetchone()
            if referrer:
                referrer_id = referrer["id"]

        cur = conn.execute(
            "INSERT INTO signups (waitlist_id, email, name, referral_code, referred_by, position, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (waitlist_id, email, name, referral_code, referred_by, position, now)
        )
        signup_id = cur.lastrowid

        # Record referral
        if referrer_id:
            conn.execute(
                "INSERT INTO referrals (referrer_signup_id, referee_signup_id, created_at) VALUES (?, ?, ?)",
                (referrer_id, signup_id, now)
            )

        return {
            "id": signup_id, "waitlist_id": waitlist_id, "email": email,
            "name": name, "referral_code": referral_code, "referred_by": referred_by,
            "position": position, "created_at": now
        }


def get_signups(waitlist_id: int, limit: int = 100, offset: int = 0) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM signups WHERE waitlist_id=? ORDER BY position ASC LIMIT ? OFFSET ?",
            (waitlist_id, limit, offset)
        ).fetchall()
        return [dict(r) for r in rows]


def get_signup_by_email(waitlist_id: int, email: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM signups WHERE waitlist_id=? AND email=?",
            (waitlist_id, email)
        ).fetchone()
        return dict(row) if row else None


def get_effective_position(signup_id: int) -> int:
    """Position = base position - (referral_count * 5). Min 1."""
    with get_db() as conn:
        signup = conn.execute("SELECT * FROM signups WHERE id=?", (signup_id,)).fetchone()
        if not signup:
            return 0
        ref_count = conn.execute(
            "SELECT COUNT(*) as c FROM referrals WHERE referrer_signup_id=?",
            (signup_id,)
        ).fetchone()["c"]
        effective = signup["position"] - (ref_count * 5)
        return max(1, effective)


def get_referral_count(signup_id: int) -> int:
    with get_db() as conn:
        return conn.execute(
            "SELECT COUNT(*) as c FROM referrals WHERE referrer_signup_id=?",
            (signup_id,)
        ).fetchone()["c"]


# --- Stats ---

def get_waitlist_stats(waitlist_id: int) -> dict:
    with get_db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) as c FROM signups WHERE waitlist_id=?", (waitlist_id,)
        ).fetchone()["c"]

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_count = conn.execute(
            "SELECT COUNT(*) as c FROM signups WHERE waitlist_id=? AND created_at LIKE ?",
            (waitlist_id, f"{today}%")
        ).fetchone()["c"]

        referred_count = conn.execute(
            "SELECT COUNT(*) as c FROM signups WHERE waitlist_id=? AND referred_by IS NOT NULL AND referred_by != ''",
            (waitlist_id,)
        ).fetchone()["c"]

        referral_rate = (referred_count / total * 100) if total > 0 else 0

        # Top referrers
        top_referrers = conn.execute("""
            SELECT s.email, s.name, s.referral_code, COUNT(r.id) as referral_count
            FROM signups s
            JOIN referrals r ON r.referrer_signup_id = s.id
            WHERE s.waitlist_id = ?
            GROUP BY s.id
            ORDER BY referral_count DESC
            LIMIT 10
        """, (waitlist_id,)).fetchall()

        return {
            "total_signups": total,
            "today_signups": today_count,
            "referred_signups": referred_count,
            "referral_rate": round(referral_rate, 1),
            "top_referrers": [dict(r) for r in top_referrers]
        }


def get_leaderboard(waitlist_id: int, limit: int = 20) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("""
            SELECT s.id, s.email, s.name, s.referral_code, s.position,
                   COALESCE(ref_counts.cnt, 0) as referral_count,
                   MAX(1, s.position - COALESCE(ref_counts.cnt, 0) * 5) as effective_position
            FROM signups s
            LEFT JOIN (
                SELECT referrer_signup_id, COUNT(*) as cnt
                FROM referrals GROUP BY referrer_signup_id
            ) ref_counts ON ref_counts.referrer_signup_id = s.id
            WHERE s.waitlist_id = ?
            ORDER BY effective_position ASC
            LIMIT ?
        """, (waitlist_id, limit)).fetchall()
        return [dict(r) for r in rows]
