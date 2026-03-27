#!/usr/bin/env python3
"""
FleaScan Telegram Edit Bot
Polls Telegram for commands to update leads.json, then pushes to GitHub.

Commands (only from authorized chat_id):
  /leads or /ls         — list all leads with ID, name, status
  /get <id>             — show full details for a lead
  /s <id> <Status>      — update status (New/Active/Pending/Closed/Dead)
  /n <id> <text>        — update Notes
  /c <id> <text>        — update Contact_Info
  /help                 — show command list

Run via PM2:
  pm2 start tg_bot.py --name fleascam-tg --interpreter python3
"""

import json
import subprocess
import datetime
import time
import requests
from pathlib import Path

BOT_TOKEN  = "8551790941:AAEJsyNNzwB87AWA7fb5WF3UPdWjnlaWK-0"
CHAT_ID    = 8755227361
API        = f"https://api.telegram.org/bot{BOT_TOKEN}"
REPO_DIR   = Path(__file__).parent
LEADS_FILE = REPO_DIR / "files" / "leads.json"
ROOT_LEADS = REPO_DIR / "leads.json"
ROOT_HTML  = REPO_DIR / "index.html"
FILES_HTML = REPO_DIR / "files" / "index.html"

VALID_STATUSES = {"new", "active", "pending", "closed", "dead"}


# ── Telegram helpers ──────────────────────────────────────────────────────────

def send(text: str, parse_mode: str = "HTML") -> None:
    requests.post(f"{API}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
    }, timeout=10)


def get_updates(offset: int) -> list:
    try:
        r = requests.get(f"{API}/getUpdates", params={
            "offset": offset,
            "timeout": 20,
            "allowed_updates": ["message"],
        }, timeout=30)
        return r.json().get("result", [])
    except Exception:
        return []


# ── Leads helpers ─────────────────────────────────────────────────────────────

def load_leads() -> list:
    return json.loads(LEADS_FILE.read_text())


def save_leads(leads: list) -> None:
    data = json.dumps(leads, indent=2, ensure_ascii=False)
    LEADS_FILE.write_text(data)
    ROOT_LEADS.write_text(data)   # keep root in sync


def git_push(msg: str) -> str:
    try:
        subprocess.run(
            ["git", "-C", str(REPO_DIR), "add",
             "files/leads.json", "leads.json"],
            check=True, capture_output=True
        )
        res = subprocess.run(
            ["git", "-C", str(REPO_DIR), "commit", "-m", msg],
            capture_output=True, text=True
        )
        if "nothing to commit" in res.stdout:
            return "ℹ️ No changes."
        subprocess.run(
            ["git", "-C", str(REPO_DIR), "push"],
            check=True, capture_output=True
        )
        return "✅ Pushed — site updates in ~30s."
    except subprocess.CalledProcessError as e:
        return f"⚠️ Git error: {e}"


def find_lead(leads: list, lead_id: int):
    return next((l for l in leads if l.get("Lead_ID") == lead_id), None)


# ── Command handlers ──────────────────────────────────────────────────────────

def cmd_list(leads: list) -> str:
    lines = ["<b>FleaScan Pipeline</b>"]
    for l in sorted(leads, key=lambda x: x.get("Lead_ID", 0)):
        status = l.get("Status", "New")
        emoji = {"New": "✦", "Active": "◉", "Pending": "◎",
                 "Closed": "◆", "Dead": "○"}.get(status, "·")
        lines.append(f"{emoji} <b>#{l['Lead_ID']}</b> {l['Market_Name']} — {l['City_State_ZIP']}")
    lines.append("\n/get &lt;id&gt; for details")
    return "\n".join(lines)


