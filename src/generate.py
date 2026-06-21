from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

from .bandcamp import embed_url, extract_bandcamp_urls, fetch_page_props, split_title, textify
from .config import load_config
from .gmail import EmailMessage, search_messages
from .scoring import score_item


def public_source(msg: EmailMessage, config: dict[str, Any]) -> dict[str, str]:
    gmail_cfg = config.get('gmail', {})
    return {
        'source_subject': msg.subject[:160] if gmail_cfg.get('include_subjects', True) else '',
        'source_from': msg.sender[:120] if gmail_cfg.get('include_senders', False) else '',
        'source_date': msg.date,
        'snippet': msg.snippet[:240] if gmail_cfg.get('include_snippets', False) else '',
    }


def load_sample(path: str | Path) -> list[EmailMessage]:
    data = json.loads(Path(path).read_text())
    out = []
    for i, item in enumerate(data.get('messages', data if isinstance(data, list) else [])):
        out.append(EmailMessage(
            id=str(item.get('id', i)),
            thread_id=str(item.get('thread_id', item.get('id', i))),
            subject=item.get('subject', ''),
            sender=item.get('sender', ''),
            date=item.get('date', ''),
            snippet=item.get('snippet', ''),
            body=item.get('body', ''),
        ))
    return out


def collect_items(messages: list[EmailMessage], config: dict[str, Any]) -> list[dict[str, Any]]:
    by_url: dict[str, dict[str, Any]] = {}
    for msg in messages:
        raw = msg.body + ' ' + msg.snippet
        plain = textify(raw)
        for url in extract_bandcamp_urls(raw):
            score, reasons = score_item(url, msg.subject, msg.snippet, plain, config)
            existing = by_url.get(url)
            if not existing or score > int(existing.get('score') or 0):
                by_url[url] = {
                    'url': url,
                    'score': score,
                    'reasons': reasons,
                    **public_source(msg, config),
                }
    max_links = int(config.get('bandcamp', {}).get('max_links_per_run') or 80)
    return sorted(by_url.values(), key=lambda x: (-int(x.get('score') or 0), x.get('url', '')))[:max_links]


def enrich_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for item in items:
        props, title = fetch_page_props(item['url'])
        artist, release = split_title(title, item['url'])
        item.update({
            'artist': artist,
            'release': release,
            'page_title': title,
            'embed_url': embed_url(props, item['url']),
            'artwork_url': props.get('artwork_url', ''),
            'bandcamp_item_type': props.get('item_type', ''),
            'bandcamp_item_id': props.get('item_id') or props.get('id') or '',
            'tracks': props.get('_trackinfo') or [],
            'fetch_error': props.get('_error', ''),
        })
        enriched.append(item)
    return enriched


