"""EXIF / GPS metadata extraction — the industry-standard image forensics step.

From the OSINT community methodology (r/OSINT wiki): "the first step is to
look at exif data... it often contains interesting information on the
creation date, the camera used, sometimes GPS data." We do what ExifTool
does, natively, so the toolchain stays self-contained.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ExifResult:
    """Extracted metadata for one photo."""
    path: str = ""
    created: Optional[str] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    software: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None
    gps_alt: Optional[float] = None
    gps_dms: Optional[str] = None
    has_gps: bool = False
    fields: dict = field(default_factory=dict)

    @property
    def gmaps_url(self) -> Optional[str]:
        """Google Maps link when GPS is present — one-click location view."""
        if self.gps_lat is None or self.gps_lon is None:
            return None
        return f"https://www.google.com/maps?q={self.gps_lat:.6f},{self.gps_lon:.6f}"


def _dms_to_decimal(dms, ref) -> Optional[float]:
    """Convert GPS DMS tuple + hemisphere ref to decimal degrees."""
    try:
        d, m, s = float(dms[0]), float(dms[1]), float(dms[2])
        dec = d + m / 60.0 + s / 3600.0
        if ref in ("S", "W"):
            dec = -dec
        return round(dec, 6)
    except (TypeError, ValueError, IndexError):
        return None


def extract_exif(path) -> ExifResult:
    """Extract EXIF + GPS from an image. Pure Pillow, no external tools."""
    from PIL import Image, ExifTags

    res = ExifResult(path=str(path))
    try:
        img = Image.open(path)
        exif = img._getexif()
    except Exception:
        return res
    if not exif:
        return res

    # Human-readable tag names
    tags = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
    res.fields = {k: str(v) for k, v in tags.items() if k not in ("MakerNote",)}

    res.created = tags.get("DateTimeOriginal") or tags.get("DateTime")
    res.camera_make = tags.get("Make")
    res.camera_model = tags.get("Model")
    res.software = tags.get("Software")

    # GPS
    gps = tags.get("GPSInfo")
    if gps:
        try:
            gps_tags = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps.items()}
            lat = _dms_to_decimal(gps_tags.get("GPSLatitude"), gps_tags.get("GPSLatitudeRef"))
            lon = _dms_to_decimal(gps_tags.get("GPSLongitude"), gps_tags.get("GPSLongitudeRef"))
            alt = None
            try:
                alt = float(gps_tags.get("GPSAltitude", 0) or 0)
            except (TypeError, ValueError):
                pass
            if lat is not None and lon is not None:
                res.gps_lat, res.gps_lon, res.gps_alt = lat, lon, alt
                res.has_gps = True
                d = gps_tags.get("GPSLatitude", [0, 0, 0])
                res.gps_dms = f"{d[0]}°{d[1]}'{d[2]}\" {gps_tags.get('GPSLatitudeRef', '')}"
        except Exception:
            pass
    return res
