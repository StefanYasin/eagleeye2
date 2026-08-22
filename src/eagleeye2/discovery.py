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
    # --- expanded coverage (roadmap #1: 4 -> 300+ sites) ---
    "youtube": "https://www.youtube.com/@{h}",
    "facebook": "https://www.facebook.com/{h}",
    "linkedin": "https://www.linkedin.com/in/{h}",
    "github": "https://github.com/{h}",
    "reddit": "https://www.reddit.com/user/{h}",
    "twitch": "https://www.twitch.tv/{h}",
    "pinterest": "https://www.pinterest.com/{h}/",
    "tumblr": "https://{h}.tumblr.com/",
    "vimeo": "https://vimeo.com/{h}",
    "flickr": "https://www.flickr.com/people/{h}/",
    "soundcloud": "https://soundcloud.com/{h}",
    "spotify": "https://open.spotify.com/user/{h}",
    "steam": "https://steamcommunity.com/id/{h}",
    "discord": "https://discord.com/users/{h}",
    "telegram": "https://t.me/{h}",
    "whatsapp": "https://wa.me/{h}",
    "snapchat": "https://www.snapchat.com/add/{h}",
    "onlyfans": "https://onlyfans.com/{h}",
    "patreon": "https://www.patreon.com/{h}",
    "etsy": "https://www.etsy.com/shop/{h}",
    "ebay": "https://www.ebay.com/usr/{h}",
    "keybase": "https://keybase.io/{h}",
    "hackernews": "https://news.ycombinator.com/user?id={h}",
    "producthunt": "https://www.producthunt.com/@{h}",
    "medium": "https://medium.com/@{h}",
    "devto": "https://dev.to/{h}",
    "gitlab": "https://gitlab.com/{h}",
    "bitbucket": "https://bitbucket.org/{h}",
    "pastebin": "https://pastebin.com/u/{h}",
    "replit": "https://replit.com/@{h}",
    "codepen": "https://codepen.io/{h}",
    "dribbble": "https://dribbble.com/{h}",
    "behance": "https://www.behance.net/{h}",
    "fiverr": "https://www.fiverr.com/{h}",
    "upwork": "https://www.upwork.com/freelancers/~{h}",
    "gravatar": "https://gravatar.com/{h}",
    "wordpress": "https://{h}.wordpress.com/",
    "blogger": "https://{h}.blogspot.com/",
    "vk": "https://vk.com/{h}",
    "ok": "https://ok.ru/{h}",
    "weibo": "https://weibo.com/u/{h}",
    "mixcloud": "https://www.mixcloud.com/{h}/",
    "bandcamp": "https://{h}.bandcamp.com/",
    "letterboxd": "https://letterboxd.com/{h}/",
    "trakt": "https://trakt.tv/users/{h}",
    "strava": "https://www.strava.com/athletes/{h}",
    "goodreads": "https://www.goodreads.com/{h}",
    "chess": "https://www.chess.com/member/{h}",
    "lichess": "https://lichess.org/@/{h}",
    "roblox": "https://www.roblox.com/user.aspx?username={h}",
    "mastodon.social": "https://mastodon.social/@{h}",
    "kaggle": "https://www.kaggle.com/{h}",
    "huggingface": "https://huggingface.co/{h}",
    "dockerhub": "https://hub.docker.com/u/{h}",
    "pypi": "https://pypi.org/user/{h}/",
    "npm": "https://www.npmjs.com/~{h}",
    "crates": "https://crates.io/users/{h}",
    "stackoverflow": "https://stackoverflow.com/users/{h}",
    "askubuntu": "https://askubuntu.com/users/{h}",
    "superuser": "https://superuser.com/users/{h}",
    "serverfault": "https://serverfault.com/users/{h}",
    "wikipedia": "https://en.wikipedia.org/wiki/User:{h}",
    "wikidata": "https://www.wikidata.org/wiki/User:{h}",
    "archive": "https://archive.org/@{h}",
    "internetarchive": "https://archive.org/details/@{h}",
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
