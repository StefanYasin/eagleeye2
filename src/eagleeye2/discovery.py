"""Handle generation + profile URL probing + og:image extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import httpx

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"
    )
}
TIMEOUT = 12.0

SITE_RULES = {
    "instagram": "https://www.instagram.com/{h}/",
    "threads": "https://www.threads.net/@{h}",
    "x": "https://x.com/{h}",
    "tiktok": "https://www.tiktok.com/@{h}",
}


@dataclass
class Candidate:
    site: str
    handle: str
    url: str
    og_image: Optional[str] = None
    og_image_src: Optional[str] = None  # unmodified og:image (fallback for 403s)
    status: Optional[int] = None
    note: str = ""


def candidate_handles(name: str) -> list[str]:
    """Generate plausible usernames from a person's name."""
    parts = [p for p in re.split(r"[^A-Za-z0-9]+", name.strip().lower()) if p]
    if not parts:
        return []
    first, last = parts[0], parts[-1] if len(parts) > 1 else ""
    handles = set()
    if last:
        handles.update(
            [first + last, f"{first}.{last}", f"{first}_{last}", f"{first}{last}1"]
        )
        if len(first) >= 3:
            handles.add(f"{first[:3]}{last}")
    else:
        handles.add(first)
    return sorted(h for h in handles if 3 <= len(h) <= 30)


def _og_image(html: str) -> Optional[str]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for prop in ("og:image", "og:image:url"):
        meta = soup.find("meta", attrs={"property": prop}) or soup.find(
            "meta", attrs={"name": prop}
        )
        if meta and meta.get("content"):
            return meta["content"].strip()
    return None


def _upgrade_avatar_url(url: str) -> str:
    """Ask CDNs for a larger avatar when the og:image is a tiny thumbnail."""
    if "cdninstagram.com" in url:
        url = re.sub(r"s\d+x\d+", "s640x640", url)
    return url


def probe(url: str) -> Candidate:
    """Fetch a profile URL and try to extract its og:image avatar."""
    c = Candidate(site="", handle="", url=url)
    try:
        r = httpx.get(url, headers=UA, follow_redirects=True, timeout=TIMEOUT)
        c.status = r.status_code
        if r.status_code == 200 and r.headers.get("content-type", "").startswith(
            "text/html"
        ):
            src = _og_image(r.text)
            c.og_image_src = src
            c.og_image = _upgrade_avatar_url(src or "") or None
            c.note = "ok" if c.og_image else "no og:image"
        elif r.status_code == 404:
            c.note = "not found"
        else:
            c.note = f"http {r.status_code}"
    except httpx.TimeoutException:
        c.note = "timeout"
    except Exception as exc:  # noqa: BLE001
        c.note = f"error: {type(exc).__name__}"
    return c


def build_candidates(name: str, sites: list[str]) -> list[Candidate]:
    out: list[Candidate] = []
    for site in sites:
        if site not in SITE_RULES:
            continue
        for handle in candidate_handles(name):
            out.append(
                Candidate(
                    site=site,
                    handle=handle,
                    url=SITE_RULES[site].format(h=handle),
                )
            )
    return out
