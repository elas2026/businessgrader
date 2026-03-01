#!/usr/bin/env python3
"""
BusinessGrader Campaign Sender
Usage:
  python3 send_campaign.py [--limit N] [--industry INDUSTRY] [--dry-run]

Options:
  --limit N        Only send N emails (for testing)
  --industry IND   Only send to a specific industry (legal, accounting, medical, dental, financial_services, other)
  --dry-run        Print what would be sent without actually sending
"""

import sqlite3
import json
import os
import sys
import time
import subprocess
import logging
import argparse
from datetime import datetime, timezone

# ─── PATHS ───────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DB_PATH    = os.path.join(BASE_DIR, 'targets.db')
TEMPLATES  = os.path.join(BASE_DIR, 'email_templates.json')
LOG_PATH   = os.path.join(BASE_DIR, 'campaign.log')
OUTLOOK    = '/home/node/.openclaw/workspace/tools/outlook.py'
FROM_EMAIL = 'emily.loving@agenticscale.ai'
CC_EMAIL   = 'emily.loving@agenticscale.ai'

# ─── LOGGING ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger(__name__)

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def load_templates():
    with open(TEMPLATES) as f:
        return json.load(f)

def personalise(template_str, business_name, contact_name, city):
    first_name = contact_name.split()[0] if contact_name else 'there'
    return (template_str
            .replace('{{business_name}}', business_name)
            .replace('{{contact_name}}', first_name)
            .replace('{{city}}', city))

def get_pending(conn, industry=None, limit=None):
    query = "SELECT id, business_name, industry, city, state, contact_email, contact_name FROM targets WHERE email_status = 'pending'"
    params = []
    if industry:
        query += ' AND industry = ?'
        params.append(industry)
    query += ' ORDER BY id'
    if limit:
        query += ' LIMIT ?'
        params.append(limit)
    return conn.execute(query, params).fetchall()

def mark_sent(conn, target_id):
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("UPDATE targets SET email_status = 'sent', sent_at = ? WHERE id = ?", (now, target_id))
    conn.commit()

def send_email(to_email, subject, html_body, dry_run=False):
    """Send via outlook.py. Returns (success, output)."""
    cmd = ['python3', OUTLOOK, 'send', to_email, subject, html_body, CC_EMAIL]
    if dry_run:
        return True, '[DRY-RUN] Would execute: ' + ' '.join(cmd[:5]) + ' ...'
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip() or result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, 'Timeout after 30s'
    except Exception as e:
        return False, str(e)

# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='BusinessGrader Campaign Sender')
    parser.add_argument('--limit', type=int, default=None, help='Max emails to send')
    parser.add_argument('--industry', type=str, default=None,
                        choices=['legal', 'accounting', 'medical', 'dental', 'financial_services', 'other'],
                        help='Filter by industry')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be sent without sending')
    args = parser.parse_args()

    templates = load_templates()
    conn = sqlite3.connect(DB_PATH)

    targets = get_pending(conn, industry=args.industry, limit=args.limit)

    if not targets:
        log.info("No pending targets found (matching filters).")
        conn.close()
        return

    mode = '🔍 DRY-RUN' if args.dry_run else '🚀 LIVE'
    log.info(f"{'='*60}")
    log.info(f"BusinessGrader Campaign Sender — {mode}")
    log.info(f"Targets: {len(targets)}{' (filtered: ' + args.industry + ')' if args.industry else ''}")
    log.info(f"Rate limit: 1 email / 3 seconds")
    log.info(f"{'='*60}")

    sent_count = 0
    error_count = 0

    for idx, row in enumerate(targets, 1):
        target_id, business_name, industry, city, state, contact_email, contact_name = row

        tmpl = templates.get(industry, templates.get('other'))
        subject  = personalise(tmpl['subject'],  business_name, contact_name, city)
        html_body = personalise(tmpl['html_body'], business_name, contact_name, city)

        log.info(f"[{idx}/{len(targets)}] → {contact_email} | {business_name} ({industry}, {city} {state})")

        if args.dry_run:
            log.info(f"  Subject : {subject}")
            log.info(f"  To      : {contact_email}")
            log.info(f"  Contact : {contact_name}")
            log.info(f"  [DRY-RUN — no email sent]")
            sent_count += 1
        else:
            success, output = send_email(contact_email, subject, html_body)
            if success:
                mark_sent(conn, target_id)
                log.info(f"  ✅ Sent OK: {output[:80]}")
                sent_count += 1
            else:
                log.error(f"  ❌ Failed: {output[:120]}")
                error_count += 1

        # Rate limiting (skip delay on last item or dry-run)
        if not args.dry_run and idx < len(targets):
            time.sleep(3)

    log.info(f"{'='*60}")
    log.info(f"Campaign complete — Sent: {sent_count} | Errors: {error_count}")
    log.info(f"{'='*60}")
    conn.close()

if __name__ == '__main__':
    main()
