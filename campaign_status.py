#!/usr/bin/env python3
"""
BusinessGrader Campaign Dashboard
Usage: python3 campaign_status.py
"""

import sqlite3
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'targets.db')

RATE_SECONDS = 3  # seconds per email

def fmt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"

def bar(pct, width=30):
    filled = int(width * pct / 100)
    return '█' * filled + '░' * (width - filled)

def main():
    if not os.path.exists(DB_PATH):
        print(f"❌  Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # ── Totals ────────────────────────────────────────────────────────────────
    total    = cur.execute("SELECT COUNT(*) FROM targets").fetchone()[0]
    sent     = cur.execute("SELECT COUNT(*) FROM targets WHERE email_status = 'sent'").fetchone()[0]
    opened   = cur.execute("SELECT COUNT(*) FROM targets WHERE email_status = 'opened'").fetchone()[0]
    replied  = cur.execute("SELECT COUNT(*) FROM targets WHERE email_status = 'replied'").fetchone()[0]
    converted= cur.execute("SELECT COUNT(*) FROM targets WHERE email_status = 'converted'").fetchone()[0]
    pending  = cur.execute("SELECT COUNT(*) FROM targets WHERE email_status = 'pending'").fetchone()[0]

    sent_pct = (sent / total * 100) if total else 0

    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          BusinessGrader — Campaign Dashboard                 ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # ── Overall Progress ──────────────────────────────────────────────────────
    print("  OVERALL PROGRESS")
    print(f"  {bar(sent_pct)} {sent_pct:.1f}%")
    print()
    print(f"  {'Total targets:':<22} {total:>6}")
    print(f"  {'Pending:':<22} {pending:>6}")
    print(f"  {'Sent:':<22} {sent:>6}   ({sent_pct:.1f}%)")
    print(f"  {'Opened:':<22} {opened:>6}")
    print(f"  {'Replied:':<22} {replied:>6}")
    print(f"  {'Converted:':<22} {converted:>6}")
    print()

    # ── Industry Breakdown ────────────────────────────────────────────────────
    print("  BREAKDOWN BY INDUSTRY")
    print(f"  {'Industry':<24} {'Total':>6} {'Sent':>6} {'Pending':>8} {'Progress'}")
    print(f"  {'─'*24} {'─'*6} {'─'*6} {'─'*8} {'─'*20}")

    by_industry = cur.execute("""
        SELECT
            industry,
            COUNT(*) as total,
            SUM(CASE WHEN email_status = 'sent' THEN 1 ELSE 0 END) as sent,
            SUM(CASE WHEN email_status = 'pending' THEN 1 ELSE 0 END) as pending
        FROM targets
        GROUP BY industry
        ORDER BY total DESC
    """).fetchall()

    for ind, t, s, p in by_industry:
        pct = (s / t * 100) if t else 0
        mini_bar = '█' * int(pct / 10) + '░' * (10 - int(pct / 10))
        print(f"  {ind:<24} {t:>6} {s:>6} {p:>8}   {mini_bar} {pct:.0f}%")

    print()

    # ── Time Estimate ─────────────────────────────────────────────────────────
    if pending > 0:
        est_seconds = pending * RATE_SECONDS
        print(f"  ⏱  Estimated time to complete: {fmt_time(est_seconds)} ({pending} emails × {RATE_SECONDS}s)")
    else:
        print("  ✅ All emails sent!")
    print()

    # ── Recent Sends ─────────────────────────────────────────────────────────
    recent = cur.execute("""
        SELECT business_name, industry, city, state, contact_email, sent_at
        FROM targets
        WHERE email_status = 'sent' AND sent_at IS NOT NULL
        ORDER BY sent_at DESC
        LIMIT 10
    """).fetchall()

    if recent:
        print("  RECENT SENDS (last 10)")
        print(f"  {'Business':<30} {'Industry':<16} {'Location':<18} {'Sent At'}")
        print(f"  {'─'*30} {'─'*16} {'─'*18} {'─'*20}")
        for biz, ind, city, state, email, sent_at in recent:
            loc = f"{city}, {state}"
            ts = sent_at[:16].replace('T', ' ') if sent_at else 'N/A'
            print(f"  {biz[:29]:<30} {ind:<16} {loc[:17]:<18} {ts}")
    else:
        print("  No emails sent yet.")

    print()
    print("═" * 64)
    print()
    conn.close()

if __name__ == '__main__':
    main()
