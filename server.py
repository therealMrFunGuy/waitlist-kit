"""WaitlistKit — FastAPI REST API server."""

import csv
import io
import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Header, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from pydantic import BaseModel, EmailStr

import db
from landing import render_landing_page, render_confirmation_page, THEMES
from referrals import get_referral_link, get_referral_stats, get_waitlist_leaderboard, calculate_viral_coefficient
from email_notify import send_welcome_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("waitlistkit")

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8505")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    logger.info("WaitlistKit started")
    yield


app = FastAPI(
    title="WaitlistKit",
    description="Launch page + viral waitlist + analytics for pre-launch products",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic Models ---

class WaitlistCreate(BaseModel):
    name: str
    tagline: str = ""
    description: str = ""
    color_theme: str = "gradient"
    redirect_url: str = ""

class SignupCreate(BaseModel):
    email: EmailStr
    name: str = ""
    referral_code: str = ""


# --- Auth helper ---

def verify_api_key(waitlist_id: int, api_key: str):
    wl = db.get_waitlist(waitlist_id)
    if not wl:
        raise HTTPException(status_code=404, detail="Waitlist not found")
    if wl["api_key"] != api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return wl


# --- Waitlist endpoints ---

@app.post("/waitlists")
async def create_waitlist(data: WaitlistCreate):
    if data.color_theme not in THEMES:
        raise HTTPException(status_code=400, detail=f"Invalid theme. Choose from: {list(THEMES.keys())}")
    wl = db.create_waitlist(
        name=data.name, tagline=data.tagline, description=data.description,
        color_theme=data.color_theme, redirect_url=data.redirect_url
    )
    return wl


@app.get("/waitlists")
async def list_waitlists():
    return db.list_waitlists()


@app.get("/waitlists/{waitlist_id}")
async def get_waitlist(waitlist_id: int):
    wl = db.get_waitlist(waitlist_id)
    if not wl:
        raise HTTPException(status_code=404, detail="Waitlist not found")
    stats = db.get_waitlist_stats(waitlist_id)
    return {**wl, "stats": stats}


@app.post("/waitlists/{waitlist_id}/signup")
async def signup(waitlist_id: int, data: SignupCreate):
    try:
        signup = db.create_signup(
            waitlist_id=waitlist_id, email=data.email,
            name=data.name, referred_by=data.referral_code or None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    wl = db.get_waitlist(waitlist_id)
    effective_pos = db.get_effective_position(signup["id"])
    ref_link = get_referral_link(wl["slug"], signup["referral_code"], BASE_URL)

    # Send welcome email (non-blocking, best-effort)
    try:
        send_welcome_email(
            to_email=signup["email"], waitlist_name=wl["name"],
            position=effective_pos, referral_link=ref_link, tagline=wl.get("tagline", "")
        )
    except Exception as e:
        logger.warning(f"Email send failed: {e}")

    return {
        **signup,
        "effective_position": effective_pos,
        "referral_link": ref_link,
    }


@app.get("/waitlists/{waitlist_id}/signups")
async def list_signups(waitlist_id: int, limit: int = 100, offset: int = 0,
                       x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required (X-Api-Key header)")
    verify_api_key(waitlist_id, x_api_key)
    return db.get_signups(waitlist_id, limit, offset)


@app.get("/waitlists/{waitlist_id}/stats")
async def get_stats(waitlist_id: int):
    wl = db.get_waitlist(waitlist_id)
    if not wl:
        raise HTTPException(status_code=404, detail="Waitlist not found")
    stats = db.get_waitlist_stats(waitlist_id)
    stats["viral_coefficient"] = calculate_viral_coefficient(waitlist_id)
    return stats


@app.get("/waitlists/{waitlist_id}/leaderboard")
async def leaderboard(waitlist_id: int, limit: int = 20):
    wl = db.get_waitlist(waitlist_id)
    if not wl:
        raise HTTPException(status_code=404, detail="Waitlist not found")
    return get_waitlist_leaderboard(waitlist_id, limit)


@app.get("/waitlists/{waitlist_id}/export")
async def export_signups(waitlist_id: int, x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    verify_api_key(waitlist_id, x_api_key)

    signups = db.get_signups(waitlist_id, limit=100000)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "email", "name", "referral_code", "referred_by", "position", "created_at"])
    writer.writeheader()
    for s in signups:
        writer.writerow({k: s.get(k, "") for k in writer.fieldnames})

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=waitlist_{waitlist_id}_export.csv"}
    )


# --- Public landing page ---

@app.get("/w/{slug}", response_class=HTMLResponse)
async def landing_page(slug: str, ref: str = ""):
    wl = db.get_waitlist_by_slug(slug)
    if not wl:
        raise HTTPException(status_code=404, detail="Waitlist not found")
    stats = db.get_waitlist_stats(wl["id"])
    html = render_landing_page(wl, stats, ref_code=ref)
    return HTMLResponse(content=html)


@app.post("/w/{slug}/join", response_class=HTMLResponse)
async def join_waitlist(slug: str, email: str = Form(...), name: str = Form(""),
                        ref: str = Form("")):
    """Handle form submission from landing page."""
    wl = db.get_waitlist_by_slug(slug)
    if not wl:
        raise HTTPException(status_code=404, detail="Waitlist not found")

    try:
        signup = db.create_signup(
            waitlist_id=wl["id"], email=email, name=name,
            referred_by=ref or None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    effective_pos = db.get_effective_position(signup["id"])
    ref_link = get_referral_link(slug, signup["referral_code"], BASE_URL)
    stats = db.get_waitlist_stats(wl["id"])

    # Send welcome email
    try:
        send_welcome_email(
            to_email=email, waitlist_name=wl["name"],
            position=effective_pos, referral_link=ref_link, tagline=wl.get("tagline", "")
        )
    except Exception as e:
        logger.warning(f"Email send failed: {e}")

    # If redirect URL is set, redirect
    if wl.get("redirect_url"):
        return RedirectResponse(url=wl["redirect_url"], status_code=303)

    html = render_confirmation_page(wl, signup, stats, ref_link, effective_pos)
    return HTMLResponse(content=html)


@app.get("/w/{slug}/status")
async def check_status(slug: str, email: str = Query(...)):
    wl = db.get_waitlist_by_slug(slug)
    if not wl:
        raise HTTPException(status_code=404, detail="Waitlist not found")

    signup = db.get_signup_by_email(wl["id"], email)
    if not signup:
        raise HTTPException(status_code=404, detail="Email not found on this waitlist")

    effective_pos = db.get_effective_position(signup["id"])
    ref_count = db.get_referral_count(signup["id"])
    total = db.get_waitlist_stats(wl["id"])["total_signups"]

    return {
        "email": email,
        "position": effective_pos,
        "total_signups": total,
        "referral_count": ref_count,
        "referral_code": signup["referral_code"],
        "referral_link": get_referral_link(slug, signup["referral_code"], BASE_URL),
    }


# --- Health ---

@app.get("/health")
async def health():
    return {"status": "ok", "service": "waitlistkit", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8505)
