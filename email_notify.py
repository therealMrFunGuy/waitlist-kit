"""Email notification system for WaitlistKit.

Supports SMTP and Resend API. Configure via environment variables:
- EMAIL_PROVIDER: "smtp" or "resend" (default: none/disabled)
- SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM
- RESEND_API_KEY, RESEND_FROM
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("waitlistkit.email")

EMAIL_PROVIDER = os.environ.get("EMAIL_PROVIDER", "")
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM = os.environ.get("RESEND_FROM", "WaitlistKit <noreply@waitlistkit.dev>")


def _build_welcome_html(waitlist_name: str, position: int, referral_link: str, tagline: str = "") -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 560px; margin: 0 auto; padding: 40px 20px; color: #1a1a2e;">
  <div style="text-align: center; margin-bottom: 32px;">
    <h1 style="font-size: 24px; margin: 0;">{waitlist_name}</h1>
    {f'<p style="color: #666; margin-top: 8px;">{tagline}</p>' if tagline else ''}
  </div>
  <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 32px; color: white; text-align: center; margin-bottom: 24px;">
    <p style="font-size: 18px; margin: 0 0 8px 0;">You're in!</p>
    <p style="font-size: 48px; font-weight: 700; margin: 0;">#{position}</p>
    <p style="font-size: 14px; opacity: 0.9; margin: 8px 0 0 0;">in line</p>
  </div>
  <div style="background: #f8f9fa; border-radius: 12px; padding: 24px; text-align: center; margin-bottom: 24px;">
    <p style="font-size: 16px; font-weight: 600; margin: 0 0 8px 0;">Move up the list!</p>
    <p style="color: #666; font-size: 14px; margin: 0 0 16px 0;">Each referral moves you up 5 spots.</p>
    <div style="background: white; border: 2px dashed #667eea; border-radius: 8px; padding: 12px; word-break: break-all;">
      <a href="{referral_link}" style="color: #667eea; text-decoration: none; font-size: 14px;">{referral_link}</a>
    </div>
  </div>
  <p style="color: #999; font-size: 12px; text-align: center;">Sent by WaitlistKit</p>
</body>
</html>"""


def send_welcome_email(to_email: str, waitlist_name: str, position: int,
                       referral_link: str, tagline: str = "") -> bool:
    """Send a welcome email after signup. Returns True if sent, False if skipped/failed."""
    if not EMAIL_PROVIDER:
        logger.info(f"Email disabled, skipping welcome to {to_email}")
        return False

    html = _build_welcome_html(waitlist_name, position, referral_link, tagline)
    subject = f"You're #{position} on the {waitlist_name} waitlist!"

    try:
        if EMAIL_PROVIDER == "smtp":
            return _send_smtp(to_email, subject, html)
        elif EMAIL_PROVIDER == "resend":
            return _send_resend(to_email, subject, html)
        else:
            logger.warning(f"Unknown email provider: {EMAIL_PROVIDER}")
            return False
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def _send_smtp(to: str, subject: str, html: str) -> bool:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_FROM, to, msg.as_string())
    logger.info(f"SMTP email sent to {to}")
    return True


def _send_resend(to: str, subject: str, html: str) -> bool:
    import urllib.request
    import json

    data = json.dumps({
        "from": RESEND_FROM,
        "to": [to],
        "subject": subject,
        "html": html
    }).encode()

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=data,
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        logger.info(f"Resend email sent to {to}: {result.get('id', 'ok')}")
        return True
