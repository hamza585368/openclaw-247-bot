import os
import threading
import time
import requests
from flask import Flask, jsonify

app = Flask(__name__)

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "").strip().replace("bot", "", 1) if os.environ.get("TG_BOT_TOKEN", "").strip().startswith("bot") else os.environ.get("TG_BOT_TOKEN", "").strip()
TG_USER_ID = os.environ.get("TG_USER_ID", "").strip()
GH_PAT = os.environ.get("GH_PAT", "").strip()
GITHUB_REPO = "hamza585368/openclaw-247-bot"

_poller_started = False
_lock = threading.Lock()

def setup_telegram_bot():
    if not TG_BOT_TOKEN:
        print("ERROR: TG_BOT_TOKEN missing in Render Environment!")
        return
    try:
        # 1. Purana Webhook hatao taaki getUpdates 100% kaam kare
        wh_url = f"https://telegram.org{TG_BOT_TOKEN}/deleteWebhook"
        r1 = requests.post(wh_url, json={"drop_pending_updates": False}, timeout=15)
        print("Webhook clear status:", r1.text)

        # 2. Purana OpenClaw Menu hata kar naya Agency Menu set karo
        cmd_url = f"https://telegram.org{TG_BOT_TOKEN}/setMyCommands"
        commands = [
            {"command": "start", "description": "Check Agency Bot Status"},
            {"command": "leads", "description": "USA GMB Leads (e.g. /leads Roofers in Dallas TX)"},
            {"command": "web", "description": "Create SEO Website (e.g. /web Plumber in Austin TX)"},
            {"command": "idea", "description": "Best USA Money Making Niche & Plan"}
        ]
        requests.post(cmd_url, json={"commands": commands}, timeout=15)
    except Exception as e:
        print("Setup error:", e)

def send_telegram(chat_id, text):
    url = f"https://telegram.org{TG_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=15)
        print("Send status:", r.status_code)
    except Exception as e:
        print(f"Telegram send error: {e}")

def trigger_github_worker(task_type, task_input, chat_id):
    url = f"https://github.com{GITHUB_REPO}/actions/workflows/agency_worker.yml/dispatches"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GH_PAT}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    payload = {
        "ref": "main",
        "inputs": {
            "task_type": task_type,
            "task_input": task_input,
            "chat_id": str(chat_id)
        }
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=20)
    print(f"GitHub Trigger Status: {resp.status_code} | {resp.text}")
    return resp.status_code == 204

def telegram_polling_loop():
    setup_telegram_bot()
    offset = 0
    print("Telegram Polling Loop Started Successfully!")
    while True:
        try:
            if not TG_BOT_TOKEN:
                time.sleep(10)
                continue
            url = f"https://telegram.org{TG_BOT_TOKEN}/getUpdates"
            resp = requests.get(url, params={"offset": offset, "timeout": 20}, timeout=30).json()
            if not resp.get("ok"):
                print("Telegram API Error:", resp)
                time.sleep(5)
                continue

            for result in resp.get("result", []):
                offset = result["update_id"] + 1
                msg = result.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id", ""))
                text = msg.get("text", "").strip()

                if not chat_id or not text:
                    continue

                print(f"Incoming Msg from {chat_id}: {text}")

                if TG_USER_ID and TG_USER_ID.isdigit() and chat_id != TG_USER_ID:
                    send_telegram(chat_id, f"⚠️ Access Denied! Aapki Chat ID ({chat_id}) Render ke TG_USER_ID ({TG_USER_ID}) se alag hai.")
                    continue

                if text.startswith("/start") or text.lower() in ["hi", "hii", "hello", "/help"]:
                    help_msg = (
                        "🚀 16GB AI Agency Live Hai!\n\n"
                        "Ye Commands Bhejein:\n"
                        "1️⃣ USA GMB Leads + Calling Script:\n"
                        "/leads Roofers in Dallas Texas\n\n"
                        "2️⃣ Client Website + GMB SEO Code:\n"
                        "/web Plumber in Miami Florida\n\n"
                        "3️⃣ Paisa Kamane ka Niche & Strategy:\n"
                        "/idea High ticket USA GMB service"
                    )
                    send_telegram(chat_id, help_msg)

                elif text.startswith("/leads"):
                    query = text.replace("/leads", "", 1).strip() or "Roofers in Dallas Texas"
                    send_telegram(chat_id, f"⚡ 16GB GitHub Server start ho gaya...\nTarget: {query}\n2-4 min mein CSV file + Calling Pitch aayegi!")
                    if not trigger_github_worker("leads", query, chat_id):
                        send_telegram(chat_id, "❌ Error: GitHub Actions start nahi hua. Render mein GH_PAT check karein.")

                elif text.startswith("/web"):
                    query = text.replace("/web", "", 1).strip() or "Roofing Company Miami FL"
                    send_telegram(chat_id, f"💻 Website + SEO Agent kaam par lag gaya...\nClient: {query}\n2-3 min mein ready HTML file aayegi!")
                    if not trigger_github_worker("web", query, chat_id):
                        send_telegram(chat_id, "❌ Error: GitHub Actions start nahi hua. GH_PAT check karein.")

                elif text.startswith("/idea"):
                    query = text.replace("/idea", "", 1).strip() or "Best USA GMB niches for $1000 deal"
                    send_telegram(chat_id, f"🧠 Business Strategist research kar raha hai: {query}...")
                    if not trigger_github_worker("idea", query, chat_id):
                        send_telegram(chat_id, "❌ Error: GitHub Actions start nahi hua. GH_PAT check karein.")
                else:
                    send_telegram(chat_id, "Command samajh nahi aaya. /start dabayein ya '/leads Roofers in Dallas Texas' bhejein!")

        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

def ensure_poller():
    global _poller_started
    with _lock:
        if not _poller_started:
            _poller_started = True
            t = threading.Thread(target=telegram_polling_loop, daemon=True)
            t.start()

@app.route("/")
def health_check():
    ensure_poller()
    return jsonify({"status": "alive", "poller": _poller_started, "repo": GITHUB_REPO}), 200

ensure_poller()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