def cmd_get(leads: list, lead_id: int) -> str:
    l = find_lead(leads, lead_id)
    if not l:
        return f"❌ Lead #{lead_id} not found."
    contact = l.get("Contact_Info", "Not available")
    notes   = l.get("Notes", "") or "—"
    return (
        f"<b>#{l['Lead_ID']} — {l['Market_Name']}</b>\n"
        f"📍 {l['Full_Address']}, {l['City_State_ZIP']}\n"
        f"Status: <b>{l.get('Status','New')}</b>\n"
        f"Price: {l.get('Asking_Price','—')}\n"
        f"Owner: {l.get('Owner_Name_If_Known','—')}\n"
        f"📞 {contact}\n\n"
        f"<i>{l.get('Investment_Thesis','—')}</i>\n\n"
        f"Notes: {notes}\n\n"
        f"Edit: /s {lead_id} &lt;Status&gt; · /n {lead_id} &lt;note&gt; · /c {lead_id} &lt;contact&gt;"
    )


def cmd_status(leads: list, lead_id: int, new_status: str) -> str:
    canonical = new_status.strip().capitalize()
    if canonical.lower() not in VALID_STATUSES:
        return f"❌ Invalid status. Use: New, Active, Pending, Closed, Dead"
    l = find_lead(leads, lead_id)
    if not l:
        return f"❌ Lead #{lead_id} not found."
    old = l.get("Status", "New")
    l["Status"] = canonical
    save_leads(leads)
    push_msg = git_push(f"tg: lead #{lead_id} status {old} → {canonical}")
    return f"✅ Lead #{lead_id} <b>{l['Market_Name']}</b>\nStatus: {old} → <b>{canonical}</b>\n{push_msg}"


def cmd_note(leads: list, lead_id: int, text: str) -> str:
    l = find_lead(leads, lead_id)
    if not l:
        return f"❌ Lead #{lead_id} not found."
    l["Notes"] = text
    save_leads(leads)
    push_msg = git_push(f"tg: lead #{lead_id} notes updated")
    return f"✅ Lead #{lead_id} notes updated.\n{push_msg}"


def cmd_contact(leads: list, lead_id: int, text: str) -> str:
    l = find_lead(leads, lead_id)
    if not l:
        return f"❌ Lead #{lead_id} not found."
    l["Contact_Info"] = text
    save_leads(leads)
    push_msg = git_push(f"tg: lead #{lead_id} contact updated")
    return f"✅ Lead #{lead_id} contact info updated.\n{push_msg}"


HELP_TEXT = """<b>FleaScan Bot Commands</b>

/ls — list all leads
/get &lt;id&gt; — lead details
/s &lt;id&gt; &lt;Status&gt; — update status
/n &lt;id&gt; &lt;text&gt; — update notes
/c &lt;id&gt; &lt;text&gt; — update contact info

Statuses: New · Active · Pending · Closed · Dead"""


# ── Main loop ─────────────────────────────────────────────────────────────────

def handle(text: str) -> str:
    parts = text.strip().split(None, 2)
    if not parts:
        return "Send /help for commands."
    cmd = parts[0].lower().split("@")[0]

    try:
        if cmd in ("/ls", "/leads"):
            return cmd_list(load_leads())

        if cmd == "/help":
            return HELP_TEXT

        if cmd == "/get":
            if len(parts) < 2:
                return "Usage: /get <id>"
            return cmd_get(load_leads(), int(parts[1]))

        if cmd == "/s":
            if len(parts) < 3:
                return "Usage: /s <id> <Status>"
            return cmd_status(load_leads(), int(parts[1]), parts[2])

        if cmd == "/n":
            if len(parts) < 3:
                return "Usage: /n <id> <note text>"
            return cmd_note(load_leads(), int(parts[1]), parts[2])

        if cmd == "/c":
            if len(parts) < 3:
                return "Usage: /c <id> <contact info>"
            return cmd_contact(load_leads(), int(parts[1]), parts[2])

        return "Unknown command. Send /help."

    except (ValueError, IndexError):
        return "❌ Bad format. Send /help for usage."


def main():
    print(f"FleaScan bot started — polling @KingJulian15_bot")
    offset = 0
    while True:
        updates = get_updates(offset)
        for u in updates:
            offset = u["update_id"] + 1
            msg = u.get("message", {})
            if msg.get("from", {}).get("id") != CHAT_ID:
                continue   # ignore messages from other users
            text = msg.get("text", "").strip()
            if not text:
                continue
            reply = handle(text)
            send(reply)
        time.sleep(1)


if __name__ == "__main__":
    main()
