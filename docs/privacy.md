# Privacy notes

Daily Crate is designed for least privilege and static hosting.

## Gmail access

Use only Gmail read-only OAuth scope:

`https://www.googleapis.com/auth/gmail.readonly`

The app should never send, delete, archive, label, or mark email read/unread.

## Secrets

Never commit:

- OAuth client secret files
- refresh tokens
- `.env` files
- GitHub tokens

Use GitHub Actions secrets.

## Published data

If GitHub Pages is public, assume `web/data.json` and `web/archive.json` are public too.

Defaults minimize exposure:

- raw email bodies are never written
- snippets are off by default
- senders are off by default
- subjects can be disabled in `config.yaml`

Public Bandcamp metadata and page/embed links are stored so the UI can open or embed tracks.

Direct Bandcamp preview stream URLs are **not** published by default because those URLs include signed, expiring query tokens. Set `bandcamp.publish_direct_stream_urls: true` only for a private site if native `<audio>` playback is worth exposing those temporary URLs.