def flatten_rows(items: list[dict[str, Any]], pull_date: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        base = {
            'parent_url': item.get('url', ''),
            'release': item.get('release', ''),
            'label_artist': item.get('artist', ''),
            'score': item.get('score', 0),
            'reasons': item.get('reasons') or [],
            'source_subject': item.get('source_subject', ''),
            'source_from': item.get('source_from', ''),
            'source_date': item.get('source_date', ''),
            'snippet': item.get('snippet', ''),
            'pull_date': pull_date,
            'platform': 'Bandcamp',
            'artwork_url': item.get('artwork_url', ''),
        }
        tracks = item.get('tracks') or []
        if tracks:
            for tr in tracks:
                raw_url = tr.get('url') or item.get('url')
                track_id = tr.get('id') or ''
                url = f"{raw_url}#track-{track_id}" if track_id and raw_url == item.get('url') else raw_url
                rows.append({**base,
                    'key': url,
                    'url': url,
                    'type': 'track',
                    'title': tr.get('title') or item.get('release') or '',
                    'artist': tr.get('artist') or item.get('artist') or '',
                    'duration': tr.get('duration') or 0,
                    'bandcamp_track_id': track_id,
                    'stream_url': tr.get('stream_url') or '',
                    'embed_url': f"https://bandcamp.com/EmbeddedPlayer/track={track_id}/size=large/bgcol=111111/linkcol=e6a23c/artwork=small/transparent=true/" if track_id else item.get('embed_url', ''),
                })
        else:
            rows.append({**base,
                'key': item.get('url', ''),
                'url': item.get('url', ''),
                'type': 'release',
                'title': item.get('release') or item.get('page_title') or '',
                'artist': item.get('artist') or '',
                'duration': 0,
                'bandcamp_track_id': '',
                'stream_url': '',
                'embed_url': item.get('embed_url', ''),
            })
    return rows


def load_archive(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {'items': {}, 'snapshots': []}
    try:
        data = json.loads(path.read_text())
        if not isinstance(data.get('items'), dict):
            data['items'] = {}
        if not isinstance(data.get('snapshots'), list):
            data['snapshots'] = []
        return data
    except Exception:
        return {'items': {}, 'snapshots': []}


def update_archive(path: Path, current_rows: list[dict[str, Any]], generated_at: str, meta: dict[str, Any], archive_days: int) -> dict[str, Any]:
    archive = load_archive(path)
    items = archive.setdefault('items', {})
    pull_date = generated_at[:10]
    for row in current_rows:
        key = row.get('key') or row.get('url')
        if not key:
            continue
        prev = items.get(key, {})
        pull_dates = list(dict.fromkeys((prev.get('pull_dates') or []) + [pull_date]))[-archive_days:]
        reasons = list(dict.fromkeys((prev.get('reasons') or []) + (row.get('reasons') or [])))
        merged = {**prev, **row}
        merged.update({
            'key': key,
            'first_seen_at': prev.get('first_seen_at') or generated_at,
            'last_seen_at': generated_at,
            'seen_count': int(prev.get('seen_count') or 0) + 1,
            'pull_dates': pull_dates,
            'reasons': reasons,
            'best_score': max(int(prev.get('best_score') or 0), int(row.get('score') or 0)),
        })
        items[key] = merged
    snap = {'generated_at': generated_at, 'pull_date': pull_date, **meta}
    archive['snapshots'] = [s for s in archive.get('snapshots', []) if s.get('generated_at') != generated_at]
    archive['snapshots'].append(snap)
    archive['snapshots'] = archive['snapshots'][-archive_days:]
    archive['updated_at'] = generated_at
    archive['summary'] = f"{len(items)} archived rows across {len(archive['snapshots'])} pulls."
    path.write_text(json.dumps(archive, indent=2, ensure_ascii=False))
    return archive


def write_web_data(data_dir: Path, web_dir: Path) -> None:
    web_dir.mkdir(parents=True, exist_ok=True)
    for name in ('data.json', 'archive.json'):
        src = data_dir / name
        if src.exists():
            (web_dir / name).write_text(src.read_text())


def generate(config_path: str | Path, sample_path: str | Path | None = None) -> dict[str, Any]:
    config = load_config(config_path)
    data_dir = Path(config.get('output', {}).get('data_dir', 'data'))
    web_dir = Path(config.get('output', {}).get('web_dir', 'web'))
    data_dir.mkdir(parents=True, exist_ok=True)
    messages = load_sample(sample_path) if sample_path else search_messages(
        query=config.get('gmail', {}).get('query', 'newer_than:3d bandcamp'),
        max_results=int(config.get('gmail', {}).get('max_emails') or 80),
        user_id='me',
    )
    items = enrich_items(collect_items(messages, config)) if config.get('bandcamp', {}).get('enabled', True) else []
    now = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')
    rows = flatten_rows(items, now[:10])
    meta = {'emails_reviewed': len(messages), 'links_found': len(items), 'items_found': len(items), 'rows_found': len(rows)}
    archive = update_archive(data_dir / 'archive.json', rows, now, meta, int(config.get('output', {}).get('archive_days') or 365))
    title = config.get('site', {}).get('title') or 'Daily Crate'
    data = {
        'site': config.get('site', {}),
        'generated_at': now,
        'emails_reviewed': len(messages),
        'items': items,
        'rows': rows,
        'archive_summary': archive.get('summary', ''),
        'summary': f'{title}: {len(items)} Bandcamp finds / {len(rows)} playable rows from {len(messages)} recent music emails.',
    }
    (data_dir / 'data.json').write_text(json.dumps(data, indent=2, ensure_ascii=False))
    write_web_data(data_dir, web_dir)
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.yaml')
    parser.add_argument('--sample', default=None, help='fixture JSON file for local tests')
    args = parser.parse_args()
    data = generate(args.config, args.sample)
    print(data['summary'])


if __name__ == '__main__':
    main()
