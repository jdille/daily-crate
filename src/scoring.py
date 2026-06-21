from __future__ import annotations

import re
from typing import Any


def score_item(url: str, subject: str, snippet: str, body_text: str, config: dict[str, Any]) -> tuple[int, list[str]]:
    blob = ' '.join([url, subject, snippet, body_text[:4000]]).lower()
    score = 50
    reasons: list[str] = []

    for source in config.get('music', {}).get('priority_sources', []) or []:
        if str(source).lower() in blob:
            score += 15
            reasons.append(str(source))

    for term in config.get('music', {}).get('preferred_terms', []) or []:
        t = str(term).lower()
        if t and t in blob:
            score += 10
            reasons.append(str(term))

    for term, bonus in (config.get('music', {}).get('bonus_terms') or {}).items():
        if re.search(rf'\b{re.escape(str(term).lower())}\b', blob):
            score += int(bonus or 0)
            reasons.append(str(term))

    if '/track/' in url:
        score += 8
        reasons.append('track')
    if '/album/' in url:
        score += 6
        reasons.append('album')
    if not reasons:
        reasons.append('Bandcamp')
    return score, list(dict.fromkeys(reasons))[:8]
