#!/usr/bin/env python3
"""
FleaScan Bot — GitHub Pages Publisher
Appends new leads to leads.json and pushes to GitHub.

Usage (called automatically by Claude Code after every scan):
  python push_leads.py --leads '[{...}, {...}]'

Or interactively:
  python push_leads.py
"""

import json
import os
import subprocess
import sys
import argparse
import datetime
from pathlib import Path

LEADS_FILE = Path(__file__).parent / "leads.json"

def load_leads():
    if LEADS_FILE.exists():
        with open(LEADS_FILE) as f:
            return json.load(f)
    return []

def save_leads(leads):
    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)

def next_id(leads):
    if not leads:
        return 1
    return max(l.get("Lead_ID", 0) for l in leads) + 1

def append_leads(new_leads: list[dict]) -> list[dict]:
    existing = load_leads()
    start_id = next_id(existing)
    today = datetime.date.today().isoformat()

    for i, lead in enumerate(new_leads):
        lead.setdefault("Lead_ID", start_id + i)
        lead.setdefault("Scan_Date", today)
        lead.setdefault("Status", "New")

    combined = existing + new_leads
    save_leads(combined)
    print(f"✅ Saved {len(new_leads)} new leads. Total: {len(combined)}")
    return combined

def git_push():
    """Commit and push leads.json to GitHub."""
    repo_dir = LEADS_FILE.parent
    try:
        subprocess.run(["git", "-C", str(repo_dir), "add", "leads.json"],
                       check=True, capture_output=True)
        msg = f"scan: add leads {datetime.date.today().isoformat()}"
        result = subprocess.run(
            ["git", "-C", str(repo_dir), "commit", "-m", msg],
            capture_output=True, text=True
        )
        if "nothing to commit" in result.stdout:
            print("ℹ️  No changes to commit.")
            return
        subprocess.run(["git", "-C", str(repo_dir), "push"],
                       check=True, capture_output=True)
        print("🚀 Pushed to GitHub — site will update in ~30 seconds.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Git error: {e.stderr or e}")
        print("   Make sure you've run: git remote add origin <your-repo-url>")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--leads", type=str, help="JSON array of lead objects")
    args = parser.parse_args()

    if args.leads:
        try:
            new_leads = json.loads(args.leads)
            if not isinstance(new_leads, list):
                new_leads = [new_leads]
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            sys.exit(1)
    else:
        # Interactive mode — read from stdin
        print("Paste lead JSON array (end with EOF / Ctrl+D):")
        raw = sys.stdin.read().strip()
        new_leads = json.loads(raw)

    append_leads(new_leads)
    git_push()

if __name__ == "__main__":
    main()
