import os, time, json, secrets, subprocess, threading
from flask import Flask

app = Flask(__name__)

# Keys Render Environment Variables se aayengi (100% Safe)
GROQ_KEY = os.environ.get("GROQ_KEY", "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")
GEMINI_KEY = os.environ.get("GEMINI_KEY", "AIzaSyDH1ZW9PlS7VCG13M6x_wy3kLyzKoyHPfc")
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY", "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")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "9029740245:AAGc1on9TUQvGut_V06vRHSkY1N66YSny8A")
TG_USER_ID = os.environ.get("TG_USER_ID", "7431620371")
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "")  # Format: username/openclaw-247-bot

STATE_DIR = "/root/.openclaw"
WORK_DIR = "/app/backup_data/workspace"
os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(WORK_DIR, exist_ok=True)

def git_backup_loop():
    if not GH_TOKEN or not GH_REPO:
        return
    repo_url = f"https://{GH_TOKEN}@://github.com{GH_REPO}.git"
    subprocess.run(f"git clone {repo_url} /app/gh_sync || true", shell=True)
    if os.path.exists("/app/gh_sync/workspace"):
        subprocess.run("cp -rn /app/gh_sync/workspace/* /app/backup_data/workspace/ 2>/dev/null || true", shell=True)
    while True:
        time.sleep(600)  # Har 10 minute mein GitHub par auto-backup
        cmd = """
        mkdir -p /app/gh_sync/workspace
        cp -r /app/backup_data/workspace/* /app/gh_sync/workspace/ 2>/dev/null || true
        cd /app/gh_sync
        git config user.email "bot@openclaw.local"
        git config user.name "OpenClawAutoBackup"
        git add .
        git diff --staged --quiet || (git commit -m "Auto-backup 24/7" && git push origin main)
        """
        subprocess.run(["bash", "-c", cmd])

def setup_and_run_openclaw():
    soul_path = os.path.join(WORK_DIR, "SOUL.md")
    if not os.path.exists(soul_path):
        with open(soul_path, "w") as f:
            f.write("# 24/7 Cloud AI Agent & Video Editor\nHamesha Hinglish mein reply karo. Light edits ffmpeg/auto-editor se turant karo, aur heavy GPU tasks Colab/GitHub worker ko bhejo.\n")

    cfg = {
        "gateway": {"mode": "local", "port": 18789, "bind": "loopback", "auth": {"mode": "token", "token": secrets.token_hex(16)}},
        "models": {"providers": {
            "groq_fast": {"baseUrl": "https://groq.com", "apiKey": GROQ_KEY, "api": "openai-completions", "models": [
                {"id": "llama-3.3-70b-versatile", "name": "Groq 70B", "reasoning": False, "input": ["text"], "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0}, "contextWindow": 128000, "maxTokens": 8192}
            ]},
            "gemini_direct": {"baseUrl": "https://googleapis.com", "apiKey": GEMINI_KEY, "api": "openai-completions", "models": [
                {"id": "gemini-2.5-flash", "name": "Gemini Flash", "reasoning": False, "input": ["text"], "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0}, "contextWindow": 1000000, "maxTokens": 8192}
            ]},
            "openrouter": {"baseUrl": "https://openrouter.ai", "apiKey": OPENROUTER_KEY, "api": "openai-completions", "models": [
                {"id": "openrouter/free", "name": "OR Free", "reasoning": False, "input": ["text"], "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0}, "contextWindow": 128000, "maxTokens": 8192}
            ]}
        }},
        "agents": {"defaults": {"workspace": WORK_DIR, "model": {
            "primary": "groq_fast/llama-3.3-70b-versatile",
            "fallbacks": ["gemini_direct/gemini-2.5-flash", "openrouter/openrouter/free"]
        }}},
        "tools": {"exec": {"security": "full", "ask": "off"}},
        "channels": {"telegram": {"enabled": True, "botToken": TG_BOT_TOKEN, "dmPolicy": "allowlist", "allowFrom": [str(TG_USER_ID)]}}
    }
    with open(os.path.join(STATE_DIR, "openclaw.json"), "w") as f:
        json.dump(cfg, f, indent=2)

    while True:
        subprocess.run(["openclaw", "gateway", "run", "--port", "18789", "--verbose"])
        time.sleep(5)

@app.route("/")
def home():
    return "✅ OpenClaw 24/7 Server + GitHub Auto-Backup is ALIVE!", 200

if __name__ == "__main__":
    threading.Thread(target=git_backup_loop, daemon=True).start()
    threading.Thread(target=setup_and_run_openclaw, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
