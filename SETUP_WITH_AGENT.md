# Setup Daily Crate with an agent

Copy/paste this prompt to the agent helping you set up the repo.

```text
You are helping me set up Daily Crate, a GitHub Actions + GitHub Pages music inbox crate.

Goal:
- Configure this repo so a scheduled GitHub Action scans my Gmail music emails with read-only access.
- Generate sanitized JSON files in data/.
- Publish the static UI in web/ via GitHub Pages.

Rules:
- Do not ask me to paste secrets into chat.
- Use Gmail read-only access only.
- Do not commit raw email bodies, OAuth tokens, .env files, or credentials.
- Store OAuth values only as GitHub Actions secrets.
- If Spotify is not configured, leave it disabled and still make Bandcamp work.
- Keep the repo working with sample data before touching real Gmail.

Steps:
1. Ask me for my GitHub username/repo and whether the repo/page can be public.
2. Ask for my music preferences: genres, sources, labels/clubs/newsletters, and whether I want Spotify now.
3. Copy config.example.yaml to config.yaml and edit only non-secret settings.
4. Run a sample generation: python -m src.generate --config config.yaml --sample fixtures/sample_emails.json
5. Verify web/data.json and web/archive.json exist and the page loads locally.
6. Guide me through creating Google OAuth credentials and running scripts/setup_google_oauth.py locally.
7. Add these GitHub Actions secrets: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN.
8. If Spotify is enabled, add Spotify secrets too, otherwise leave disabled.
9. Run the Daily Crate workflow manually in GitHub Actions.
10. Enable GitHub Pages from GitHub Actions and verify the page URL loads.
11. Only after manual run works, enable/keep the schedule.

Success criteria:
- The workflow finishes green.
- data/data.json and data/archive.json are generated without raw email bodies.
- The GitHub Pages site shows tracks or a useful empty state.
- Saves/listens work in the browser using localStorage.
```

## Tyler pilot defaults

Start simple:

- Bandcamp enabled
- Spotify disabled until the Bandcamp page works
- browser-local saves/listens
- no raw snippets unless the repo/page is private
