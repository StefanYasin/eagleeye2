"""EagleEye 2.0 CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from . import __version__
from .pipeline import run_scan
from .exif import extract_exif
from .reverse_image import reverse_image_search

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
    purpose: Optional[str] = typer.Option(
        None,
        "--purpose",
        help=(
            "Lawful use case: investigation, trust_safety, missing_person, "
            "research, background, other. Required unless --auto-accept."
        ),
    ),
    auto_accept: bool = typer.Option(
        False,
        "--auto-accept",
        help="Skip the ethics affirmation (scripts/tests only).",
    ),
) -> None:
    """Scan for a person's profiles from a photo."""
    from .ethics import EthicsGate, UseCase, USE_CASE_DESCRIPTIONS

    gate = EthicsGate(auto_accept=auto_accept)
    if not gate.affirm(UseCase(purpose) if purpose else None):
        typer.echo(EthicsGate.notice())
        typer.echo("Valid --purpose values: " + ", ".join(USE_CASE_DESCRIPTIONS.keys()))
        raise typer.Exit(code=1)
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
def exif(
    photo: Path = typer.Option(
        ..., "--photo", "-p", exists=True, file_okay=True, dir_okay=False,
        help="Photo to extract metadata from.",
    ),
) -> None:
    """Extract EXIF / GPS metadata from a photo (industry-standard first step)."""
    res = extract_exif(photo)
    typer.echo(f"EXIF — {res.path}")
    typer.echo(f"  Created:   {res.created or '—'}")
    typer.echo(f"  Camera:    {res.camera_make or '—'} {res.camera_model or ''}".rstrip())
    typer.echo(f"  Software:  {res.software or '—'}")
    if res.has_gps:
        typer.echo(f"  GPS:       {res.gps_lat}, {res.gps_lon} (alt {res.gps_alt}m)")
        typer.echo(f"  Maps:      {res.gmaps_url}")
    else:
        typer.echo("  GPS:       none (photo has no location data)")
    typer.echo(f"  Tags:      {len(res.fields)} total")


@app.command()
def revimg(
    photo: Path = typer.Option(
        ..., "--photo", "-p", exists=True, file_okay=True, dir_okay=False,
        help="Photo to reverse-image-search.",
    ),
    engines: str = typer.Option(
        "yandex,bing", "--engines", "-e",
        help="Comma-separated: yandex, bing, tineye",
    ),
    open_browser: bool = typer.Option(
        True, "--open/--no-open", "-o",
        help="Open search URLs in browser (reliable free method).",
    ),
) -> None:
    """Reverse image search — find where a photo has been posted."""
    from rich.console import Console
    from rich.table import Table

    engine_list = [e.strip() for e in engines.split(",") if e.strip()]
    typer.echo(f"🔍 Reverse image search ({', '.join(engine_list)}) — {photo}")

    # The reliable free path: open each engine's search page in the browser
    if open_browser:
        from .reverse_image import reverse_image_browser_urls
        urls = reverse_image_browser_urls(str(photo))
        console = Console()
        table = Table(title="Open in browser (one click per engine)")
        table.add_column("Engine")
        table.add_column("URL")
        for engine in engine_list:
            if engine in urls:
                table.add_row(engine, urls[engine])
                import webbrowser
                webbrowser.open(urls[engine])
        console.print(table)
        typer.echo("✅ Opened in your browser — results will load there.")
        return

    results = reverse_image_search(str(photo), tuple(engine_list))
    console = Console()
    for res in results:
        table = Table(title=f"{res.engine} — {len(res.hits)} hits")
        table.add_column("URL", style="cyan")
        table.add_column("Source")
        if res.error and not res.hits:
            typer.echo(f"⚠️ {res.engine}: {res.error}")
        for hit in res.hits[:10]:
            table.add_row(hit.url[:70], hit.source or "—")
        if res.hits:
            console.print(table)
        if res.search_url:
            typer.echo(f"  Open: {res.search_url}")


@app.command()
def version() -> None:
    """Show version."""
    typer.echo(f"eagleeye2 {__version__}")


if __name__ == "__main__":
    app()
