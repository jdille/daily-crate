from src.bandcamp import clean_url, extract_bandcamp_urls
from src.generate import flatten_rows
from src.scoring import score_item


def test_extract_bandcamp_urls_filters_generic():
    raw = 'listen https://artist.bandcamp.com/album/foo image https://f4.bcbits.com/img/a123.jpg homepage https://bandcamp.com'
    urls = extract_bandcamp_urls(raw)
    assert urls == ['https://artist.bandcamp.com/album/foo']


def test_score_uses_config_terms():
    cfg = {'music': {'preferred_terms': ['ambient'], 'priority_sources': ['Boomkat'], 'bonus_terms': {'vinyl': 5}}}
    score, reasons = score_item('https://x.bandcamp.com/album/y', 'Boomkat ambient vinyl', '', '', cfg)
    assert score > 70
    assert 'ambient' in reasons
    assert 'Boomkat' in reasons


def test_flattened_track_rows_keep_release_artwork():
    rows = flatten_rows([
        {
            'url': 'https://artist.bandcamp.com/album/release',
            'release': 'Release',
            'artist': 'Artist',
            'score': 88,
            'artwork_url': 'https://f4.bcbits.com/img/a123_5.jpg',
            'tracks': [{'title': 'Track One', 'id': 42, 'stream_url': 'https://example.com/stream.mp3'}],
        }
    ], '2026-06-21')

    assert rows[0]['type'] == 'track'
    assert rows[0]['title'] == 'Track One'
    assert rows[0]['artwork_url'] == 'https://f4.bcbits.com/img/a123_5.jpg'
