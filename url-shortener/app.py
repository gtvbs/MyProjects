import os
import re
import io
import base64
import random
import string
import json
import redis
import qrcode
from flask import Flask, request, render_template_string, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ocp-super-secret-key-2026")

# Connect to Redis service in OpenShift
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)

STRONG_PWD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')

BASE_STYLE = """
<style>
  body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f6f9; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
  .card { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.1); width: 100%; max-width: 460px; }
  h2 { margin-top: 0; color: #1e293b; text-align: center; }
  .form-group { margin-bottom: 1rem; }
  label { display: block; font-weight: 600; margin-bottom: 0.4rem; color: #334155; }
  input[type="text"], input[type="password"], input[type="url"], input[type="number"] {
    width: 100%; padding: 0.65rem; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box;
  }
  .checkbox-group { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; }
  button { width: 100%; padding: 0.75rem; background: #2563eb; color: white; border: none; border-radius: 6px; font-size: 1rem; font-weight: 600; cursor: pointer; margin-top: 0.5rem; }
  button:hover { background: #1d4ed8; }
  .error { background: #fee2e2; color: #b91c1c; padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; font-size: 0.9rem; }
  .short-url-box { background: #f8fafc; border: 1px dashed #94a3b8; padding: 0.75rem; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; word-break: break-all; }
  .qr-box { text-align: center; margin: 1rem 0; }
  .timer { text-align: center; font-weight: 600; color: #dc2626; margin: 1rem 0; font-size: 1.1rem; }
  .hidden { display: none; }
</style>
"""

LOGIN_HTML = BASE_STYLE + """
<div class="card">
  <h2>URL Shortener - Login</h2>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="POST">
    <div class="form-group">
      <label>User ID</label>
      <input type="text" name="userid" required placeholder="Enter User ID">
    </div>
    <div class="form-group">
      <label>Password</label>
      <input type="password" name="password" required placeholder="Min 8 chars, 1 Upper, 1 Lower, 1 Num, 1 Special">
      <small style="color:#64748b; font-size:0.78rem;">Strong password mandatory: At least 8 chars, 1 uppercase, 1 lowercase, 1 number & 1 special char (@$!%*?&).</small>
    </div>
    <button type="submit">Login</button>
  </form>
</div>
"""

INPUT_HTML = BASE_STYLE + """
<div class="card">
  <h2>Create Short URL</h2>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="POST" action="/generate">
    <div class="form-group">
      <label>Destination URL *</label>
      <input type="url" name="url" required placeholder="https://example.com/very/long/path">
    </div>

    <div class="checkbox-group">
      <input type="checkbox" id="qr_needed" name="qr_needed">
      <label for="qr_needed" style="margin:0;">QR Code Needed?</label>
    </div>

    <div class="checkbox-group">
      <input type="checkbox" id="expiry_needed" name="expiry_needed" onchange="document.getElementById('expiry_box').classList.toggle('hidden')">
      <label for="expiry_needed" style="margin:0;">Expiry Needed?</label>
    </div>
    <div id="expiry_box" class="form-group hidden">
      <label>Expiry Time (in seconds)</label>
      <input type="number" name="expiry_seconds" min="10" value="300">
    </div>

    <div class="checkbox-group">
      <input type="checkbox" id="custom_needed" name="custom_needed" onchange="document.getElementById('custom_box').classList.toggle('hidden')">
      <label for="custom_needed" style="margin:0;">Customise Short URL?</label>
    </div>
    <div id="custom_box" class="form-group hidden">
      <label>Custom Alias</label>
      <input type="text" name="custom_code" pattern="[A-Za-z0-9_-]+" placeholder="my-custom-link">
    </div>

    <div class="checkbox-group">
      <input type="checkbox" id="pwd_needed" name="pwd_needed" onchange="document.getElementById('pwd_box').classList.toggle('hidden')">
      <label for="pwd_needed" style="margin:0;">Password Protected?</label>
    </div>
    <div id="pwd_box" class="form-group hidden">
      <label>Set Link Password</label>
      <input type="password" name="url_password" placeholder="Password required to open link">
    </div>

    <button type="submit">Generate</button>
  </form>
</div>
"""

