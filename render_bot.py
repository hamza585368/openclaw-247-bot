import os
import threading
import time
import requests
from flask import Flask, jsonify

app = Flask(__name__)

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "").strip()
TG_USER_ID = os.environ.get("TG_USER_ID", "").strip()
GH_PAT = os.environ.get("GH_PAT", "").strip()
GITHUB_REPO = "hamza585368/openclaw-247-bot"

def send_telegram(chat_id, text):
    url = f"https://telegram.org{TG_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=15)
    except Exception as e:
        print(f"Telegram error: {e}")

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
    if resp.status_code != 204:
        print(f"GitHub API Error {resp.status_code}: {resp.text}")
    return resp.status_code == 204

def telegram_polling_loop():
    offset = 0
    while True:
        try:
            if not TG_BOT_TOKEN:
                time.sleep(10)
                continue
            url = f"https://telegram.org{TG_BOT_TOKEN}/getUpdates"
            resp = requests.get(url, params={"offset": offset, "timeout": 25}, timeout=35).json()
            for result in resp.get("result", []):
                offset = result["update_id"] + 1
                msg = result.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id", ""))
                text = msg.get("text", "").strip()

                if not chat_id or not text:
                    continue

                if TG_USER_ID and chat_id != TG_USER_ID:
                    continue

                if text.startswith("/start"):
                    help_msg = (
                        "🚀 16GB AI Agency Live Hai (Gemini + Groq + OpenRouter Auto-Brain)!\n\n"
                        "Commands:\n"
                        "1️⃣ USA GMB Leads + Calling Script:\n"
                        "/leads Plumbers in Austin Texas\n\n"
                        "2️⃣ Client Website + GMB SEO Code:\n"
                        "/web Roofing Company in Miami Florida\n\n"
                        "3️⃣ Paisa Kamane ka Niche & Strategy:\n"
                        "/idea Best USA GMB niches for $1000 deal"
                    )
                    send_telegram(chat_id, help_msg)

                elif text.startswith("/leads "):
                    query = text.replace("/leads ", "", 1).strip()
                    send_telegram(chat_id, f"⚡ 16GB GitHub Server start ho gaya...\nTarget: {query}\n2-4 min mein CSV file + Calling Pitch aayegi!")
                    if not trigger_github_worker("leads", query, chat_id):
                        send_telegram(chat_id, "❌ Error: GitHub Actions trigger nahi hua. Render mein GH_PAT check karein.")

                elif text.startswith("/web "):
                    query = text.replace("/web ", "", 1).strip()
                    send_telegram(chat_id, f"💻 Website + SEO Developer Agent kaam par lag gaya...\nClient: {query}\n2-3 min mein ready HTML file aayegi!")
                    if not trigger_github_worker("web", query, chat_id):
                        send_telegram(chat_id, "❌ Error: GitHub Actions trigger nahi hua. GH_PAT check karein.")

                elif text.startswith("/idea "):
                    query = text.replace("/idea ", "", 1).strip()
                    send_telegram(chat_id, f"🧠 Business Strategist research kar raha hai: {query}...")
                    if not trigger_github_worker("idea", query, chat_id):
                        send_telegram(chat_id, "❌ Error: GitHub Actions trigger nahi hua. GH_PAT check karein.")

        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

@app.route("/")
def health_check():
    return jsonify({"status": "alive", "repo": GITHUB_REPO}), 200

if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
    t = threading.Thread(target=telegram_polling_loop, daemon=True)
    t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
  
