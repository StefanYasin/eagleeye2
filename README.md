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
