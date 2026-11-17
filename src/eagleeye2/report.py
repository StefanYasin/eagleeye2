"""Terminal rendering (rich) for scan results."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table


def render_table(report: dict) -> None:
    console = Console()
    console.print(
        f"[bold]EagleEye 2.0[/bold] — scan for "
        f"[cyan]{report['name'] or 'unknown'}[/cyan] (model: {report['model']})"
    )
    table = Table(title="Profile candidates")
    for col in ("Site", "Handle", "URL", "Status", "Distance", "Verified", "Note"):
        table.add_column(col, overflow="fold")
    for r in report["results"]:
        verified = (
            "[green]YES[/green]"
            if r["verified"]
            else ("[red]no[/red]" if r["verified"] is not None else "—")
        )
        dist = f"{r['distance']:.3f}" if r["distance"] is not None else "—"
        table.add_row(
            r["site"],
            r["handle"],
            r["url"],
            str(r["status"] or "—"),
            dist,
            verified,
            r["note"],
        )
    console.print(table)
    n_verified = sum(1 for r in report["results"] if r["verified"])
    console.print(
        f"[bold]{n_verified}[/bold] verified match(es) out of "
        f"{len(report['results'])} candidate(s)."
    )


# ---- Maigret-style status grammar + confidence summary + markdown export ----

def status_glyph(result: dict) -> str:
    """Maigret-style glyph for one result: [+] verified, [-] miss, [?] unknown."""
    if result["verified"] is True:
        return "[green][+][/green]"
    if result["verified"] is False:
        return "[dim][-][/dim]"
    return "[yellow][?][/yellow]"


def summarize(report: dict) -> dict:
    """Confidence summary (Maigret-style): what the scan actually concluded.

    Pure function over the report dict; unit-testable without deepface.
    """
    results = report.get("results", [])
    verified = [r for r in results if r["verified"]]
    candidates = [r for r in results if r["verified"] is False]
    unknown = [r for r in results if r["verified"] is None]

    distances = [r["distance"] for r in verified if r["distance"] is not None]
    best = min(distances) if distances else None

    if verified and best is not None and best < 0.4:
        confidence = "high"
    elif verified:
        confidence = "medium"
    else:
        confidence = "low"

    # Follow-up leads: the unverified candidates closest to a match.
    leads = sorted(candidates, key=lambda r: (r["distance"] is None, r["distance"] or 999))[:3]

    return {
        "platforms_checked": len({r["site"] for r in results}),
        "candidates": len(results),
        "verified": len(verified),
        "best_distance": best,
        "confidence": confidence,
        "leads": [
            {"site": l["site"], "handle": l["handle"], "url": l["url"],
             "distance": l["distance"]}
            for l in leads
        ],
        "unknown": len(unknown),
    }


DISCLAIMER = (
    "Automated face matching can produce false positives. Verify matches "
    "manually before acting on them. This tool must only be used with "
    "consent and for lawful purposes; see the ethics notice in the README."
)


def render_summary(report: dict) -> None:
    """Print the confidence summary block after a scan."""
    from rich.console import Console
    console = Console()
    s = summarize(report)
    label = {"high": "[bold green]HIGH[/bold green]",
             "medium": "[yellow]MEDIUM[/yellow]",
             "low": "[red]LOW[/red]"}[s["confidence"]]
    console.print(f"\n[bold]Summary[/bold]: {s['platforms_checked']} platforms, "
                  f"{s['candidates']} candidates, [bold]{s['verified']}[/bold] verified "
                  f"({label} confidence)")
    if s["best_distance"] is not None:
        console.print(f"  best face distance: {s['best_distance']:.3f}")
    if s["leads"]:
        console.print("  follow-up leads (unverified, closest first):")
        for lead in s["leads"]:
            dist = f"{lead['distance']:.3f}" if lead["distance"] is not None else "—"
            console.print(f"    [-] {lead['site']}: {lead['handle']} ({dist}) {lead['url']}")
    console.print(f"  [dim]{DISCLAIMER}[/dim]")


def export_markdown(report: dict) -> str:
    """LLM-tuned markdown report: one flat document, no tables to misparse.

    Suitable for feeding into an LLM context or archiving as evidence.
    """
    s = summarize(report)
    lines = [
        f"# EagleEye 2.0 scan report",
        "",
        f"- Target name: {report.get('name') or 'unknown'}",
        f"- Face model: {report.get('model') or 'unknown'}",
        f"- Platforms checked: {s['platforms_checked']}",
        f"- Candidates: {s['candidates']}",
        f"- Verified matches: {s['verified']}",
        f"- Confidence: {s['confidence']}",
    ]
    if s["best_distance"] is not None:
        lines.append(f"- Best face distance: {s['best_distance']:.3f}")
    lines += ["", "## Results", ""]
    for r in report.get("results", []):
        glyph = "+" if r["verified"] else ("-" if r["verified"] is False else "?")
        dist = f"{r['distance']:.3f}" if r["distance"] is not None else "n/a"
        status = str(r["status"] or "n/a")
        lines.append(f"[{glyph}] {r['site']} | handle: {r['handle']} | "
                     f"url: {r['url']} | status: {status} | distance: {dist} | "
                     f"verified: {r['verified']}")
    lines += ["", "## Disclaimer", "", DISCLAIMER, ""]
    return "\n".join(lines)
