# Tyler Daily Crate GitHub Actions Pilot Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Create a friend-ready Daily Crate template repo that Tyler can configure with an agent and run via GitHub Actions/GitHub Pages.

**Architecture:** Python generator scans Gmail read-only or sample fixtures, extracts/enriches Bandcamp links, writes sanitized JSON, and a static UI reads that JSON from GitHub Pages. Browser localStorage handles save/listen state in v1.

**Tech Stack:** Python 3.11, Google Gmail API, PyYAML, static HTML/CSS/JS, GitHub Actions, GitHub Pages.

---

## Tasks

1. Scaffold repo with config, docs, package files, and tests.
2. Port Bandcamp extraction/enrichment into reusable modules.
3. Add static UI adapted for localStorage and relative JSON paths.
4. Add GitHub Actions workflows for generation and Pages deploy.
5. Verify sample generation, unit tests, and static page output.
6. Pilot with Tyler's config and Gmail OAuth secrets.
