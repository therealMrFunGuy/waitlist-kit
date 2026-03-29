# WaitlistKit

Launch page + viral waitlist + analytics tool for pre-launch products.

## Features

- **Beautiful landing pages** — 4 themes (minimal, gradient, dark, startup), server-rendered, no build step
- **Viral referral system** — unique referral codes, position boosting (each referral = 5 spots up), leaderboard
- **Analytics** — signup counts, daily stats, referral breakdown, viral coefficient
- **MCP server** — manage waitlists from any MCP-compatible AI tool
- **Email notifications** — welcome emails via SMTP or Resend API
- **CSV export** — download signups for import into other tools
- **Zero dependencies frontend** — all inline CSS, no JavaScript frameworks

## Quick Start

```bash
# Docker
docker compose up -d

# Or local
pip install -r requirements.txt
python server.py
```

API at http://localhost:8430, landing pages at http://localhost:8430/w/{slug}

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /waitlists | Create waitlist |
| GET | /waitlists | List all |
| GET | /waitlists/{id} | Get details + stats |
| POST | /waitlists/{id}/signup | Sign up (email, name, referral_code) |
| GET | /waitlists/{id}/signups | List signups (API key required) |
| GET | /waitlists/{id}/stats | Stats + referral breakdown |
| GET | /waitlists/{id}/leaderboard | Referral leaderboard |
| GET | /waitlists/{id}/export | CSV export (API key required) |
| GET | /w/{slug} | Public landing page |
| POST | /w/{slug}/join | Form submit from landing page |
| GET | /w/{slug}/status?email=x | Check position |

## MCP Tools

- `create_waitlist` — create a new waitlist
- `get_waitlist_stats` — signup counts, referral stats
- `export_signups` — export all signups as JSON
- `check_position` — check position by email
- `list_waitlists` — list all waitlists

Run MCP server: `python mcp_server.py`
