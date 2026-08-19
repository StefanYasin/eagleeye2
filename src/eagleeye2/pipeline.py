"""Orchestrate: photo -> embedding -> probe profiles -> verify faces -> report."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Optional

import httpx

from . import discovery
from .faces import embed, verify
from .report import render_table


def _upscale_small_avatar(path: Path) -> None:
    """Upscale tiny avatar images so face detection can find the face."""
    import cv2

    img = cv2.imread(str(path))
    if img is None:
        return
    h, w = img.shape[:2]
    if min(h, w) < 300:
        scale = max(1.0, 300 / min(h, w))
        img = cv2.resize(
            img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC
        )
        cv2.imwrite(str(path), img)


def run_scan(
    photo: Path,
    name: str,
    sites: list[str],
    model: str,
    out: Optional[Path],
    urls_file: Optional[Path],
) -> dict:
    # Fail fast: the reference photo must contain a detectable face.
    embed(photo, model)

    results = []
    candidates: list[discovery.Candidate] = []
    if urls_file:
        for line in urls_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                candidates.append(
                    discovery.Candidate(site="custom", handle="", url=line)
                )
    else:
        candidates = discovery.build_candidates(name, sites)

    with tempfile.TemporaryDirectory(prefix="eagleeye2-") as tmp:
        tmp = Path(tmp)
        for i, cand in enumerate(candidates):
            probe = discovery.probe(cand.url)
            entry = {
                "site": cand.site or "custom",
                "handle": cand.handle or "",
                "url": cand.url,
                "status": probe.status,
                "note": probe.note,
                "distance": None,
                "verified": None,
            }
            if probe.og_image:
                try:
                    avatar = tmp / f"cand_{i}.jpg"
                    resp = httpx.get(
                        probe.og_image,
                        headers=discovery.UA,
                        follow_redirects=True,
                        timeout=discovery.TIMEOUT,
                    )
                    if resp.status_code in (403, 404) and probe.og_image_src:
                        # Some CDNs sign URLs per-size; retry with the original.
                        resp = httpx.get(
                            probe.og_image_src,
                            headers=discovery.UA,
                            follow_redirects=True,
                            timeout=discovery.TIMEOUT,
                        )
                    if resp.status_code == 200 and len(resp.content) > 1024:
                        avatar.write_bytes(resp.content)
                        _upscale_small_avatar(avatar)
                        try:
                            v = verify(photo, avatar, model)
                            note = f"verified={v['verified']}"
                        except ValueError:
                            # Tiny/odd avatars defeat face detection; fall back
                            # to whole-image embedding (large distance = reject).
                            v = verify(photo, avatar, model, enforce_detection=False)
                            note = f"verified(loose)={v['verified']}"
                        entry["distance"] = round(v["distance"], 4)
                        entry["verified"] = v["verified"]
                        entry["note"] = note
                    else:
                        entry["note"] = f"avatar fetch http {resp.status_code}"
                except Exception as exc:  # noqa: BLE001
                    entry["note"] = f"verify error: {type(exc).__name__}"
            results.append(entry)

    report = {
        "name": name,
        "photo": str(photo),
        "model": model,
        "sites": sites,
        "results": results,
    }
    if out:
        out.write_text(json.dumps(report, indent=2))
    render_table(report)
    return report
