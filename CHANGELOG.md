# Changelog

All notable changes to the ai.doo marketing site will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [2026-04-02]

### Added

- **"Why self-hosted?" section** — six benefit cards (data never leaves, runs on your hardware,
  air-gap capable, predictable cost, compliance-ready, full auditability) inserted on the homepage
  between "What we do" and "How we work"; linked from desktop and mobile nav
- **Self-hosted Inter font** — variable WOFF2 (latin subset) at `/fonts/inter-latin.woff2`;
  declared in `style.css` via `@font-face`. Eliminates the only third-party CDN dependency on
  the site and removes all `fonts.googleapis.com` / `fonts.gstatic.com` requests

### Changed

- **Pilot pricing** — Pilot card now shows "from £3,000 — exact scope agreed upfront" instead
  of "pricing on request"; improves lead pre-qualification and reduces email roundtrips
- **Chat API system prompt** — updated with pilot pricing figure and "Why self-hosted" talking
  points so the chat widget reflects current site content
- **`style.css`** — now committed and tracked; `@font-face` declaration added at top of file

### Fixed

- **Privacy policy — chat history disclosure** (Section 4a) — corrected inaccurate statement
  ("no conversation history is stored") to accurately reflect that session history is sent to
  OpenAI per message for context but is not stored server-side
- **Privacy policy — Section 3** — updated from "Google Fonts" (third-party CDN) to "Fonts —
  self-hosted, no external requests" following the font migration
