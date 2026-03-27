# FleaScan — Distressed Flea Market Deal Pipeline

Live site: **https://YOUR_USERNAME.github.io/fleascam-leads**

## How it works

1. Claude Code bot scans for distressed outdoor flea markets
2. Bot appends new leads to `leads.json`
3. `push_leads.py` commits and pushes to GitHub
4. GitHub Pages serves the CRM dashboard automatically

## Running a scan

In your Claude Code terminal:
```
scan
```

The bot will find 5 new leads, append them to `leads.json`, and push to GitHub.

## Manual push

```bash
python push_leads.py --leads '[{"Market_Name": "...", ...}]'
```

## Lead statuses

| Status | Meaning |
|--------|---------|
| New | Just found, needs review |
| Active | Currently pursuing |
| Pending | Offer made / under review |
| Closed | Deal won |
| Dead | No longer viable |

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/fleascam-leads.git
cd fleascam-leads
# Enable GitHub Pages: Settings → Pages → Source: main branch / root
```
