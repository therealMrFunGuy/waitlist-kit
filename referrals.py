"""Referral tracking system for WaitlistKit."""

from db import get_db, get_referral_count, get_effective_position, get_leaderboard


def get_referral_link(slug: str, referral_code: str, base_url: str = "") -> str:
    """Generate a full referral link."""
    if not base_url:
        base_url = "http://localhost:8430"
    return f"{base_url}/w/{slug}?ref={referral_code}"


def get_referral_stats(signup_id: int) -> dict:
    """Get detailed referral stats for a signup."""
    with get_db() as conn:
        signup = conn.execute("SELECT * FROM signups WHERE id=?", (signup_id,)).fetchone()
        if not signup:
            return {}

        ref_count = get_referral_count(signup_id)
        effective_pos = get_effective_position(signup_id)

        # Get list of people they referred
        referred = conn.execute("""
            SELECT s.email, s.name, s.created_at
            FROM referrals r
            JOIN signups s ON s.id = r.referee_signup_id
            WHERE r.referrer_signup_id = ?
            ORDER BY r.created_at DESC
        """, (signup_id,)).fetchall()

        return {
            "signup_id": signup_id,
            "email": signup["email"],
            "referral_code": signup["referral_code"],
            "base_position": signup["position"],
            "effective_position": effective_pos,
            "positions_gained": signup["position"] - effective_pos,
            "referral_count": ref_count,
            "referred_users": [dict(r) for r in referred]
        }


def get_waitlist_leaderboard(waitlist_id: int, limit: int = 20) -> list[dict]:
    """Get the referral leaderboard for a waitlist."""
    return get_leaderboard(waitlist_id, limit)


def calculate_viral_coefficient(waitlist_id: int) -> float:
    """Calculate the viral coefficient (K-factor) for a waitlist.
    K = invites_sent_per_user * conversion_rate
    Here we approximate: K = total_referrals / total_signups
    """
    with get_db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) as c FROM signups WHERE waitlist_id=?", (waitlist_id,)
        ).fetchone()["c"]

        referred = conn.execute(
            "SELECT COUNT(*) as c FROM signups WHERE waitlist_id=? AND referred_by IS NOT NULL AND referred_by != ''",
            (waitlist_id,)
        ).fetchone()["c"]

        if total == 0:
            return 0.0
        return round(referred / total, 3)
