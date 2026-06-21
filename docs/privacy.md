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

Public Bandcamp metadata and links are stored so the UI can play/queue tracks.
