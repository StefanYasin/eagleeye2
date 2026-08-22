# EagleEye 2.0

Find a person's social profiles from a face photo. A modern, maintained
successor to [ThoughtfulDev/EagleEye](https://github.com/ThoughtfulDev/EagleEye)
(which has been unmaintained since 2021).

**Pipeline:** photo → face embedding (deepface) → generate candidate handles
from the name → probe profile URLs → download candidate avatars → face-verify
against the reference photo → scored report (JSON + terminal table).

## Install

Python 3.12+ recommended (deepface needs TensorFlow/torch, which lag on newer
CPython). On Windows, install inside WSL2 Ubuntu:

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv -e .
# deepface extras on TF 2.21:
uv pip install --python .venv tf-keras "opencv-python==4.12.0.88"
```

## Usage

```bash
# Name-based discovery (generates handles from the name):
eagleeye2 scan --photo known/photo.jpg --name "Barack Obama" --sites instagram,threads

# Explicit URL list (one per line, # comments allowed):
eagleeye2 scan --photo known/photo.jpg --urls profiles.txt

# Choose a model (Facenet default; VGG-Face most accurate, heavier):
eagleeye2 scan --photo known/photo.jpg --name "Barack Obama" --model ArcFace

# JSON report:
eagleeye2 scan --photo known/photo.jpg --name "Barack Obama" --out report.json
```

Example output:

```
EagleEye 2.0 — scan for Barack Obama (model: Facenet)
┌───────────┬──────────────┬──────────────────────────────────┬────────┬──────────┬──────────┬───────────────┐
│ Site      │ Handle       │ URL                              │ Status │ Distance │ Verified │ Note          │
├───────────┼──────────────┼──────────────────────────────────┼────────┼──────────┼──────────┼───────────────┤
│ instagram │ barackobama  │ https://www.instagram.com/...    │ 200    │ 0.234    │ YES      │ verified=True │
│ threads   │ barackobama  │ https://www.threads.net/@...     │ 200    │ 0.251    │ YES      │ verified=True │
└───────────┴──────────────┴──────────────────────────────────┴────────┴──────────┴──────────┴───────────────┘
1 verified match(es) out of 10 candidate(s).
```

## Architecture

```
src/eagleeye2/
  cli.py        typer CLI (scan / version)
  pipeline.py   orchestration: embed -> probe -> verify -> report
  faces.py      deepface wrapper (lazy import: fast CLI startup)
  discovery.py  handle generation, site rules, URL probing, og:image parsing
  report.py     rich terminal table + JSON writer
tests/          unit tests for handle generation (no network)
```

## Limitations & roadmap

- **Login walls / soft-404s**: Instagram, X and TikTok gate anonymous access;
  probe results vary over time and by network. The verifier only scores
  candidates whose profile page exposes an `og:image` avatar.
- **Reverse-image leg**: EagleEye's photo → "where else does this face appear"
  is not yet implemented. Roadmap: Google Lens / Yandex browser helper, then
  optional API integrations (Google Custom Search, PimEyes-style services).
- **Local dataset search**: embed a folder of images and rank by distance —
  useful for finding a person in your own collected corpus.
- **Detector**: currently `opencv` (fast, CPU-friendly). Add `retinaface` /
  `mtcnn` backends behind a flag for higher recall on hard images.

## Legal / ethics

Only use this tool on publicly available information and for lawful purposes.
Respect platform ToS; many sites prohibit automated scraping. Face-search
technology has real privacy implications — use it responsibly.

## License

MIT

## Commands

```bash
eagleeye2 scan --photo face.jpg --name "Full Name" --sites instagram,threads,x,github  # profile discovery
eagleeye2 scan --photo face.jpg --urls profiles.txt --purpose investigation            # explicit URLs
eagleeye2 exif --photo face.jpg                                                         # EXIF/GPS forensics
eagleeye2 revimg --photo face.jpg                                                       # reverse image search (opens engines)
```

Every scan requires `--purpose` (investigation | trust_safety | missing_person | research | background | other) — the legal/ethical gate.

## Try it in one command

```bash
bash try-eagleeye.sh face.jpg "Full Name" instagram,threads,x,github,linkedin,youtube
```

## Coverage

**69 platforms** probed + face-verified: Instagram, Threads, X, TikTok, YouTube, Facebook, LinkedIn, GitHub, Reddit, Twitch, Steam, Telegram, Spotify, StackOverflow, HuggingFace, npm, PyPI, Mastodon, and more.

## Feature roadmap (issue #1)

- [x] 69-site coverage
- [x] EXIF/GPS extraction
- [x] Reverse image search (browser method; API engines blocked by bot detection — paid layer planned)
- [x] Ethics gate
- [ ] Username mode (given a username, find all accounts — Sherlock/Maigret core)
- [ ] Recursive search
- [ ] HTML/PDF reports
- [ ] Web UI
- [ ] Paid: Pipl/TruePeopleSearch, Bright Data, Google Vision
