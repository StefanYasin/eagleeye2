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
