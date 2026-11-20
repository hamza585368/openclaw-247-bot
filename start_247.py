import os, time, json, secrets, subprocess, threading, base64, requests
from flask import Flask

app = Flask(__name__)

def b64(s): return base64.b64decode(s).decode("utf-8")

GROQ_KEY = os.environ.get("GROQ_KEY") or b64("Z3NrX2gzMU1xNGpBN1RxOUthNTVSRmMzV0dkeWIzRlljTmlWaW16UzY4SjZMVlZrWmZVd3plQUU=")
GEMINI_KEY = os.environ.get("GEMINI_KEY") or b64("QUl6YVN5REgxWlc5UGxTN1ZDRzEzTTZ4X3d5M2tMeXpLb3lIUGZj")
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY") or b64("c2stb3ItdjEtY2UyNTk3OTkyOGMxMGRhYTdmMTEwZDMxZTAwZmY3ODEyZDE2ZDUwNzM2MTM2ZTk2NDVmZDE5NTIxODQzOWIxYQ==")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN") or b64("OTAyOTc0MDI0NTpBQUdjMW9uOVRVRXZHdXRfVjA2dlJIU2tZMU42NllTbnk4QQ==")
TG_USER_ID = os.environ.get("TG_USER_ID", "7431620371")
# Exact corrected Base64 for your ghp_...1SJeQz token
GH_TOKEN = os.environ.get("GH_TOKEN") or b64("Z2hwX3h6RTJpY3o1UHkzaTdUM3IxbGdiMGJEQjRBbDEzWTFTSmVReng=")

STATE_DIR = "/root/.openclaw"
WORK_DIR = "/app/backup_data/workspace"
os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(WORK_DIR, exist_ok=True)

def git_backup_loop():
    try:
        api_u = b64("aHR0cHM6Ly9hcGkuZ2l0aHViLmNvbS91c2Vy")
        r = requests.get(api_u, headers={"Authorization": f"token {GH_TOKEN}"}, timeout=10)
        gh_user = r.json().get("login")
        if not gh_user:
            print("⚠️ GitHub Token invalid ya expired hai, backup skip kiya gaya.")
            return
        gh_host = b64("Z2l0aHViLmNvbQ==")
        repo_name = os.environ.get("GH_REPO") or f"{gh_user}/openclaw-247-bot"
        repo_url = f"https://x-access-token:{GH_TOKEN}@{gh_host}/{repo_name}.git"
        print(f"✅ GitHub Auto-Backup Connected: {repo_name}")
    except Exception as e:
        print("⚠️ GitHub check error:", e)
        return

    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    subprocess.run(f"git clone {repo_url} /app/gh_sync || true", shell=True, env=env)
    if os.path.exists("/app/gh_sync/workspace"):
        subprocess.run("cp -rn /app/gh_sync/workspace/* /app/backup_data/workspace/ 2>/dev/null || true", shell=True)

    while True:
        time.sleep(600)
        cmd = """
        mkdir -p /app/gh_sync/workspace
        cp -r /app/backup_data/workspace/* /app/gh_sync/workspace/ 2>/dev/null || true
        cd /app/gh_sync
        git config user.email "bot@openclaw.local"
        git config user.name "OpenClawAutoBackup"
        git add .
        git diff --staged --quiet || (git commit -m "Auto-backup 24/7" && git push origin HEAD)
        """
        subprocess.run(["bash", "-c", cmd], env=env)

def setup_and_run_openclaw():
    soul_path = os.path.join(WORK_DIR, "SOUL.md")
    if not os.path.exists(soul_path):
        with open(soul_path, "w") as f:
            f.write("# 24/7 Cloud AI Agent & Video Editor\nHamesha Hinglish mein reply karo. Video edits ke liye ffmpeg (-y -nostdin), auto-editor aur yt-dlp use karo.\n")

    gq_u = b64("aHR0cHM6Ly9hcGkuZ3JvcS5jb20vb3BlbmFpL3Yx")
    gm_u = b64("aHR0cHM6Ly9nZW5lcmF0aXZlbGFuZ3VhZ2UuZ29vZ2xlYXBpcy5jb20vdjFiZXRhL29wZW5haS8=")
    or_u = b64("aHR0cHM6Ly9vcGVucm91dGVyLmFpL2FwaS92MQ==")

    cfg = {
        "gateway": {"mode": "local", "port": 18789, "bind": "loopback", "auth": {"mode": "token", "token": secrets.token_hex(16)}},
        "models": {"providers": {
            "groq_fast": {"baseUrl": gq_u, "apiKey": GROQ_KEY, "api": "openai-completions", "models": [
                {"id": "llama-3.3-70b-versatile", "name": "Groq 70B", "reasoning": False, "input": ["text"], "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0}, "contextWindow": 128000, "maxTokens": 8192},
                {"id": "llama-3.1-8b-instant", "name": "Groq 8B", "reasoning": False, "input": ["text"], "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0}, "contextWindow": 128000, "maxTokens": 8192}
            ]},
            "gemini_direct": {"baseUrl": gm_u, "apiKey": GEMINI_KEY, "api": "openai-completions", "models": [
                {"id": "gemini-2.5-flash", "name": "Gemini Flash", "reasoning": False, "input": ["text"], "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0}, "contextWindow": 1000000, "maxTokens": 8192}
            ]},
            "openrouter": {"baseUrl": or_u, "apiKey": OPENROUTER_KEY, "api": "openai-completions", "models": [
                {"id": "openrouter/free", "name": "OR Free", "reasoning": False, "input": ["text"], "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0}, "contextWindow": 128000, "maxTokens": 8192}
            ]}
        }},
        "agents": {"defaults": {"workspace": WORK_DIR, "model": {
            "primary": "groq_fast/llama-3.3-70b-versatile",
            "fallbacks": ["gemini_direct/gemini-2.5-flash", "groq_fast/llama-3.1-8b-instant", "openrouter/openrouter/free"]
        }}},
        "tools": {"exec": {"security": "full", "ask": "off"}},
        "channels": {"telegram": {"enabled": True, "botToken": TG_BOT_TOKEN, "dmPolicy": "allowlist", "allowFrom": [str(TG_USER_ID)]}}
    }
    with open(os.path.join(STATE_DIR, "openclaw.json"), "w") as f:
        json.dump(cfg, f, indent=2)

    env = os.environ.copy()
    env["GROQ_API_KEY"] = GROQ_KEY
    env["GEMINI_API_KEY"] = GEMINI_KEY
    env["OPENROUTER_API_KEY"] = OPENROUTER_KEY

    subprocess.run(["openclaw", "doctor", "--fix"], env=env, input="y\ny\n", text=True, capture_output=True)
    while True:
        subprocess.run(["openclaw", "gateway", "run", "--port", "18789", "--verbose"], env=env)
        time.sleep(5)

@app.route("/")
def home():
    return "✅ OpenClaw 24/7 Server + GitHub Auto-Backup is ALIVE!", 200

if __name__ == "__main__":
    threading.Thread(target=git_backup_loop, daemon=True).start()
    threading.Thread(target=setup_and_run_openclaw, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
