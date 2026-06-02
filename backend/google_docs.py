"""Google Docs and Sheets integration for the Courtroom backend.

All operations are **no-ops** when the required env vars are absent so the
rest of the backend starts cleanly without credentials.
"""

import base64
import json
import os
import tempfile
from datetime import datetime, timezone
from typing import Optional

_gdoc_enabled = False
_gsheet_enabled = False
_docs_service = None
_sheets_service = None

_GDOC_ID: Optional[str] = None
_GSHEET_ID: Optional[str] = None


def _load_credentials():
    """Build and cache Google API service clients.

    Credentials are read from GOOGLE_CREDENTIALS_JSON (base64-encoded service
    account JSON) or from GOOGLE_CREDENTIALS_FILE (path to the JSON file).
    """
    global _gdoc_enabled, _gsheet_enabled, _docs_service, _sheets_service
    global _GDOC_ID, _GSHEET_ID

    _GDOC_ID = os.getenv("GDOC_ID")
    _GSHEET_ID = os.getenv("GSHEET_ID")

    # Resolve credentials source.
    creds_json_b64 = os.getenv("GOOGLE_CREDENTIALS_JSON")
    creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE")

    if not creds_json_b64 and not creds_file:
        print("[google] GOOGLE_CREDENTIALS_JSON / GOOGLE_CREDENTIALS_FILE not set — "
              "Docs/Sheets integration disabled")
        return

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        scopes = [
            "https://www.googleapis.com/auth/documents",
            "https://www.googleapis.com/auth/spreadsheets",
        ]

        if creds_json_b64:
            # Decode base64 → temp file so the google client can load it.
            raw = base64.b64decode(creds_json_b64)
            creds_data = json.loads(raw)
            credentials = service_account.Credentials.from_service_account_info(
                creds_data, scopes=scopes
            )
        else:
            credentials = service_account.Credentials.from_service_account_file(
                creds_file, scopes=scopes
            )

        if _GDOC_ID:
            _docs_service = build("docs", "v1", credentials=credentials)
            _gdoc_enabled = True
            print(f"[google] Docs integration enabled (doc_id={_GDOC_ID})")
        else:
            print("[google] GDOC_ID not set — Docs integration disabled")

        if _GSHEET_ID:
            _sheets_service = build("sheets", "v4", credentials=credentials)
            _gsheet_enabled = True
            print(f"[google] Sheets integration enabled (sheet_id={_GSHEET_ID})")
        else:
            print("[google] GSHEET_ID not set — Sheets integration disabled")

    except ImportError:
        print("[google] google-api-python-client not installed — Docs/Sheets disabled")
    except Exception as exc:
        print(f"[google] Failed to initialise credentials: {exc}")


def init():
    """Call once at application startup to wire up credentials."""
    _load_credentials()


# ---------------------------------------------------------------------------
# Google Docs helpers
# ---------------------------------------------------------------------------

def append_to_doc(text: str) -> bool:
    """Append *text* as a new paragraph to the configured Google Doc.

    Returns True on success, False if integration is disabled or an error
    occurs.
    """
    if not _gdoc_enabled or _docs_service is None:
        return False

    try:
        # Fetch current end-of-document index.
        doc = _docs_service.documents().get(documentId=_GDOC_ID).execute()
        body_content = doc.get("body", {}).get("content", [])
        end_index = body_content[-1].get("endIndex", 1) - 1 if body_content else 1

        requests = [
            {
                "insertText": {
                    "location": {"index": end_index},
                    "text": text + "\n",
                }
            }
        ]
        _docs_service.documents().batchUpdate(
            documentId=_GDOC_ID, body={"requests": requests}
        ).execute()
        return True
    except Exception as exc:
        print(f"[google] Docs append error: {exc}")
        return False


def format_courtroom_block(
    prompt: str,
    response: str,
    timestamp: str,
    judge_opinions: Optional[list] = None,
) -> str:
    """Build the plaintext block that gets appended to the courtroom Doc."""
    sep = "─" * 60
    lines = [
        sep,
        f"⏱  {timestamp}",
        "",
        f"👤 PROMPT",
        prompt.strip(),
        "",
        f"🤖 GEMINI RESPONSE",
        response.strip(),
    ]

    if judge_opinions:
        lines.append("")
        lines.append("⚖️  JUDGE OPINIONS")
        for opinion in judge_opinions:
            lines.append(f"\n[{opinion['judge']}]")
            lines.append(opinion["text"].strip())

    lines.append(sep)
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Google Sheets helpers
# ---------------------------------------------------------------------------

def append_summary_row(summary: str, exchange_count: int) -> bool:
    """Append one summary row to the configured Google Sheet.

    Columns: timestamp (UTC ISO-8601) | summary | exchange_count

    Returns True on success, False if integration is disabled or an error
    occurs.
    """
    if not _gsheet_enabled or _sheets_service is None:
        return False

    try:
        ts = datetime.now(timezone.utc).isoformat()
        body = {"values": [[ts, summary, exchange_count]]}
        _sheets_service.spreadsheets().values().append(
            spreadsheetId=_GSHEET_ID,
            range="Sheet1!A:C",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body,
        ).execute()
        return True
    except Exception as exc:
        print(f"[google] Sheets append error: {exc}")
        return False