OUTPUT_HTML = BASE_STYLE + """
<div class="card">
  <h2>Generated Short URL</h2>
  <div class="short-url-box">
    <a id="shortLink" href="{{ short_url }}" target="_blank">{{ short_url }}</a>
    <button type="button" onclick="copyUrl()" style="width:auto; padding:0.4rem 0.8rem; margin:0; font-size:0.85rem;">Copy</button>
  </div>

  {% if qr_b64 %}
  <div class="qr-box">
    <img src="data:image/png;base64,{{ qr_b64 }}" alt="QR Code" style="max-width:200px; border:1px solid #e2e8f0; border-radius:8px;">
  </div>
  {% endif %}

  {% if ttl > 0 %}
  <div class="timer">Expires in: <span id="timer">{{ ttl }}</span>s</div>
  <script>
    let timeLeft = {{ ttl }};
    const timerEl = document.getElementById('timer');
    const interval = setInterval(() => {
      timeLeft--;
      if (timeLeft <= 0) {
        clearInterval(interval);
        timerEl.innerText = "EXPIRED";
        document.getElementById('shortLink').style.pointerEvents = 'none';
        document.getElementById('shortLink').style.color = '#94a3b8';
      } else {
        timerEl.innerText = timeLeft;
      }
    }, 1000);
  </script>
  {% endif %}

  <a href="/input" style="display:block; text-align:center; margin-top:1rem; color:#2563eb; text-decoration:none; font-weight:600;">+ Shorten Another URL</a>
</div>
<script>
function copyUrl() {
  const url = document.getElementById('shortLink').href;
  navigator.clipboard.writeText(url).then(() => alert('Short URL copied to clipboard!'));
}
</script>
"""

PASSWORD_PROMPT_HTML = BASE_STYLE + """
<div class="card">
  <h2>Protected Link</h2>
  <p style="text-align:center; color:#475569;">This short URL is password protected.</p>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="POST">
    <div class="form-group">
      <label>Enter Password</label>
      <input type="password" name="password" required autofocus>
    </div>
    <button type="submit">Unlock & Redirect</button>
  </form>
</div>
"""

@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        userid = request.form.get("userid", "").strip()
        password = request.form.get("password", "")
        if not STRONG_PWD_REGEX.match(password):
            error = "Password does not meet strong password requirements!"
        else:
            session["user"] = userid
            return redirect(url_for("input_page"))
    return render_template_string(LOGIN_HTML, error=error)

@app.route("/input", methods=["GET"])
def input_page():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template_string(INPUT_HTML, error=None)

@app.route("/generate", methods=["POST"])
def generate():
    if "user" not in session:
        return redirect(url_for("login"))

    long_url = request.form.get("url", "").strip()
    qr_needed = "qr_needed" in request.form
    expiry_needed = "expiry_needed" in request.form
    custom_needed = "custom_needed" in request.form
    pwd_needed = "pwd_needed" in request.form

    if custom_needed:
        code = request.form.get("custom_code", "").strip()
        if not code:
            return render_template_string(INPUT_HTML, error="Custom alias cannot be empty.")
        if r.exists(f"url:{code}"):
            return render_template_string(INPUT_HTML, error="Custom alias already in use. Choose another.")
    else:
        code = "".join(random.choices(string.ascii_letters + string.digits, k=6))
        while r.exists(f"url:{code}"):
            code = "".join(random.choices(string.ascii_letters + string.digits, k=6))

    ttl = int(request.form.get("expiry_seconds", 300)) if expiry_needed else 0
    pwd_hash = None
    if pwd_needed:
        raw_pwd = request.form.get("url_password", "")
        if not raw_pwd:
            return render_template_string(INPUT_HTML, error="Please enter a password for the protected link.")
        pwd_hash = generate_password_hash(raw_pwd)

    payload = {
        "url": long_url,
        "pwd_hash": pwd_hash,
        "created_by": session["user"]
    }

    if ttl > 0:
        r.setex(f"url:{code}", ttl, json.dumps(payload))
    else:
        r.set(f"url:{code}", json.dumps(payload))

    short_url = request.host_url.rstrip("/") + "/" + code

    qr_b64 = None
    if qr_needed:
        img = qrcode.make(short_url)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return render_template_string(OUTPUT_HTML, short_url=short_url, qr_b64=qr_b64, ttl=ttl)

@app.route("/<code>", methods=["GET", "POST"])
def redirect_short_url(code):
    raw = r.get(f"url:{code}")
    if not raw:
        return BASE_STYLE + "<div class='card'><h2>404 - Link Not Found or Expired</h2></div>", 404

    data = json.loads(raw)
    if data.get("pwd_hash"):
        if request.method == "POST":
            entered = request.form.get("password", "")
            if check_password_hash(data["pwd_hash"], entered):
                return redirect(data["url"])
            return render_template_string(PASSWORD_PROMPT_HTML, error="Incorrect password!")
        return render_template_string(PASSWORD_PROMPT_HTML, error=None)

    return redirect(data["url"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
