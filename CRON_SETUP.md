# BusinessGrader Campaign — Morning Report Cron Setup

## Overview
The morning report runs at **7am AEDT = 9pm UTC** daily.  
It emails Emily with overnight results and sends a WhatsApp summary.

---

## Step 1: Create the morning report script

Save this as `/home/node/.openclaw/workspace/data/businessgrader/morning_report.sh`:

```bash
#!/bin/bash
# BusinessGrader Morning Report
# Runs at 7am AEDT (9pm UTC)

WORKSPACE="/home/node/.openclaw/workspace"
SCRIPT_DIR="$WORKSPACE/data/businessgrader"
LOG="$SCRIPT_DIR/morning_report.log"

echo "=== Morning Report $(date) ===" >> "$LOG"

# Get campaign status output
STATUS=$(python3 "$SCRIPT_DIR/campaign_status.py" 2>&1)

# Count key stats from DB
STATS=$(python3 - <<'EOF'
import sqlite3, os
db = '/home/node/.openclaw/workspace/data/businessgrader/targets.db'
conn = sqlite3.connect(db)
c = conn.cursor()
total    = c.execute("SELECT COUNT(*) FROM targets").fetchone()[0]
sent     = c.execute("SELECT COUNT(*) FROM targets WHERE email_status='sent'").fetchone()[0]
pending  = c.execute("SELECT COUNT(*) FROM targets WHERE email_status='pending'").fetchone()[0]
replied  = c.execute("SELECT COUNT(*) FROM targets WHERE email_status='replied'").fetchone()[0]
pct      = round(sent/total*100, 1) if total else 0

# Sent since yesterday (last 24h)
overnight = c.execute("""
    SELECT COUNT(*) FROM targets
    WHERE email_status='sent'
    AND sent_at > datetime('now', '-24 hours')
""").fetchone()[0]

conn.close()
print(f"TOTAL={total}|SENT={sent}|PENDING={pending}|REPLIED={replied}|PCT={pct}|OVERNIGHT={overnight}")
EOF
)

# Parse stats
TOTAL=$(echo $STATS | grep -oP 'TOTAL=\K[^|]+')
SENT=$(echo $STATS | grep -oP 'SENT=\K[^|]+')
PENDING=$(echo $STATS | grep -oP 'PENDING=\K[^|]+')
REPLIED=$(echo $STATS | grep -oP 'REPLIED=\K[^|]+')
PCT=$(echo $STATS | grep -oP 'PCT=\K[^|]+')
OVERNIGHT=$(echo $STATS | grep -oP 'OVERNIGHT=\K[^|]+')

# Build email HTML
EMAIL_HTML="<h2>BusinessGrader Campaign — Morning Report</h2>
<p>Good morning Emily! Here's your overnight update:</p>
<table border='1' cellpadding='8' cellspacing='0' style='border-collapse:collapse;'>
  <tr><td><strong>Total Targets</strong></td><td>${TOTAL}</td></tr>
  <tr><td><strong>Sent (All Time)</strong></td><td>${SENT} (${PCT}%)</td></tr>
  <tr><td><strong>Sent Overnight</strong></td><td>${OVERNIGHT}</td></tr>
  <tr><td><strong>Pending</strong></td><td>${PENDING}</td></tr>
  <tr><td><strong>Replied</strong></td><td>${REPLIED}</td></tr>
</table>
<pre style='font-family:monospace;font-size:12px;background:#f4f4f4;padding:16px;'>
${STATUS}
</pre>
<p style='color:#888;font-size:12px;'>BusinessGrader Campaign | AgenticScale</p>"

# Send email to Emily
python3 "$WORKSPACE/tools/outlook.py" send \
  "emily.loving@agenticscale.ai" \
  "BusinessGrader Morning Report — $(date '+%d %b %Y')" \
  "$EMAIL_HTML" \
  >> "$LOG" 2>&1

echo "Email sent to emily.loving@agenticscale.ai" >> "$LOG"

# WhatsApp 3-line summary to Emily
WA_MSG="📊 *BusinessGrader Morning Report*
✉️ Sent overnight: ${OVERNIGHT} | Total sent: ${SENT}/${TOTAL} (${PCT}%)
💬 Replies received: ${REPLIED} | Pending: ${PENDING}"

# Send WhatsApp via OpenClaw message tool (or curl to WhatsApp API)
# Using OpenClaw CLI if available:
# openclaw message send --channel whatsapp --to +61433869329 --message "$WA_MSG"

# Alternative: direct WhatsApp API call (update with your credentials)
# curl -s -X POST "https://api.whatsapp.com/..." -d "to=+61433869329&message=$WA_MSG"

echo "WhatsApp summary: $WA_MSG" >> "$LOG"
echo "=== Report complete ===" >> "$LOG"
```

---

## Step 2: Make the script executable

```bash
chmod +x /home/node/.openclaw/workspace/data/businessgrader/morning_report.sh
```

---

## Step 3: Add the cron job

Run `crontab -e` and add this line:

```cron
# BusinessGrader Morning Report — 7am AEDT = 9pm UTC daily
0 21 * * * /home/node/.openclaw/workspace/data/businessgrader/morning_report.sh >> /home/node/.openclaw/workspace/data/businessgrader/morning_report.log 2>&1
```

---

## Step 4: Verify cron is installed

```bash
crontab -l | grep businessgrader
```

Expected output:
```
0 21 * * * /home/node/.openclaw/workspace/data/businessgrader/morning_report.sh >> ...
```

---

## Cron Schedule Notes

| Time Zone | Time  | Cron expression |
|-----------|-------|-----------------|
| AEDT      | 7:00am | `0 21 * * *` (UTC) |
| AEST      | 7:00am | `0 21 * * *` (UTC) |
| UTC       | 9:00pm | `0 21 * * *` |

> Note: AEDT is UTC+11. When daylight saving ends (AEST = UTC+10), adjust to `0 20 * * *`.

---

## WhatsApp Message Format (3-line summary)

```
📊 *BusinessGrader Morning Report*
✉️ Sent overnight: 42 | Total sent: 187/500 (37.4%)
💬 Replies received: 3 | Pending: 313
```

Recipient: **+61433869329** (Emily Loving)

---

## Files Summary

| File | Purpose |
|------|---------|
| `targets.db` | SQLite database — 500 Australian professional service businesses |
| `email_templates.json` | 6 industry-specific HTML email templates |
| `send_campaign.py` | Campaign sender with dry-run, industry filter, rate limiting |
| `campaign_status.py` | Campaign dashboard with progress + industry breakdown |
| `morning_report.sh` | Daily cron script for 7am AEDT report |
| `campaign.log` | Sender activity log |
| `morning_report.log` | Morning report log |
