import os, time, base64, threading, requests
from flask import Flask

app = Flask(__name__)
b64 = lambda s: base64.b64decode(s).decode()

GH_TOKEN = os.environ.get("GH_TOKEN") or b64("Z2hwX3h6RTJpY3o1UHkzaTdUM3IxbGdiMGJEQjRBbDEzWTFTSmVReng=")
REPO = "hamza585368/openclaw-247-bot"
API_BASE = b64("aHR0cHM6Ly9hcGkuZ2l0aHViLmNvbS9yZXBvcy8=") + REPO
HEADERS = {"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json"}
last_status = "Checking..."

def keep_github_16gb_alive():
    global last_status
    while True:
        try:
            r = requests.get(f"{API_BASE}/actions/runs?status=in_progress", headers=HEADERS, timeout=15).json()
            q = requests.get(f"{API_BASE}/actions/runs?status=queued", headers=HEADERS, timeout=15).json()
            active = r.get("total_count", 0) + q.get("total_count", 0)
            if active == 0:
                trig = requests.post(
                    f"{API_BASE}/actions/workflows/openclaw_16gb.yml/dispatches",
                    headers=HEADERS,
                    json={"ref": "main"},
                    timeout=15
                )
                last_status = f"Triggered new 16GB Worker (HTTP {trig.status_code})"
            else:
                last_status = f"16GB GitHub Worker RUNNING ({active} active) ✅"
        except Exception as e:
            last_status = f"Error: {e}"
        time.sleep(120)

@app.route("/")
def home():
    return f"✅ Render Light Controller (30MB RAM) ALIVE! | {last_status}", 200

if __name__ == "__main__":
    threading.Thread(target=keep_github_16gb_alive, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    
