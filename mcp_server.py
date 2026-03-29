"""WaitlistKit MCP Server — tools for managing waitlists via MCP protocol."""

import json
import os
import sys

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
import db
from referrals import get_referral_link, calculate_viral_coefficient

mcp = FastMCP(
    "waitlistkit",
    description="Launch page + viral waitlist + analytics for pre-launch products",
)

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8430")


@mcp.tool()
def create_waitlist(name: str, tagline: str = "", description: str = "",
                    color_theme: str = "gradient") -> str:
    """Create a new waitlist with a landing page.

    Args:
        name: Name of the product/waitlist
        tagline: Short tagline shown on the landing page
        description: Longer description for the landing page
        color_theme: Theme for the landing page (minimal, gradient, dark, startup)

    Returns:
        JSON with waitlist details including slug, API key, and landing page URL
    """
    db.init_db()
    valid_themes = ["minimal", "gradient", "dark", "startup"]
    if color_theme not in valid_themes:
        return json.dumps({"error": f"Invalid theme. Choose from: {valid_themes}"})

    wl = db.create_waitlist(
        name=name, tagline=tagline, description=description,
        color_theme=color_theme
    )
    wl["landing_page_url"] = f"{BASE_URL}/w/{wl['slug']}"
    return json.dumps(wl, indent=2)


@mcp.tool()
def get_waitlist_stats(waitlist_id: int) -> str:
    """Get signup counts, referral stats, and viral coefficient for a waitlist.

    Args:
        waitlist_id: The waitlist ID

    Returns:
        JSON with total signups, today's signups, referral stats, top referrers, and viral coefficient
    """
    db.init_db()
    wl = db.get_waitlist(waitlist_id)
    if not wl:
        return json.dumps({"error": "Waitlist not found"})

    stats = db.get_waitlist_stats(waitlist_id)
    stats["viral_coefficient"] = calculate_viral_coefficient(waitlist_id)
    stats["waitlist_name"] = wl["name"]
    stats["landing_page_url"] = f"{BASE_URL}/w/{wl['slug']}"
    return json.dumps(stats, indent=2)


@mcp.tool()
def export_signups(waitlist_id: int) -> str:
    """Export all signups for a waitlist as JSON.

    Args:
        waitlist_id: The waitlist ID

    Returns:
        JSON array of all signups with email, name, referral code, position, and timestamps
    """
    db.init_db()
    wl = db.get_waitlist(waitlist_id)
    if not wl:
        return json.dumps({"error": "Waitlist not found"})

    signups = db.get_signups(waitlist_id, limit=100000)
    # Enrich with effective positions
    enriched = []
    for s in signups:
        s["effective_position"] = db.get_effective_position(s["id"])
        s["referral_count"] = db.get_referral_count(s["id"])
        enriched.append(s)

    return json.dumps({
        "waitlist": wl["name"],
        "total": len(enriched),
        "signups": enriched
    }, indent=2)


@mcp.tool()
def check_position(waitlist_id: int, email: str) -> str:
    """Check someone's position on a waitlist by email.

    Args:
        waitlist_id: The waitlist ID
        email: The email address to look up

    Returns:
        JSON with position, referral count, referral link, and total waitlist size
    """
    db.init_db()
    wl = db.get_waitlist(waitlist_id)
    if not wl:
        return json.dumps({"error": "Waitlist not found"})

    signup = db.get_signup_by_email(waitlist_id, email)
    if not signup:
        return json.dumps({"error": "Email not found on this waitlist"})

    effective_pos = db.get_effective_position(signup["id"])
    ref_count = db.get_referral_count(signup["id"])
    total = db.get_waitlist_stats(waitlist_id)["total_signups"]
    ref_link = get_referral_link(wl["slug"], signup["referral_code"], BASE_URL)

    return json.dumps({
        "email": email,
        "name": signup["name"],
        "base_position": signup["position"],
        "effective_position": effective_pos,
        "positions_gained": signup["position"] - effective_pos,
        "referral_count": ref_count,
        "referral_link": ref_link,
        "total_signups": total,
    }, indent=2)


@mcp.tool()
def list_waitlists() -> str:
    """List all waitlists with their basic info and signup counts.

    Returns:
        JSON array of all waitlists
    """
    db.init_db()
    waitlists = db.list_waitlists()
    for wl in waitlists:
        stats = db.get_waitlist_stats(wl["id"])
        wl["total_signups"] = stats["total_signups"]
        wl["landing_page_url"] = f"{BASE_URL}/w/{wl['slug']}"
    return json.dumps(waitlists, indent=2)


if __name__ == "__main__":
    mcp.run()
