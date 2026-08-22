"""Reverse image search — the original EagleEye killer feature.

Industry methodology (r/OSINT wiki): "use either Google Images, Bing Images,
Yandex Images or TinEye." Each engine finds *where a photo has been posted*,
which turns a face photo into a trail of accounts.

Free engines (no key): Yandex, Bing. TinEye has a free-tier API.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import httpx

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    )
}
TIMEOUT = 20.0


@dataclass
class ReverseImageHit:
    engine: str
    url: str
    title: str = ""
    source: str = ""
    thumbnail: str = ""


@dataclass
class ReverseImageResult:
    engine: str
    hits: list = field(default_factory=list)
    error: str = ""
    search_url: str = ""


def _upload_binary(client: httpx.Client, url: str, data: bytes, extra=None) -> str:
    """POST a binary file to a reverse-image endpoint; return response text."""
    r = client.post(
        url,
        data=extra or {},
        files={"file": ("image.jpg", data, "image/jpeg")},
        headers=UA,
        follow_redirects=True,
        timeout=TIMEOUT,
    )
    return r.text


# ---------------------------------------------------------------- Yandex
def yandex_search(photo_bytes: bytes) -> ReverseImageResult:
    """Yandex Images reverse search (free, no key)."""
    res = ReverseImageResult(engine="yandex")
    try:
        with httpx.Client() as client:
            # 1) upload to Yandex's temp upload endpoint
            upload = client.post(
                "https://yandex.com/images-apphost/image-details?cbird=111",
                files={"file": ("image.jpg", photo_bytes, "image/jpeg")},
                headers=UA,
                timeout=TIMEOUT,
            )
            if upload.status_code != 200:
                res.error = f"upload http {upload.status_code}"
                return res
            try:
                import json as _json
                url_key = _json.loads(upload.text).get("url", "")
            except Exception:
                # fallback: parse the url from the response body
                m = re.search(r'"url"\s*:\s*"([^"]+)"', upload.text)
                url_key = m.group(1) if m else ""
            if not url_key:
                res.error = "no upload url"
                return res
            res.search_url = f"https://yandex.com/images/search?rpt=imageview&url={url_key}"
            # 2) fetch the results page and extract image titles/links
            page = client.get(res.search_url, headers=UA, timeout=TIMEOUT)
            html = page.text
            # Yandex embeds results as JSON-ish CbirSimilarImages; extract URLs
            urls = re.findall(r'"url"\s*:\s*"(https?://[^"]+)"', html)
            seen = set()
            for u in urls:
                u = u.replace("\\u002F", "/").replace("\\/", "/")
                if u.startswith("http") and u not in seen:
                    seen.add(u)
                    res.hits.append(ReverseImageHit(engine="yandex", url=u))
                if len(res.hits) >= 12:
                    break
    except httpx.TimeoutException:
        res.error = "timeout"
    except Exception as e:  # noqa: BLE001
        res.error = f"error: {type(e).__name__}"
    return res


# ---------------------------------------------------------------- Bing
def bing_search(photo_bytes: bytes) -> ReverseImageResult:
    """Bing Visual Search (free, no key)."""
    res = ReverseImageResult(engine="bing")
    try:
        with httpx.Client() as client:
            html = _upload_binary(
                client,
                "https://www.bing.com/images/searchview/async?q=imgurl:&first=1&count=12",
                photo_bytes,
            )
            res.search_url = "https://www.bing.com/images/search?q=imgurl:"
            # Bing results carry murl (media url) attributes
            urls = re.findall(r'murl="(https?://[^"]+)"', html)
            seen = set()
            for u in urls:
                u = u.replace("&amp;", "&")
                if u not in seen:
                    seen.add(u)
                    res.hits.append(ReverseImageHit(engine="bing", url=u))
                if len(res.hits) >= 12:
                    break
    except httpx.TimeoutException:
        res.error = "timeout"
    except Exception as e:  # noqa: BLE001
        res.error = f"error: {type(e).__name__}"
    return res


# ---------------------------------------------------------------- TinEye (free tier)
def tineye_search(photo_bytes: bytes, api_key: str = "", public_id: str = "") -> ReverseImageResult:
    """TinEye reverse search. Free tier API needs key; without key, use public UI."""
    res = ReverseImageResult(engine="tineye")
    if api_key and public_id:
        try:
            import base64
            b64 = base64.b64encode(photo_bytes).decode()
            with httpx.Client() as client:
                r = client.post(
                    "https://api.tineye.com/rest/v3/search/",
                    data={"api_key": api_key, "public_id": public_id, "image": b64},
                    timeout=TIMEOUT,
                )
                if r.status_code == 200:
                    import json as _json
                    data = _json.loads(r.text)
                    for m in data.get("results", [])[:12]:
                        res.hits.append(ReverseImageHit(
                            engine="tineye", url=m.get("image_url", ""),
                            title=m.get("backlink", {}).get("crawl_date", ""),
                            source=m.get("backlink", {}).get("backlink", ""),
                        ))
                    res.search_url = "https://tineye.com/search"
                else:
                    res.error = f"http {r.status_code}"
        except Exception as e:  # noqa: BLE001
            res.error = f"error: {type(e).__name__}"
    else:
        res.error = "no api key (free engines only)"
    return res


def reverse_image_search(photo_path: str, engines=("yandex", "bing")) -> list[ReverseImageResult]:
    """Run reverse image search across engines; return per-engine results.

    Free tier: engines increasingly bot-block direct uploads (Yandex returns
    empty bodies to scripts, Bing rejects multipart). The reliable free path
    is the open-in-browser method (what practitioners actually use). Programmatic
    engines return search_urls when hits can't be scraped.
    """
    data = open(photo_path, "rb").read()
    out = []
    for engine in engines:
        if engine == "yandex":
            out.append(yandex_search(data))
        elif engine == "bing":
            out.append(bing_search(data))
        elif engine == "tineye":
            out.append(tineye_search(data))
    return out


def reverse_image_browser_urls(photo_path: str) -> dict[str, str]:
    """One-click search URLs for every engine (the reliable free method)."""
    import urllib.parse
    import os

    photo = os.path.abspath(photo_path)
    # data: URL lets engines see the photo without hosting it
    import base64, mimetypes
    mime = mimetypes.guess_type(photo)[0] or "image/jpeg"
    b64 = base64.b64encode(open(photo, "rb").read()).decode()
    data_url = f"data:{mime};base64,{b64}"

    return {
        "google": f"https://images.google.com/searchbyimage?image_url={urllib.parse.quote(data_url, safe='')}",
        "yandex": f"https://yandex.com/images/search?rpt=imageview&url={urllib.parse.quote(data_url, safe='')}",
        "bing": f"https://www.bing.com/images/search?q=imgurl:{urllib.parse.quote(data_url, safe='')}",
        "tineye": f"https://tineye.com/search?url={urllib.parse.quote(data_url, safe='')}",
    }
