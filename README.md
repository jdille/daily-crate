# Daily Crate

Turn a music-heavy Gmail inbox into a daily listening crate.

Daily Crate scans recent music emails, extracts Bandcamp links, enriches them with public Bandcamp metadata, writes sanitized JSON, and publishes a static listening UI with GitHub Pages.

## What it does

- Reads Gmail with read-only OAuth credentials.
- Finds Bandcamp links from music newsletters / labels / clubs.
- Parses Bandcamp public page metadata, tracklists, preview streams, embeds, and album art.
- Builds `data/data.json` and `data/archive.json`.
- Serves `web/` as a static crate UI.
- Stores saves/listens in your browser's `localStorage` for v1.

## What it does not do

- It does not need a server, droplet, or Tailscale.
- It does not send, delete, archive, label, or mark email read.
- It does not commit raw email bodies.
- It does not store secrets in files.

## Quick start with an agent

1. Click **Use this template** or fork this repo.
2. Open `SETUP_WITH_AGENT.md` and paste the agent prompt into Claude/Codex/etc.
3. Copy `config.example.yaml` to `config.yaml` and adjust preferences.
4. Add GitHub Actions secrets for Google OAuth.
5. Run the `Daily Crate` workflow manually.
6. Enable GitHub Pages from GitHub Actions.

## Local sample run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml
python -m src.generate --config config.yaml --sample fixtures/sample_emails.json
python -m http.server 8080 -d web
```

Then open http://localhost:8080.

## Real Gmail run

Set secrets/env vars:

```bash
export GOOGLE_CLIENT_ID=...
export GOOGLE_CLIENT_SECRET=...
export GOOGLE_REFRESH_TOKEN=...
python -m src.generate --config config.yaml
```

Use `scripts/setup_google_oauth.py` to create a refresh token locally. Do **not** paste tokens into chat.

## Privacy

GitHub Pages may be public depending on repo/settings. Daily Crate minimizes data in generated JSON by default:

- no raw email body
- no full sender address unless configured
- only short source subject/date/category
- public Bandcamp metadata and page/embed URLs
- direct Bandcamp preview stream URLs are off by default because they include signed, expiring query tokens; use `bandcamp.publish_direct_stream_urls: true` only for a private site if you want native `<audio>` playback
See `docs/privacy.md`.
