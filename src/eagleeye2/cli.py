"""EagleEye 2.0 CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from . import __version__
from .pipeline import run_scan

app = typer.Typer(help="EagleEye 2.0 — find social profiles from a face photo.")


@app.command()
def scan(
    photo: Path = typer.Option(
        ...,
        "--photo",
        "-p",
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Photo of the person (must contain a face).",
    ),
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Person's name for handle generation."
    ),
    sites: str = typer.Option(
        "instagram,threads",
        "--sites",
        "-s",
        help="Comma-separated sites: instagram, threads, x, tiktok",
    ),
    model: str = typer.Option(
        "Facenet",
        "--model",
        "-m",
        help="deepface model: Facenet, VGG-Face, ArcFace, SFace, OpenFace, DeepID",
    ),
    out: Optional[Path] = typer.Option(
        "scan_report.json", "--out", "-o", help="JSON report path."
    ),
    urls: Optional[Path] = typer.Option(
        None,
        "--urls",
        "-u",
        exists=True,
        help="File of explicit profile URLs to check instead of name-based search.",
    ),
) -> None:
    """Scan for a person's profiles from a photo."""
    if not name and not urls:
        raise typer.BadParameter("Provide --name and/or --urls")
    site_list = [s.strip() for s in sites.split(",") if s.strip()]
    run_scan(
        photo=photo,
        name=name or "",
        sites=site_list,
        model=model,
        out=out,
        urls_file=urls,
    )
    typer.echo(f"Report written to {out}")


@app.command()
def version() -> None:
    """Show version."""
    typer.echo(f"eagleeye2 {__version__}")


if __name__ == "__main__":
    app()
