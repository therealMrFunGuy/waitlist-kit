"""WaitlistKit — FastAPI REST API server."""

import csv
import io
import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Header, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from pydantic import BaseModel, EmailStr

from auth_client import require_auth
import db
from landing import render_landing_page, render_confirmation_page, THEMES
from referrals import get_referral_link, get_referral_stats, get_waitlist_leaderboard, calculate_viral_coefficient
from email_notify import send_welcome_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("waitlistkit")

AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:8499")
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


# --- Landing Page ---

LANDING_PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WaitlistKit — Launch Viral Waitlists in Seconds</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        html { scroll-behavior: smooth; }
        .code-block { background: #1e1e2e; border-radius: 0.5rem; }
        .code-block code { color: #cdd6f4; font-size: 0.85rem; }
        .kw { color: #cba6f7; } .str { color: #a6e3a1; } .cmt { color: #6c7086; }
    </style>
</head>
<body class="bg-white text-gray-900 antialiased">

<!-- Nav -->
<nav class="sticky top-0 z-50 bg-white/80 backdrop-blur border-b border-gray-100">
    <div class="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
        <a href="/" class="text-xl font-bold bg-gradient-to-r from-rose-500 to-pink-500 bg-clip-text text-transparent">WaitlistKit</a>
        <div class="hidden md:flex items-center gap-8 text-sm font-medium text-gray-600">
            <a href="#features" class="hover:text-rose-500 transition">Features</a>
            <a href="#pricing" class="hover:text-rose-500 transition">Pricing</a>
            <a href="#docs" class="hover:text-rose-500 transition">Docs</a>
            <a href="https://github.com/therealMrFunGuy/waitlist-kit" target="_blank" class="hover:text-rose-500 transition">GitHub</a>
        </div>
    </div>
</nav>

<!-- Hero -->
<section class="relative overflow-hidden">
    <div class="absolute inset-0 bg-gradient-to-br from-rose-50 via-pink-50 to-white"></div>
    <div class="relative max-w-4xl mx-auto px-6 py-24 md:py-36 text-center">
        <span class="inline-block px-3 py-1 mb-6 text-xs font-semibold tracking-wide uppercase rounded-full bg-rose-100 text-rose-600">Open Source</span>
        <h1 class="text-4xl md:text-6xl font-extrabold leading-tight tracking-tight">
            Launch <span class="bg-gradient-to-r from-rose-500 to-pink-500 bg-clip-text text-transparent">Viral Waitlists</span> in Seconds
        </h1>
        <p class="mt-6 text-lg md:text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            Built-in referral tracking, beautiful themed landing pages, real-time analytics, and first-class MCP integration. One API call to go from zero to waitlist.
        </p>
        <div class="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
            <a href="#docs" class="px-8 py-3 rounded-lg bg-gradient-to-r from-rose-500 to-pink-500 text-white font-semibold shadow-lg shadow-rose-200 hover:shadow-xl hover:shadow-rose-300 transition">Get Started</a>
            <a href="https://github.com/therealMrFunGuy/waitlist-kit" target="_blank" class="px-8 py-3 rounded-lg border border-gray-200 font-semibold hover:border-rose-300 hover:text-rose-500 transition">View on GitHub</a>
        </div>
    </div>
</section>

<!-- Code Examples -->
<section class="py-20 bg-gray-50" id="examples">
    <div class="max-w-5xl mx-auto px-6">
        <h2 class="text-3xl font-bold text-center mb-4">Up and Running in Minutes</h2>
        <p class="text-center text-gray-500 mb-12 max-w-xl mx-auto">A simple REST API. Use curl, any HTTP client, or connect via MCP.</p>
        <div class="grid md:grid-cols-2 gap-6">
            <div>
                <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Create a Waitlist</h3>
                <div class="code-block p-4 overflow-x-auto">
<pre><code><span class="cmt"># Create a new waitlist</span>
curl -X POST http://localhost:8505/waitlists \\
  -H <span class="str">"Content-Type: application/json"</span> \\
  -d <span class="str">'{"name": "My App", "tagline": "The future of X", "color_theme": "gradient"}'</span></code></pre>
                </div>
            </div>
            <div>
                <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Add a Signup</h3>
                <div class="code-block p-4 overflow-x-auto">
<pre><code><span class="cmt"># Sign someone up (with optional referral)</span>
curl -X POST http://localhost:8505/waitlists/1/signup \\
  -H <span class="str">"Content-Type: application/json"</span> \\
  -d <span class="str">'{"email": "user@example.com", "name": "Jane", "referral_code": "abc123"}'</span></code></pre>
                </div>
            </div>
            <div>
                <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Check Leaderboard</h3>
                <div class="code-block p-4 overflow-x-auto">
<pre><code><span class="cmt"># Top referrers</span>
curl http://localhost:8505/waitlists/1/leaderboard

<span class="cmt"># Export all signups as CSV</span>
curl -H <span class="str">"X-Api-Key: wk_..."</span> \\
  http://localhost:8505/waitlists/1/export</code></pre>
                </div>
            </div>
            <div>
                <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">MCP Config (claude_desktop_config.json)</h3>
                <div class="code-block p-4 overflow-x-auto">
<pre><code>{
  <span class="str">"mcpServers"</span>: {
    <span class="str">"waitlistkit"</span>: {
      <span class="str">"command"</span>: <span class="str">"uvx"</span>,
      <span class="str">"args"</span>: [<span class="str">"mcp-server-waitlistkit"</span>]
    }
  }
}</code></pre>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Features -->
<section class="py-20" id="features">
    <div class="max-w-5xl mx-auto px-6">
        <h2 class="text-3xl font-bold text-center mb-4">Everything You Need</h2>
        <p class="text-center text-gray-500 mb-12 max-w-xl mx-auto">From landing pages to analytics, WaitlistKit handles the full pre-launch funnel.</p>
        <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div class="rounded-xl border border-gray-100 p-6 hover:shadow-lg hover:border-rose-100 transition">
                <div class="w-10 h-10 rounded-lg bg-rose-100 flex items-center justify-center text-rose-500 font-bold text-lg mb-4">P</div>
                <h3 class="font-semibold mb-2">Landing Page Generator</h3>
                <p class="text-sm text-gray-500">4 built-in themes: gradient, minimal, bold, dark. Responsive, no-code pages created via API.</p>
            </div>
            <div class="rounded-xl border border-gray-100 p-6 hover:shadow-lg hover:border-rose-100 transition">
                <div class="w-10 h-10 rounded-lg bg-pink-100 flex items-center justify-center text-pink-500 font-bold text-lg mb-4">V</div>
                <h3 class="font-semibold mb-2">Viral Referrals</h3>
                <p class="text-sm text-gray-500">Every signup gets a unique referral link. Referrers move up the queue. Track viral coefficient in real time.</p>
            </div>
            <div class="rounded-xl border border-gray-100 p-6 hover:shadow-lg hover:border-rose-100 transition">
                <div class="w-10 h-10 rounded-lg bg-fuchsia-100 flex items-center justify-center text-fuchsia-500 font-bold text-lg mb-4">A</div>
                <h3 class="font-semibold mb-2">Analytics Dashboard</h3>
                <p class="text-sm text-gray-500">Signups over time, referral leaderboard, viral coefficient, and growth stats via a single endpoint.</p>
            </div>
            <div class="rounded-xl border border-gray-100 p-6 hover:shadow-lg hover:border-rose-100 transition">
                <div class="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center text-purple-500 font-bold text-lg mb-4">E</div>
                <h3 class="font-semibold mb-2">CSV Export</h3>
                <p class="text-sm text-gray-500">One-click export of all signups with referral data. API-key protected for security.</p>
            </div>
        </div>
    </div>
</section>

<!-- Pricing -->
<section class="py-20 bg-gray-50" id="pricing">
    <div class="max-w-5xl mx-auto px-6">
        <h2 class="text-3xl font-bold text-center mb-4">Simple Pricing</h2>
        <p class="text-center text-gray-500 mb-12 max-w-xl mx-auto">Start free, scale when you need to.</p>
        <div class="grid md:grid-cols-3 gap-6">
            <!-- Free -->
            <div class="rounded-xl border border-gray-200 bg-white p-8">
                <h3 class="text-lg font-semibold mb-1">Free</h3>
                <p class="text-3xl font-extrabold mb-1">$0</p>
                <p class="text-sm text-gray-400 mb-6">Forever</p>
                <ul class="space-y-3 text-sm text-gray-600 mb-8">
                    <li class="flex items-start gap-2"><span class="text-rose-400 mt-0.5">&#10003;</span> 1 waitlist</li>
                    <li class="flex items-start gap-2"><span class="text-rose-400 mt-0.5">&#10003;</span> 500 signups</li>
                    <li class="flex items-start gap-2"><span class="text-rose-400 mt-0.5">&#10003;</span> Basic themes</li>
                    <li class="flex items-start gap-2"><span class="text-rose-400 mt-0.5">&#10003;</span> Referral tracking</li>
                    <li class="flex items-start gap-2"><span class="text-rose-400 mt-0.5">&#10003;</span> CSV export</li>
                </ul>
                <a href="#docs" class="block text-center py-2.5 rounded-lg border border-gray-200 font-medium text-sm hover:border-rose-300 hover:text-rose-500 transition">Get Started</a>
            </div>
            <!-- Pro -->
            <div class="rounded-xl border-2 border-rose-400 bg-white p-8 relative shadow-lg shadow-rose-100">
                <span class="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-rose-500 text-white text-xs font-semibold rounded-full">Popular</span>
                <h3 class="text-lg font-semibold mb-1">Pro</h3>
                <p class="text-3xl font-extrabold mb-1">$10<span class="text-base font-normal text-gray-400">/mo</span></p>
                <p class="text-sm text-gray-400 mb-6">For growing products</p>
                <ul class="space-y-3 text-sm text-gray-600 mb-8">
                    <li class="flex items-start gap-2"><span class="text-rose-400 mt-0.5">&#10003;</span> Unlimited waitlists</li>
                    <li class="flex items-start gap-2"><span class="text-rose-400 mt-0.5">&#10003;</span> Unlimited signups</li>
                    <li class="flex items-start gap-2"><span class="text-rose-400 mt-0.5">&#10003;</span> Custom branding</li>
                    <li class="flex items-start gap-2"><span class="text-rose-400 mt-0.5">&#10003;</span> Priority support</li>
                    <li class="flex items-start gap-2"><span class="text-rose-400 mt-0.5">&#10003;</span> Webhook notifications</li>
                </ul>
                <a href="#docs" class="block text-center py-2.5 rounded-lg bg-gradient-to-r from-rose-500 to-pink-500 text-white font-medium text-sm shadow hover:shadow-lg transition">Start Free Trial</a>
            </div>
            <!-- Enterprise -->
            <div class="rounded-xl border border-gray-200 bg-white p-8">
                <h3 class="text-lg font-semibold mb-1">Enterprise</h3>
                <p class="text-3xl font-extrabold mb-1">Custom</p>
                <p class="text-sm text-gray-400 mb-6">For teams at scale</p>
                <ul class="space-y-3 text-sm text-gray-600 mb-8">
                    <li class="flex items-start gap-2"><span class="text-rose-400 mt-0.5">&#10003;</span> Everything in Pro</li>
                    <li class="flex items-start gap-2"><span class="text-rose-400 mt-0.5">&#10003;</span> White-label</li>
                    <li class="flex items-start gap-2"><span class="text-rose-400 mt-0.5">&#10003;</span> Custom domains</li>
                    <li class="flex items-start gap-2"><span class="text-rose-400 mt-0.5">&#10003;</span> SLA guarantee</li>
                    <li class="flex items-start gap-2"><span class="text-rose-400 mt-0.5">&#10003;</span> Dedicated support</li>
                </ul>
                <a href="mailto:hello@rjctdlabs.xyz" class="block text-center py-2.5 rounded-lg border border-gray-200 font-medium text-sm hover:border-rose-300 hover:text-rose-500 transition">Contact Us</a>
            </div>
        </div>
    </div>
</section>

<!-- API Reference -->
<section class="py-20" id="docs">
    <div class="max-w-4xl mx-auto px-6">
        <h2 class="text-3xl font-bold text-center mb-4">API Reference</h2>
        <p class="text-center text-gray-500 mb-12 max-w-xl mx-auto">Core endpoints to manage your waitlists programmatically.</p>
        <div class="space-y-4">
            <div class="rounded-xl border border-gray-100 p-5 hover:border-rose-100 transition">
                <div class="flex items-center gap-3 mb-2">
                    <span class="px-2 py-0.5 rounded text-xs font-bold bg-green-100 text-green-700">POST</span>
                    <code class="text-sm font-mono font-semibold">/waitlists</code>
                </div>
                <p class="text-sm text-gray-500">Create a new waitlist. Pass <code class="text-xs bg-gray-100 px-1 rounded">name</code>, <code class="text-xs bg-gray-100 px-1 rounded">tagline</code>, <code class="text-xs bg-gray-100 px-1 rounded">description</code>, <code class="text-xs bg-gray-100 px-1 rounded">color_theme</code> (gradient | minimal | bold | dark). Returns the waitlist object with <code class="text-xs bg-gray-100 px-1 rounded">api_key</code> and <code class="text-xs bg-gray-100 px-1 rounded">slug</code>.</p>
            </div>
            <div class="rounded-xl border border-gray-100 p-5 hover:border-rose-100 transition">
                <div class="flex items-center gap-3 mb-2">
                    <span class="px-2 py-0.5 rounded text-xs font-bold bg-green-100 text-green-700">POST</span>
                    <code class="text-sm font-mono font-semibold">/waitlists/{id}/signup</code>
                </div>
                <p class="text-sm text-gray-500">Add a signup to a waitlist. Pass <code class="text-xs bg-gray-100 px-1 rounded">email</code> (required), <code class="text-xs bg-gray-100 px-1 rounded">name</code>, and <code class="text-xs bg-gray-100 px-1 rounded">referral_code</code>. Returns position, referral link, and signup details.</p>
            </div>
            <div class="rounded-xl border border-gray-100 p-5 hover:border-rose-100 transition">
                <div class="flex items-center gap-3 mb-2">
                    <span class="px-2 py-0.5 rounded text-xs font-bold bg-blue-100 text-blue-700">GET</span>
                    <code class="text-sm font-mono font-semibold">/waitlists/{id}/stats</code>
                </div>
                <p class="text-sm text-gray-500">Get signup count, referral stats, daily growth, and viral coefficient for a waitlist.</p>
            </div>
            <div class="rounded-xl border border-gray-100 p-5 hover:border-rose-100 transition">
                <div class="flex items-center gap-3 mb-2">
                    <span class="px-2 py-0.5 rounded text-xs font-bold bg-blue-100 text-blue-700">GET</span>
                    <code class="text-sm font-mono font-semibold">/w/{slug}</code>
                </div>
                <p class="text-sm text-gray-500">Public landing page for your waitlist. Themed, responsive, with built-in signup form and referral tracking. Share this URL with your audience.</p>
            </div>
        </div>
        <p class="text-center text-sm text-gray-400 mt-8">Full interactive docs available at <a href="/docs" class="text-rose-500 hover:underline">/docs</a> (Swagger UI)</p>
    </div>
</section>

<!-- Footer -->
<footer class="border-t border-gray-100 py-12 bg-white">
    <div class="max-w-5xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6 text-sm text-gray-400">
        <span class="font-semibold bg-gradient-to-r from-rose-500 to-pink-500 bg-clip-text text-transparent">WaitlistKit</span>
        <div class="flex gap-6">
            <a href="https://github.com/therealMrFunGuy/waitlist-kit" target="_blank" class="hover:text-rose-500 transition">GitHub</a>
            <a href="https://pypi.org/project/mcp-server-waitlistkit/" target="_blank" class="hover:text-rose-500 transition">PyPI</a>
            <a href="/docs" class="hover:text-rose-500 transition">API Docs</a>
        </div>
        <span>Powered by <a href="https://rjctdlabs.xyz" target="_blank" class="text-rose-400 hover:text-rose-500 transition">rjctdlabs.xyz</a></span>
    </div>
</footer>

</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=LANDING_PAGE_HTML)


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
async def create_waitlist(data: WaitlistCreate, auth: dict = Depends(require_auth)):
    if data.color_theme not in THEMES:
        raise HTTPException(status_code=400, detail=f"Invalid theme. Choose from: {list(THEMES.keys())}")
    wl = db.create_waitlist(
        name=data.name, tagline=data.tagline, description=data.description,
        color_theme=data.color_theme, redirect_url=data.redirect_url
    )
    return wl


@app.get("/waitlists")
async def list_waitlists(auth: dict = Depends(require_auth)):
    return db.list_waitlists()


@app.get("/waitlists/{waitlist_id}")
async def get_waitlist(waitlist_id: int, auth: dict = Depends(require_auth)):
    wl = db.get_waitlist(waitlist_id)
    if not wl:
        raise HTTPException(status_code=404, detail="Waitlist not found")
    stats = db.get_waitlist_stats(waitlist_id)
    return {**wl, "stats": stats}


@app.post("/waitlists/{waitlist_id}/signup")
async def signup(waitlist_id: int, data: SignupCreate, auth: dict = Depends(require_auth)):
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
                       x_api_key: str = Header(None), auth: dict = Depends(require_auth)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required (X-Api-Key header)")
    verify_api_key(waitlist_id, x_api_key)
    return db.get_signups(waitlist_id, limit, offset)


@app.get("/waitlists/{waitlist_id}/stats")
async def get_stats(waitlist_id: int, auth: dict = Depends(require_auth)):
    wl = db.get_waitlist(waitlist_id)
    if not wl:
        raise HTTPException(status_code=404, detail="Waitlist not found")
    stats = db.get_waitlist_stats(waitlist_id)
    stats["viral_coefficient"] = calculate_viral_coefficient(waitlist_id)
    return stats


@app.get("/waitlists/{waitlist_id}/leaderboard")
async def leaderboard(waitlist_id: int, limit: int = 20, auth: dict = Depends(require_auth)):
    wl = db.get_waitlist(waitlist_id)
    if not wl:
        raise HTTPException(status_code=404, detail="Waitlist not found")
    return get_waitlist_leaderboard(waitlist_id, limit)


@app.get("/waitlists/{waitlist_id}/export")
async def export_signups(waitlist_id: int, x_api_key: str = Header(None), auth: dict = Depends(require_auth)):
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
