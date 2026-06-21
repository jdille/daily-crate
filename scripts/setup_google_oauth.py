#!/usr/bin/env python3
from __future__ import annotations

import argparse

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPE = ['https://www.googleapis.com/auth/gmail.readonly']


def main() -> None:
    parser = argparse.ArgumentParser(description='Create a Gmail read-only OAuth refresh token for Daily Crate.')
    parser.add_argument('--client-secrets', required=True, help='Path to OAuth desktop client JSON downloaded from Google Cloud')
    args = parser.parse_args()
    flow = InstalledAppFlow.from_client_secrets_file(args.client_secrets, SCOPE)
    creds = flow.run_local_server(port=0)
    print('\nAdd these to GitHub Actions secrets. Do not paste them into chat.\n')
    print('GOOGLE_CLIENT_ID=' + (creds.client_id or ''))
    print('GOOGLE_CLIENT_SECRET=' + (creds.client_secret or ''))
    print('GOOGLE_REFRESH_TOKEN=' + (creds.refresh_token or ''))


if __name__ == '__main__':
    main()
