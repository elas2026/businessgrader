import os
import json
import datetime
import threading
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", 8080))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Microsoft Graph API config ────────────────────────────────────────────────
GRAPH_TENANT  = os.environ.get("GRAPH_TENANT", "")
GRAPH_CLIENT  = os.environ.get("GRAPH_CLIENT", "")
GRAPH_SECRET  = os.environ.get("GRAPH_SECRET", "")
SENDER_EMAIL  = os.environ.get("SENDER_EMAIL", "jenny.cole@agenticsprint.ai")
NOTIFY_EMAIL  = os.environ.get("NOTIFY_EMAIL", "emily.loving@agenticscale.ai")
SITE_URL      = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "businessgrader-web-production-56e0.up.railway.app")
SHEETS_WEBHOOK = os.environ.get("SHEETS_WEBHOOK", "https://script.google.com/macros/s/AKfycbztbdipdOiJIT8UsZbbRMnMrTiJu4YK6YZJHdaJP0yFtAnuZLMkVaH18s-wVN24L8hvbQ/exec")

# ── In-memory lead log (also printed to Railway logs) ────────────────────────
leads = []
events = []


def log_to_sheets(payload):
    """POST lead/event data to Google Sheets via Apps Script webhook."""
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(SHEETS_WEBHOOK, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        print(f"[SHEETS] Logged: {payload.get('email','event')}")
    except Exception as e:
        print(f"[SHEETS] Failed: {e}")


def get_graph_token():
    """Get Microsoft Graph API access token."""
    url  = f"https://login.microsoftonline.com/{GRAPH_TENANT}/oauth2/v2.0/token"
    data = urllib.parse.urlencode({
        "client_id":     GRAPH_CLIENT,
        "client_secret": GRAPH_SECRET,
        "scope":         "https://graph.microsoft.com/.default",
        "grant_type":    "client_credentials"
    }).encode()
    req  = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
    return resp["access_token"]


def send_notification(subject, html_body):
    """Send email via Microsoft Graph API."""
    try:
        token = get_graph_token()
        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": html_body},
                "toRecipients": [{"emailAddress": {"address": NOTIFY_EMAIL}}]
            }
        }
        data = json.dumps(payload).encode()
        req  = urllib.request.Request(
            f"https://graph.microsoft.com/v1.0/users/{SENDER_EMAIL}/sendMail",
            data=data, method="POST",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=10)
        print(f"[NOTIFY] Email sent via Graph API: {subject}")
    except Exception as e:
        print(f"[NOTIFY] Graph API email failed: {e}")


def notify_new_lead(email, url, company=None, name=None):
    now_aedt = datetime.datetime.utcnow() + datetime.timedelta(hours=11)
    subject  = f"🔥 New BusinessGrader Lead — {email}"
    body = f"""
    <h2 style="color:#FF5A00;">New Lead from BusinessGrader</h2>
    <table style="border-collapse:collapse;font-family:Arial,sans-serif;font-size:14px;">
      <tr><td style="padding:6px 12px;font-weight:bold;">Email</td><td style="padding:6px 12px;">{email}</td></tr>
      {"<tr><td style='padding:6px 12px;font-weight:bold;'>Name</td><td style='padding:6px 12px;'>" + name + "</td></tr>" if name else ""}
      {"<tr><td style='padding:6px 12px;font-weight:bold;'>Company URL</td><td style='padding:6px 12px;'>" + url + "</td></tr>" if url else ""}
      <tr><td style="padding:6px 12px;font-weight:bold;">Time (AEDT)</td><td style="padding:6px 12px;">{now_aedt.strftime('%d %b %Y %I:%M %p')}</td></tr>
      <tr><td style="padding:6px 12px;font-weight:bold;">Total Leads</td><td style="padding:6px 12px;">{len(leads)}</td></tr>
    </table>
    <p style="margin-top:16px;font-size:13px;color:#888;">BusinessGrader · AgenticScale</p>
    """
    send_notification(subject, body)


