from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

GMAIL_READONLY_SCOPE = 'https://www.googleapis.com/auth/gmail.readonly'


@dataclass
class EmailMessage:
    id: str
    thread_id: str
    subject: str
    sender: str
    date: str
    snippet: str
    body: str


def _decode(data: str | None) -> str:
    if not data:
        return ''
    data += '=' * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data.encode()).decode('utf-8', 'replace')


def _walk_parts(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if not payload:
        return []
    if payload.get('parts'):
        out: list[dict[str, Any]] = []
        for part in payload.get('parts') or []:
            out.extend(_walk_parts(part))
        return out
    return [payload]


def _headers(payload: dict[str, Any]) -> dict[str, str]:
    out = {}
    for h in payload.get('headers') or []:
        out[h.get('name', '').lower()] = h.get('value', '')
    return out


def _extract_body(payload: dict[str, Any]) -> str:
    bodies: list[str] = []
    for part in _walk_parts(payload):
        mt = part.get('mimeType', '')
        data = (part.get('body') or {}).get('data')
        if data and (mt.startswith('text/') or mt == ''):
            bodies.append(_decode(data))
    return '\n'.join(bodies)


def gmail_service():
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    refresh_token = os.environ.get('GOOGLE_REFRESH_TOKEN')
    missing = [k for k, v in {
        'GOOGLE_CLIENT_ID': client_id,
        'GOOGLE_CLIENT_SECRET': client_secret,
        'GOOGLE_REFRESH_TOKEN': refresh_token,
    }.items() if not v]
    if missing:
        raise RuntimeError(f'missing required Google secrets: {", ".join(missing)}')
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=client_id,
        client_secret=client_secret,
        scopes=[GMAIL_READONLY_SCOPE],
    )
    return build('gmail', 'v1', credentials=creds, cache_discovery=False)


def search_messages(query: str, max_results: int = 80, user_id: str = 'me') -> list[EmailMessage]:
    service = gmail_service()
    resp = service.users().messages().list(userId=user_id, q=query, maxResults=max_results).execute()
    refs = resp.get('messages') or []
    messages: list[EmailMessage] = []
    for ref in refs[:max_results]:
        msg = service.users().messages().get(userId=user_id, id=ref['id'], format='full').execute()
        payload = msg.get('payload') or {}
        hs = _headers(payload)
        messages.append(EmailMessage(
            id=msg.get('id', ''),
            thread_id=msg.get('threadId', ''),
            subject=hs.get('subject', ''),
            sender=hs.get('from', ''),
            date=hs.get('date', ''),
            snippet=msg.get('snippet', ''),
            body=_extract_body(payload),
        ))
    return messages
