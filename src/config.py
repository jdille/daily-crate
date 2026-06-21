from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

DEFAULT_CONFIG: dict[str, Any] = {
    'profile': {'display_name': 'Daily Crate', 'timezone': 'UTC'},
    'gmail': {
        'account': 'me',
        'query': 'newer_than:3d (bandcamp OR "bandcamp.com")',
        'max_emails': 80,
        'include_subjects': True,
        'include_senders': False,
        'include_snippets': False,
    },
    'music': {
        'preferred_terms': ['techno', 'house', 'ambient', 'experimental'],
        'priority_sources': ['Bandcamp'],
        'bonus_terms': {'label': 6, 'club': 6, 'vinyl': 5, 'remix': 4},
    },
    'bandcamp': {'enabled': True, 'max_links_per_run': 80},
    'spotify': {'enabled': False, 'playlist_id': '', 'max_tracks_per_run': 25},
    'site': {'title': 'Daily Crate', 'subtitle': 'music from your inbox'},
    'output': {'data_dir': 'data', 'web_dir': 'web', 'archive_days': 365},
}


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f'config file not found: {p}')
    loaded = yaml.safe_load(p.read_text()) or {}
    return deep_merge(DEFAULT_CONFIG, loaded)
