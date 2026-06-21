from __future__ import annotations

import html
import json
import re
import time
import urllib.parse
import urllib.request
from typing import Any


def clean_url(u: str) -> str | None:
    u = html.unescape(u).strip().strip('<>"\'()[]{}.,;')
    u = u.replace('\\u0026', '&')
    parsed = urllib.parse.urlparse(u)
    qs = urllib.parse.parse_qs(parsed.query)
    for key in ('url', 'u', 'q'):
        if key in qs and qs[key] and 'bandcamp.com' in qs[key][0]:
            u = qs[key][0]
            parsed = urllib.parse.urlparse(u)
            break
    if 'bandcamp.com' not in parsed.netloc.lower():
        return None
    return urllib.parse.urlunparse((parsed.scheme or 'https', parsed.netloc.lower(), parsed.path.rstrip('/'), '', '', ''))


def extract_bandcamp_urls(raw: str) -> list[str]:
    urls = set()
    for m in re.finditer(r'https?://[^\s<>"]+', raw):
        cu = clean_url(m.group(0))
        if cu:
            urls.add(cu)
    for m in re.finditer(r'href=["\']([^"\']*bandcamp\.com[^"\']*)', raw, re.I):
        cu = clean_url(m.group(1))
        if cu:
            urls.add(cu)
    return sorted(u for u in urls if is_listening_url(u))


def is_listening_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    bad_path = parsed.path.lower()
    if parsed.netloc == 'bandcamp.com':
        return False
    if any(skip in url for skip in ('/fan/', '/community', '/merch', '/music?s=', '/login', 'fan_unsubscribe')):
        return False
    if bad_path.endswith(('.gif', '.png', '.jpg', '.jpeg', '.webp', '.svg', '.css', '.js')):
        return False
    return True


def textify(raw: str) -> str:
    t = re.sub(r'<script[\s\S]*?</script>', ' ', raw, flags=re.I)
    t = re.sub(r'<style[\s\S]*?</style>', ' ', t, flags=re.I)
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', html.unescape(t)).strip()


def fetch_page_props(url: str, sleep: float = 0.08) -> tuple[dict[str, Any], str]:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Daily Crate (GitHub Actions; personal music inbox tool)'})
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read(900000).decode('utf-8', 'replace')
        if sleep:
            time.sleep(sleep)
        title = ''
        tm = re.search(r'<title[^>]*>(.*?)</title>', body, re.I | re.S)
        if tm:
            title = html.unescape(re.sub(r'\s+', ' ', tm.group(1))).strip()
        props: dict[str, Any] = {}
        m = re.search(r'<meta[^>]+name=["\']bc-page-properties["\'][^>]+content=["\']([^"\']+)["\']', body, re.I)
        if m:
            props.update(json.loads(html.unescape(m.group(1))))
        for pat in (
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        ):
            im = re.search(pat, body, re.I)
            if im:
                props.setdefault('artwork_url', html.unescape(im.group(1)))
                break
        tm = re.search(r'data-tralbum=["\']([^"\']+)["\']', body, re.I)
        if tm:
            tralbum = json.loads(html.unescape(tm.group(1)))
            props.setdefault('item_type', tralbum.get('item_type'))
            props.setdefault('item_id', tralbum.get('id'))
            props.setdefault('id', tralbum.get('id'))
            if tralbum.get('art_id'):
                props.setdefault('artwork_url', f"https://f4.bcbits.com/img/a{tralbum.get('art_id')}_5.jpg")
            props['_trackinfo'] = []
            parsed = urllib.parse.urlparse(url)
            base = f'{parsed.scheme}://{parsed.netloc}'
            for tr in tralbum.get('trackinfo') or []:
                f = tr.get('file') or {}
                link = tr.get('title_link') or ''
                props['_trackinfo'].append({
                    'num': tr.get('track_num'),
                    'title': tr.get('title') or '',
                    'artist': tr.get('artist') or '',
                    'duration': tr.get('duration'),
                    'url': urllib.parse.urljoin(base, link) if link else url,
                    'id': tr.get('track_id') or tr.get('id'),
                    'stream_url': f.get('mp3-128') or '',
                })
        return props, title
    except Exception as e:
        return {'_error': str(e)[:160]}, ''


def embed_url(props: dict[str, Any], url: str) -> str:
    item_type = str(props.get('item_type') or '').lower()
    item_id = props.get('item_id') or props.get('id')
    if not item_id:
        return ''
    kind = 'track' if item_type.startswith('t') or '/track/' in url else 'album'
    return f'https://bandcamp.com/EmbeddedPlayer/{kind}={item_id}/size=large/bgcol=111111/linkcol=e6a23c/artwork=small/transparent=true/'


def split_title(title: str, url: str) -> tuple[str, str]:
    title = (title or '').replace(' | Bandcamp', '').strip()
    artist = ''
    release = title
    if ' | ' in title:
        left, right = title.split(' | ', 1)
        release, artist = left.strip(), right.strip()
    elif ' by ' in title:
        release, artist = title.rsplit(' by ', 1)
        release, artist = release.strip(), artist.strip()
    if not release:
        release = urllib.parse.urlparse(url).path.strip('/').split('/')[-1].replace('-', ' ').title()
    return artist, release
