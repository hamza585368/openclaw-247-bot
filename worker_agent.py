import csv
import os
import re
import sys
import time
import requests
from playwright.sync_api import sync_playwright
from crewai import LLM, Agent, Task, Crew

GEMINI_KEY = os.environ.get("GEMINI_KEY", "").strip()
GROQ_KEY = os.environ.get("GROQ_KEY", "").strip()
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY", "").strip()
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "").strip()
TASK_TYPE = os.environ.get("TASK_TYPE", "leads").strip()
TASK_INPUT = os.environ.get("TASK_INPUT", "Plumbers in Dallas TX").strip()
CHAT_ID = os.environ.get("CHAT_ID", "").strip()

def send_telegram_msg(text):
    url = f"https://telegram.org{TG_BOT_TOKEN}/sendMessage"
    for i in range(0, len(text), 3800):
        requests.post(url, json={"chat_id": CHAT_ID, "text": text[i:i+3800]}, timeout=20)

def send_telegram_file(filepath, caption):
    url = f"https://telegram.org{TG_BOT_TOKEN}/sendDocument"
    with open(filepath, "rb") as f:
        requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"document": f}, timeout=60)

def get_available_llms():
    models = []
    if GEMINI_KEY:
        models.append(LLM(model="gemini/gemini-2.5-flash", api_key=GEMINI_KEY))
    if GROQ_KEY:
        models.append(LLM(model="groq/llama-3.3-70b-versatile", api_key=GROQ_KEY))
    if OPENROUTER_KEY:
        models.append(LLM(model="openrouter/meta-llama/llama-3.3-70b-instruct:free", api_key=OPENROUTER_KEY))
    return models

def run_crew_with_fallback(role, goal, backstory, description, expected_output):
    llms = get_available_llms()
    if not llms:
        raise RuntimeError("Koi bhi AI Key (GEMINI_KEY / GROQ_KEY / OPENROUTER_KEY) nahi mili!")
    last_err = None
    for llm in llms:
        try:
            agent = Agent(role=role, goal=goal, backstory=backstory, llm=llm, verbose=True)
            task = Task(description=description, expected_output=expected_output, agent=agent)
            res = Crew(agents=[agent], tasks=[task]).kickoff()
            return str(res.raw)
        except Exception as e:
            last_err = e
            print(f"Model switch triggered due to: {e}")
            continue
    raise RuntimeError(f"Saare AI models fail ho gaye: {last_err}")

def scrape_gmb_leads(search_query, max_scrolls=6):
    leads = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = browser.new_context(locale="en-US")
        page = context.new_page()
        search_url = f"https://google.com{search_query.replace(' ', '+')}?hl=en"
        page.goto(search_url, timeout=60000)
        time.sleep(5)

        try:
            feed = page.locator('div[role="feed"]')
            for _ in range(max_scrolls):
                feed.evaluate("(el) => el.scrollTop = el.scrollHeight")
                time.sleep(2)
        except Exception:
            pass

        listings = page.locator('a[href*="/maps/place/"]').all()
        seen_names = set()

        for item in listings[:25]:
            try:
                name = item.get_attribute("aria-label")
                if not name or name in seen_names:
                    continue
                seen_names.add(name)
                item.click()
                time.sleep(2)
                body_text = page.locator('div[role="main"]').inner_text(timeout=5000)
                phone_match = re.search(r'(\+1[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}|\(\d{3}\)\s?\d{3}[\s\-]\d{4})', body_text)
                phone = phone_match.group(0) if phone_match else "Not Listed"

                website = "No Website"
                web_loc = page.locator('a[data-item-id="authority"]')
                if web_loc.count() > 0:
                    website = web_loc.first.get_attribute("href") or "No Website"

                leads.append({
                    "Business Name": name,
                    "Phone": phone,
                    "Website": website
                })
            except Exception:
                continue

        browser.close()
    return leads

def run_agency():
    if TASK_TYPE == "leads":
        leads = scrape_gmb_leads(TASK_INPUT)
        csv_file = "usa_gmb_leads.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Business Name", "Phone", "Website"])
            writer.writeheader()
            writer.writerows(leads)

        lead_summary = "\n".join([f"- {l['Business Name']} | Phone: {l['Phone']} | Web: {l['Website']}" for l in leads[:15]])
        if not lead_summary:
            lead_summary = f"No direct map cards parsed for {TASK_INPUT}, create cold outreach strategy for this niche."

        output = run_crew_with_fallback(
            role="USA Cold Calling & GMB SEO Pitch Closer",
            goal="Identify hottest leads without websites and write easy phone scripts",
            backstory="Top USA agency closer who helps close $500-$1500 Website + GMB SEO deals on phone calls.",
            description=(
                f"Niche: {TASK_INPUT}\nExtracted GMB Leads:\n{lead_summary}\n\n"
                "1. List top priority businesses to call first (especially 'No Website' leads with phone numbers).\n"
                "2. Write a short, natural English calling script I can read directly to the USA business owner.\n"
                "3. Give me Hinglish tips on how to pitch pricing ($500-$1000) and close the deal."
            ),
            expected_output="Priority calling list, exact English script, and Hinglish closing tips."
        )
        send_telegram_file(csv_file, f"✅ {len(leads)} USA GMB Leads Ready: {TASK_INPUT}")
        send_telegram_msg(output)

    elif TASK_TYPE == "web":
        output = run_crew_with_fallback(
            role="Senior Local SEO Web Developer",
            goal="Build modern responsive single-file HTML5 + Tailwind CSS business website with LocalBusiness SEO Schema",
            backstory="Expert developer who creates high-converting USA local service websites.",
            description=(
                f"Create a complete, production-ready `index.html` using Tailwind CSS CDN for: {TASK_INPUT}.\n"
                "Include Hero section with Call Now CTA, Services grid, Why Choose Us, Reviews, Contact section, Meta SEO tags, and JSON-LD LocalBusiness Schema. Output ONLY valid HTML code."
            ),
            expected_output="Complete single-file HTML5 code."
        )
        html_code = output.replace("```html", "").replace("```", "").strip()
        with open("client_website.html", "w", encoding="utf-8") as f:
            f.write(html_code)
        send_telegram_file("client_website.html", f"🌐 Ready Client Website + SEO Code: {TASK_INPUT}")

    else:
        output = run_crew_with_fallback(
            role="USA Agency Money-Making Strategist",
            goal="Create step-by-step actionable USA client acquisition & revenue plans",
            backstory="Helps agency owners find high-paying USA local business niches and close deals fast.",
            description=f"Explain a complete step-by-step money-making strategy, best cities, and pricing in Hinglish for: {TASK_INPUT}",
            expected_output="Practical Hinglish agency roadmap."
        )
        send_telegram_msg(output)

if __name__ == "__main__":
    try:
        run_agency()
    except Exception as e:
        send_telegram_msg(f"❌ Worker Error: {str(e)}")
        sys.exit(1)
      
