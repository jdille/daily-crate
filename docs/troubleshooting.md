# Troubleshooting

## Workflow says Google secrets are missing

Add these repo secrets under GitHub → Settings → Secrets and variables → Actions:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`

## Page loads but no tracks show

- Run the sample fixture first.
- Check `config.yaml` Gmail query.
- Confirm the inbox actually has recent Bandcamp links.
- Run the workflow manually and inspect logs.

## Browser saves/listens disappeared

V1 stores state in browser `localStorage`, so state is per browser/device. Use export/import if added later, or wait for hosted sync in a future version.

## GitHub Pages 404

Make sure the `Deploy Pages` workflow ran green and Pages source is set to GitHub Actions.
