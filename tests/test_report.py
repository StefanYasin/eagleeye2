# tests/test_report.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from eagleeye2.report import status_glyph, summarize, export_markdown, DISCLAIMER


def _report():
    return {
        "name": "Jane Doe",
        "model": "Facenet",
        "results": [
            {"site": "instagram", "handle": "janedoe", "url": "https://instagram.com/janedoe",
             "status": 200, "distance": 0.32, "verified": True, "note": ""},
            {"site": "threads", "handle": "jane.doe", "url": "https://threads.net/jane.doe",
             "status": 200, "distance": 0.55, "verified": False, "note": ""},
            {"site": "x", "handle": "janedoe", "url": "https://x.com/janedoe",
             "status": 404, "distance": None, "verified": None, "note": "not found"},
        ],
    }


def test_status_glyphs():
    assert "[+]" in status_glyph({"verified": True})
    assert "[-]" in status_glyph({"verified": False})
    assert "[?]" in status_glyph({"verified": None})


def test_summary_counts():
    s = summarize(_report())
    assert s["platforms_checked"] == 3
    assert s["candidates"] == 3
    assert s["verified"] == 1
    assert s["best_distance"] == 0.32
    assert s["confidence"] == "high"


def test_summary_confidence_medium_without_close_match():
    rep = _report()
    rep["results"][0]["distance"] = 0.62
    assert summarize(rep)["confidence"] == "medium"


def test_summary_leads_exclude_unknown():
    s = summarize(_report())
    assert [l["handle"] for l in s["leads"]] == ["jane.doe"]   # unverified only, not None


def test_markdown_export_carries_disclaimer():
    md = export_markdown(_report())
    assert "[+] instagram" in md
    assert "[-] threads" in md
    assert "[?] x" in md
    assert DISCLAIMER in md
    assert "## Results" in md
