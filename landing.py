"""Landing page HTML generator for WaitlistKit.

Generates beautiful, server-rendered landing pages with inline CSS.
Themes: minimal, gradient, dark, startup
"""


def render_landing_page(waitlist: dict, stats: dict, ref_code: str = "") -> str:
    """Render the full landing page HTML for a waitlist."""
    theme = waitlist.get("color_theme", "gradient")
    renderer = THEMES.get(theme, _theme_gradient)
    return renderer(waitlist, stats, ref_code)


def render_confirmation_page(waitlist: dict, signup: dict, stats: dict,
                             referral_link: str, effective_position: int) -> str:
    """Render the post-signup confirmation page."""
    name = waitlist["name"]
    tagline = waitlist.get("tagline", "")
    total = stats["total_signups"]
    ref_count_text = "Share your link to move up the list. Each referral = 5 spots."

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>You're in! - {name}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
    min-height: 100vh;
    display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    color: #fff; padding: 20px;
  }}
  .card {{
    background: rgba(255,255,255,0.06);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 24px; padding: 48px; max-width: 520px; width: 100%;
    text-align: center;
  }}
  .checkmark {{
    width: 64px; height: 64px; border-radius: 50%;
    background: linear-gradient(135deg, #00c853, #64dd17);
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 24px; font-size: 32px;
  }}
  h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 8px; }}
  .tagline {{ color: rgba(255,255,255,0.6); font-size: 16px; margin-bottom: 32px; }}
  .position-box {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px; padding: 32px; margin-bottom: 32px;
  }}
  .position-label {{ font-size: 14px; text-transform: uppercase; letter-spacing: 2px; opacity: 0.8; }}
  .position-number {{ font-size: 64px; font-weight: 800; line-height: 1.1; }}
  .position-sub {{ font-size: 14px; opacity: 0.7; margin-top: 4px; }}
  .share-section {{
    background: rgba(255,255,255,0.05);
    border-radius: 16px; padding: 24px; margin-bottom: 24px;
  }}
  .share-section h3 {{ font-size: 16px; margin-bottom: 8px; }}
  .share-section p {{ font-size: 13px; color: rgba(255,255,255,0.5); margin-bottom: 16px; }}
  .ref-link {{
    background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15);
    border-radius: 10px; padding: 12px 16px; display: flex; align-items: center;
    gap: 8px; margin-bottom: 16px;
  }}
  .ref-link input {{
    flex: 1; background: none; border: none; color: #fff; font-size: 13px;
    outline: none; font-family: monospace;
  }}
  .ref-link button {{
    background: #667eea; color: white; border: none; border-radius: 6px;
    padding: 8px 16px; cursor: pointer; font-size: 13px; font-weight: 600;
    white-space: nowrap;
  }}
  .ref-link button:hover {{ background: #5a6fd6; }}
  .social-buttons {{ display: flex; gap: 10px; justify-content: center; }}
  .social-buttons a {{
    display: flex; align-items: center; gap: 6px;
    padding: 10px 18px; border-radius: 8px; text-decoration: none;
    font-size: 13px; font-weight: 600; color: white; transition: transform 0.15s;
  }}
  .social-buttons a:hover {{ transform: translateY(-1px); }}
  .btn-twitter {{ background: #1da1f2; }}
  .btn-linkedin {{ background: #0077b5; }}
  .people {{ font-size: 13px; color: rgba(255,255,255,0.4); margin-top: 16px; }}
</style>
</head>
<body>
<div class="card">
  <div class="checkmark">&#10003;</div>
  <h1>You're on the list!</h1>
  <p class="tagline">{tagline}</p>

  <div class="position-box">
    <div class="position-label">Your position</div>
    <div class="position-number">#{effective_position}</div>
    <div class="position-sub">out of {total} people</div>
  </div>

  <div class="share-section">
    <h3>Move up the line</h3>
    <p>{ref_count_text}</p>
    <div class="ref-link">
      <input type="text" value="{referral_link}" readonly id="refLink">
      <button onclick="navigator.clipboard.writeText(document.getElementById('refLink').value);this.textContent='Copied!'">Copy</button>
    </div>
    <div class="social-buttons">
      <a href="https://twitter.com/intent/tweet?text=I%20just%20joined%20the%20{name.replace(' ', '%20')}%20waitlist!%20Get%20early%20access%3A%20{referral_link}" target="_blank" class="btn-twitter">
        <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
        Share
      </a>
      <a href="https://www.linkedin.com/sharing/share-offsite/?url={referral_link}" target="_blank" class="btn-linkedin">
        <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
        Share
      </a>
    </div>
  </div>
  <p class="people">Join {total:,} others on the waitlist</p>
</div>
</body>
</html>"""


def _base_head(title: str, extra_style: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  {extra_style}
</style>
</head>"""


def _signup_form(slug: str, ref_code: str = "") -> str:
    ref_input = f'<input type="hidden" name="ref" value="{ref_code}">' if ref_code else ""
    return f"""
    <form method="POST" action="/w/{slug}/join" class="signup-form" id="signupForm">
      {ref_input}
      <div class="input-row">
        <input type="email" name="email" placeholder="your@email.com" required class="email-input" autocomplete="email">
        <button type="submit" class="submit-btn">Join Waitlist</button>
      </div>
      <input type="text" name="name" placeholder="Your name (optional)" class="name-input" autocomplete="name">
    </form>"""


def _theme_minimal(waitlist: dict, stats: dict, ref_code: str = "") -> str:
    name = waitlist["name"]
    tagline = waitlist.get("tagline", "")
    description = waitlist.get("description", "")
    total = stats["total_signups"]

    return _base_head(name, """
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    min-height: 100vh; display: flex; align-items: center; justify-content: center;
    background: #fafafa; color: #111; padding: 20px;
  }
  .container { max-width: 560px; width: 100%; text-align: center; }
  h1 { font-size: 42px; font-weight: 800; letter-spacing: -1px; margin-bottom: 12px; line-height: 1.1; }
  .tagline { font-size: 20px; color: #666; margin-bottom: 12px; font-weight: 400; }
  .description { font-size: 16px; color: #888; margin-bottom: 40px; line-height: 1.6; }
  .signup-form { margin-bottom: 24px; }
  .input-row { display: flex; gap: 8px; margin-bottom: 10px; }
  .email-input {
    flex: 1; padding: 16px 20px; border: 2px solid #e0e0e0; border-radius: 12px;
    font-size: 16px; outline: none; transition: border-color 0.2s;
  }
  .email-input:focus { border-color: #111; }
  .name-input {
    width: 100%; padding: 14px 20px; border: 2px solid #e0e0e0; border-radius: 12px;
    font-size: 15px; outline: none; transition: border-color 0.2s;
  }
  .name-input:focus { border-color: #111; }
  .submit-btn {
    padding: 16px 32px; background: #111; color: white; border: none;
    border-radius: 12px; font-size: 16px; font-weight: 700; cursor: pointer;
    transition: background 0.2s; white-space: nowrap;
  }
  .submit-btn:hover { background: #333; }
  .social-proof {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 10px 20px; background: white; border-radius: 100px;
    border: 1px solid #eee; font-size: 14px; color: #666;
  }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: #22c55e; }
  @media (max-width: 480px) {
    .input-row { flex-direction: column; }
    h1 { font-size: 32px; }
  }
  """) + f"""
<body>
<div class="container">
  <h1>{name}</h1>
  {"<p class='tagline'>" + tagline + "</p>" if tagline else ""}
  {"<p class='description'>" + description + "</p>" if description else ""}
  {_signup_form(waitlist['slug'], ref_code)}
  <div class="social-proof">
    <span class="dot"></span>
    <span><strong>{total:,}</strong> {"people have" if total != 1 else "person has"} joined</span>
  </div>
</div>
</body></html>"""


def _theme_gradient(waitlist: dict, stats: dict, ref_code: str = "") -> str:
    name = waitlist["name"]
    tagline = waitlist.get("tagline", "")
    description = waitlist.get("description", "")
    total = stats["total_signups"]

    return _base_head(name, """
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    min-height: 100vh; display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff; padding: 20px;
  }
  .container {
    max-width: 520px; width: 100%; text-align: center;
    background: rgba(255,255,255,0.08); backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.15); border-radius: 28px;
    padding: 56px 40px;
  }
  .badge {
    display: inline-block; padding: 6px 16px; background: rgba(255,255,255,0.15);
    border-radius: 100px; font-size: 13px; font-weight: 600;
    letter-spacing: 1px; text-transform: uppercase; margin-bottom: 20px;
  }
  h1 { font-size: 40px; font-weight: 800; letter-spacing: -0.5px; margin-bottom: 12px; line-height: 1.15; }
  .tagline { font-size: 18px; opacity: 0.85; margin-bottom: 12px; }
  .description { font-size: 15px; opacity: 0.65; margin-bottom: 36px; line-height: 1.6; }
  .signup-form { margin-bottom: 28px; }
  .input-row { display: flex; gap: 8px; margin-bottom: 10px; }
  .email-input {
    flex: 1; padding: 16px 20px; background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.25); border-radius: 14px;
    color: white; font-size: 16px; outline: none;
  }
  .email-input::placeholder { color: rgba(255,255,255,0.5); }
  .email-input:focus { border-color: rgba(255,255,255,0.6); background: rgba(255,255,255,0.18); }
  .name-input {
    width: 100%; padding: 14px 20px; background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.15); border-radius: 14px;
    color: white; font-size: 15px; outline: none;
  }
  .name-input::placeholder { color: rgba(255,255,255,0.4); }
  .name-input:focus { border-color: rgba(255,255,255,0.5); }
  .submit-btn {
    padding: 16px 32px; background: white; color: #764ba2; border: none;
    border-radius: 14px; font-size: 16px; font-weight: 700; cursor: pointer;
    transition: all 0.2s; white-space: nowrap;
  }
  .submit-btn:hover { transform: translateY(-1px); box-shadow: 0 8px 24px rgba(0,0,0,0.2); }
  .social-proof {
    display: inline-flex; align-items: center; gap: 8px;
    font-size: 14px; opacity: 0.7;
  }
  .avatars { display: flex; margin-right: 4px; }
  .avatar {
    width: 28px; height: 28px; border-radius: 50%; border: 2px solid rgba(255,255,255,0.3);
    margin-left: -8px; display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700;
  }
  .avatar:first-child { margin-left: 0; }
  .a1 { background: #ff6b6b; } .a2 { background: #ffd93d; color: #333; }
  .a3 { background: #6bcb77; } .a4 { background: #4d96ff; }
  @media (max-width: 480px) {
    .container { padding: 40px 24px; }
    .input-row { flex-direction: column; }
    h1 { font-size: 30px; }
  }
  """) + f"""
<body>
<div class="container">
  <span class="badge">Early Access</span>
  <h1>{name}</h1>
  {"<p class='tagline'>" + tagline + "</p>" if tagline else ""}
  {"<p class='description'>" + description + "</p>" if description else ""}
  {_signup_form(waitlist['slug'], ref_code)}
  <div class="social-proof">
    <div class="avatars">
      <div class="avatar a1">A</div>
      <div class="avatar a2">K</div>
      <div class="avatar a3">M</div>
      <div class="avatar a4">+</div>
    </div>
    <span>Join <strong>{total:,}</strong> others on the waitlist</span>
  </div>
</div>
</body></html>"""


def _theme_dark(waitlist: dict, stats: dict, ref_code: str = "") -> str:
    name = waitlist["name"]
    tagline = waitlist.get("tagline", "")
    description = waitlist.get("description", "")
    total = stats["total_signups"]

    return _base_head(name, """
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    min-height: 100vh; display: flex; align-items: center; justify-content: center;
    background: #0a0a0a; color: #e5e5e5; padding: 20px;
    background-image: radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.08) 0%, transparent 50%),
                      radial-gradient(circle at 80% 50%, rgba(255, 119, 198, 0.06) 0%, transparent 50%);
  }
  .container { max-width: 560px; width: 100%; text-align: center; }
  .logo {
    width: 56px; height: 56px; border-radius: 16px;
    background: linear-gradient(135deg, #7c3aed, #ec4899);
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 28px; font-size: 24px; font-weight: 800;
  }
  h1 {
    font-size: 48px; font-weight: 800; letter-spacing: -1.5px; margin-bottom: 16px;
    background: linear-gradient(135deg, #fff 30%, #a78bfa 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; line-height: 1.1;
  }
  .tagline { font-size: 20px; color: #a1a1aa; margin-bottom: 12px; }
  .description { font-size: 16px; color: #71717a; margin-bottom: 40px; line-height: 1.6; }
  .signup-form { margin-bottom: 28px; }
  .input-row { display: flex; gap: 8px; margin-bottom: 10px; }
  .email-input {
    flex: 1; padding: 16px 20px; background: #18181b; border: 1px solid #27272a;
    border-radius: 12px; color: white; font-size: 16px; outline: none;
    transition: border-color 0.2s;
  }
  .email-input::placeholder { color: #52525b; }
  .email-input:focus { border-color: #7c3aed; }
  .name-input {
    width: 100%; padding: 14px 20px; background: #18181b; border: 1px solid #27272a;
    border-radius: 12px; color: white; font-size: 15px; outline: none;
  }
  .name-input::placeholder { color: #52525b; }
  .name-input:focus { border-color: #7c3aed; }
  .submit-btn {
    padding: 16px 32px;
    background: linear-gradient(135deg, #7c3aed, #ec4899);
    color: white; border: none; border-radius: 12px;
    font-size: 16px; font-weight: 700; cursor: pointer;
    transition: all 0.2s; white-space: nowrap;
  }
  .submit-btn:hover { opacity: 0.9; transform: translateY(-1px); box-shadow: 0 8px 32px rgba(124, 58, 237, 0.3); }
  .social-proof {
    display: inline-flex; align-items: center; gap: 10px;
    padding: 10px 20px; background: #18181b; border: 1px solid #27272a;
    border-radius: 100px; font-size: 14px; color: #a1a1aa;
  }
  .pulse { width: 8px; height: 8px; border-radius: 50%; background: #22c55e; position: relative; }
  .pulse::after {
    content: ''; position: absolute; inset: -3px; border-radius: 50%;
    border: 2px solid #22c55e; animation: pulse 2s ease-out infinite; opacity: 0;
  }
  @keyframes pulse { 0% { transform: scale(0.8); opacity: 0.8; } 100% { transform: scale(2); opacity: 0; } }
  @media (max-width: 480px) {
    .input-row { flex-direction: column; }
    h1 { font-size: 34px; }
  }
  """) + f"""
<body>
<div class="container">
  <div class="logo">{name[0].upper()}</div>
  <h1>{name}</h1>
  {"<p class='tagline'>" + tagline + "</p>" if tagline else ""}
  {"<p class='description'>" + description + "</p>" if description else ""}
  {_signup_form(waitlist['slug'], ref_code)}
  <div class="social-proof">
    <span class="pulse"></span>
    <span><strong>{total:,}</strong> people ahead of you</span>
  </div>
</div>
</body></html>"""


def _theme_startup(waitlist: dict, stats: dict, ref_code: str = "") -> str:
    name = waitlist["name"]
    tagline = waitlist.get("tagline", "")
    description = waitlist.get("description", "")
    total = stats["total_signups"]

    return _base_head(name, """
  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    min-height: 100vh; display: flex; align-items: center; justify-content: center;
    background: #fff; color: #0f172a; padding: 20px;
  }
  .container { max-width: 640px; width: 100%; text-align: center; padding: 40px 20px; }
  .pill {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 14px 6px 8px; background: #f0fdf4; border: 1px solid #bbf7d0;
    border-radius: 100px; font-size: 13px; color: #166534; font-weight: 600;
    margin-bottom: 24px;
  }
  .pill-dot { width: 18px; height: 18px; border-radius: 50%; background: #22c55e; display: flex; align-items: center; justify-content: center; }
  .pill-dot svg { width: 10px; height: 10px; }
  h1 { font-size: 52px; font-weight: 800; letter-spacing: -2px; margin-bottom: 16px; line-height: 1.05; }
  .tagline { font-size: 22px; color: #64748b; margin-bottom: 12px; font-weight: 400; }
  .description { font-size: 17px; color: #94a3b8; margin-bottom: 44px; line-height: 1.6; max-width: 480px; margin-left: auto; margin-right: auto; }
  .signup-form { max-width: 460px; margin: 0 auto 32px; }
  .input-row { display: flex; gap: 8px; margin-bottom: 10px; }
  .email-input {
    flex: 1; padding: 18px 20px; border: 2px solid #e2e8f0; border-radius: 14px;
    font-size: 16px; outline: none; transition: all 0.2s; background: #f8fafc;
  }
  .email-input:focus { border-color: #3b82f6; background: #fff; box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1); }
  .name-input {
    width: 100%; padding: 16px 20px; border: 2px solid #e2e8f0; border-radius: 14px;
    font-size: 15px; outline: none; background: #f8fafc;
  }
  .name-input:focus { border-color: #3b82f6; background: #fff; }
  .submit-btn {
    padding: 18px 36px; background: #3b82f6; color: white; border: none;
    border-radius: 14px; font-size: 16px; font-weight: 700; cursor: pointer;
    transition: all 0.2s; white-space: nowrap;
  }
  .submit-btn:hover { background: #2563eb; transform: translateY(-1px); box-shadow: 0 8px 24px rgba(59, 130, 246, 0.25); }
  .trust-row {
    display: flex; align-items: center; justify-content: center; gap: 24px;
    font-size: 13px; color: #94a3b8;
  }
  .trust-item { display: flex; align-items: center; gap: 6px; }
  .trust-item svg { width: 16px; height: 16px; color: #cbd5e1; }
  .counter {
    margin-bottom: 32px; font-size: 15px; color: #64748b;
  }
  .counter strong { color: #0f172a; }
  @media (max-width: 480px) {
    .input-row { flex-direction: column; }
    h1 { font-size: 36px; }
    .trust-row { flex-direction: column; gap: 8px; }
  }
  """) + f"""
<body>
<div class="container">
  <div class="pill">
    <span class="pill-dot"><svg fill="white" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/></svg></span>
    Now accepting early access
  </div>
  <h1>{name}</h1>
  {"<p class='tagline'>" + tagline + "</p>" if tagline else ""}
  {"<p class='description'>" + description + "</p>" if description else ""}
  <p class="counter">Join <strong>{total:,}</strong> others already on the waitlist</p>
  {_signup_form(waitlist['slug'], ref_code)}
  <div class="trust-row">
    <span class="trust-item">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
      No spam, ever
    </span>
    <span class="trust-item">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
      Instant confirmation
    </span>
    <span class="trust-item">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
      Free to join
    </span>
  </div>
</div>
</body></html>"""


THEMES = {
    "minimal": _theme_minimal,
    "gradient": _theme_gradient,
    "dark": _theme_dark,
    "startup": _theme_startup,
}