def notify_call_booking(email=None, url=None):
    now_aedt = datetime.datetime.utcnow() + datetime.timedelta(hours=11)
    subject  = "📅 BusinessGrader — Someone Clicked Book a Call!"
    body = f"""
    <h2 style="color:#FF5A00;">Call Booking Click — BusinessGrader</h2>
    <p>Someone clicked the <strong>Book a Call</strong> button on BusinessGrader.</p>
    <table style="border-collapse:collapse;font-family:Arial,sans-serif;font-size:14px;">
      {"<tr><td style='padding:6px 12px;font-weight:bold;'>Email</td><td style='padding:6px 12px;'>" + email + "</td></tr>" if email else ""}
      {"<tr><td style='padding:6px 12px;font-weight:bold;'>URL Graded</td><td style='padding:6px 12px;'>" + url + "</td></tr>" if url else ""}
      <tr><td style="padding:6px 12px;font-weight:bold;">Time (AEDT)</td><td style="padding:6px 12px;">{now_aedt.strftime('%d %b %Y %I:%M %p')}</td></tr>
    </table>
    <p style="margin-top:16px;font-size:13px;color:#888;">BusinessGrader · AgenticScale</p>
    """
    send_notification(subject, body)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{datetime.datetime.utcnow().isoformat()}] {format % args}")

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._serve_index()
        elif self.path == "/leads":
            self._serve_leads()
        elif self.path == "/health":
            self._serve_health()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

    def do_POST(self):
        if self.path == "/submit-email":
            self._handle_email_submit()
        elif self.path == "/track-event":
            self._handle_track_event()
        elif self.path == "/book-call":
            self._handle_book_call()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _serve_index(self):
        index_path = os.path.join(BASE_DIR, "index.html")
        try:
            with open(index_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            # Track page visit
            events.append({"type": "page_view", "timestamp": datetime.datetime.utcnow().isoformat()})
        except FileNotFoundError:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"index.html not found")

    def _serve_leads(self):
        """Simple leads dashboard — shows all captured leads."""
        now_aedt = datetime.datetime.utcnow() + datetime.timedelta(hours=11)
        page_views = sum(1 for e in events if e.get("type") == "page_view")
        call_clicks = sum(1 for e in events if e.get("type") == "book_call_click")

        rows = "".join(
            f"<tr><td>{l.get('email','')}</td><td>{l.get('name','—')}</td><td>{l.get('url','—')}</td><td>{l.get('timestamp','')[:16].replace('T',' ')}</td></tr>"
            for l in reversed(leads)
        )
        html = f"""<!DOCTYPE html><html><head><title>BusinessGrader Leads</title>
        <style>body{{font-family:Arial,sans-serif;padding:24px;background:#f7f8fa;}}
        h1{{color:#FF5A00;}}table{{border-collapse:collapse;width:100%;background:#fff;border-radius:8px;overflow:hidden;}}
        th{{background:#03103D;color:#fff;padding:10px 14px;text-align:left;}}
        td{{padding:10px 14px;border-bottom:1px solid #eee;}}
        .stat{{display:inline-block;background:#fff;border-radius:8px;padding:16px 24px;margin:8px;box-shadow:0 1px 4px rgba(0,0,0,0.08);}}
        .stat span{{font-size:28px;font-weight:bold;color:#FF5A00;display:block;}}
        </style></head><body>
        <h1>📊 BusinessGrader — Lead Dashboard</h1>
        <p style="color:#888;">Last updated: {now_aedt.strftime('%d %b %Y %I:%M %p')} AEDT</p>
        <div style="margin:16px 0;">
          <div class="stat"><span>{len(leads)}</span>Total Leads</div>
          <div class="stat"><span>{page_views}</span>Page Views</div>
          <div class="stat"><span>{call_clicks}</span>Call Booking Clicks</div>
          <div class="stat"><span>{round(len(leads)/page_views*100) if page_views else 0}%</span>Conversion Rate</div>
        </div>
        <table><thead><tr><th>Email</th><th>Name</th><th>Company URL</th><th>Time (UTC)</th></tr></thead>
        <tbody>{rows if rows else "<tr><td colspan='4' style='text-align:center;color:#888;padding:24px;'>No leads yet</td></tr>"}</tbody>
        </table></body></html>"""
        content = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _serve_health(self):
        data = json.dumps({"ok": True, "leads": len(leads), "events": len(events)}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def _handle_email_submit(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data  = json.loads(body)
            email = data.get("email", "").strip()
            url   = data.get("url", "").strip()
            name  = data.get("name", "").strip()

            if email and "@" in email:
                record = {
                    "email":     email,
                    "name":      name,
                    "url":       url,
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                }
                leads.append(record)
                print(f"[LEAD] {email} | {url} | {name}")
                # Fire-and-forget — email + Google Sheets (non-blocking)
                threading.Thread(target=notify_new_lead, args=(email, url), kwargs={"name": name}, daemon=True).start()
                threading.Thread(target=log_to_sheets, args=({"email": email, "name": name, "url": url, "event": "lead"},), daemon=True).start()

            response = json.dumps({"ok": True}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(response)
        except Exception as e:
            print(f"[ERROR] email submit: {e}")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"ok": false}')

    def _handle_track_event(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data  = json.loads(body)
            event = data.get("event", "unknown")
            meta  = data.get("meta", {})
            record = {
                "type":      event,
                "meta":      meta,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }
            events.append(record)
            print(f"[EVENT] {event} | {meta}")
            response = json.dumps({"ok": True}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(response)
        except Exception as e:
            print(f"[ERROR] track event: {e}")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"ok": false}')

    def _handle_book_call(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data  = json.loads(body)
            email = data.get("email", "").strip()
            url   = data.get("url", "").strip()
            events.append({"type": "book_call_click", "email": email, "url": url, "timestamp": datetime.datetime.utcnow().isoformat()})
            print(f"[BOOK-CALL] {email} | {url}")
            threading.Thread(target=notify_call_booking, kwargs={"email": email, "url": url}, daemon=True).start()
            threading.Thread(target=log_to_sheets, args=({"email": email, "url": url, "event": "book_call_click"},), daemon=True).start()
            response = json.dumps({"ok": True}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(response)
        except Exception as e:
            print(f"[ERROR] book call: {e}")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"ok": false}')


if __name__ == "__main__":
    print(f"[START] BusinessGrader server on port {PORT}")
    print(f"[START] Notify email: {NOTIFY_EMAIL}")
    print(f"[START] SMTP configured: {'YES' if SMTP_PASS else 'NO — set SMTP_PASS env var'}")
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()
