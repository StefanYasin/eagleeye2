"""EXIF / GPS metadata extraction - the industry-standard image forensics step.

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
        """Google Maps link when GPS is present - one-click location view."""
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


def _altitude_m(gps_tags: dict) -> Optional[float]:
    """Altitude in metres, signed by GPSAltitudeRef (1 = below sea level).

    ExifTool prints 55.0 for a ref of 0 and -55.0 for a ref of 1. Cameras do
    record below-sea-level shots (Death Valley, Dead Sea, mines, dives), so
    ignoring the ref silently flips the sign. A photo with no GPSAltitude tag
    stays None instead of collapsing to 0 m, which used to read as sea level.
    """
    raw = gps_tags.get("GPSAltitude")
    if raw is None:
        return None
    try:
        alt = float(raw)
    except (TypeError, ValueError):
        return None
    ref = gps_tags.get("GPSAltitudeRef", 0)
    if isinstance(ref, (bytes, bytearray)):
        ref = ref[0] if ref else 0
    try:
        below = int(ref) == 1
    except (TypeError, ValueError):
        below = False
    return round(-alt if below else alt, 1)


def _dms_text(dms, ref) -> Optional[str]:
    """Human-readable DMS pair, e.g. 43d15'45.00" N."""
    try:
        d, m, s = (float(x) for x in dms[:3])
    except (TypeError, ValueError, IndexError):
        return None
    if isinstance(ref, (bytes, bytearray)):
        ref = ref.decode("ascii", "ignore")
    return f"{d:.0f}\u00b0{m:.0f}'{s:.2f}\" {(ref or '').strip()}".strip()


def _gps_ifd(exif, tags: dict) -> dict:
    """GPS sub-IFD as an int-keyed dict, across Pillow versions.

    Pillow >= 6 exposes it through Exif.get_ifd(); the old private
    Image._getexif() path returned it inline under the "GPSInfo" tag.
    """
    try:
        gps = exif.get_ifd(0x8825)  # ExifTags.IFD.GPSInfo
        if gps:
            return dict(gps)
    except Exception:  # noqa: BLE001 - malformed IFD, fall back below
        pass
    legacy = tags.get("GPSInfo")
    return dict(legacy) if isinstance(legacy, dict) else {}


def extract_exif(path) -> ExifResult:
    """Extract EXIF + GPS from an image. Pure Pillow, no external tools."""
    from PIL import Image, ExifTags

    res = ExifResult(path=str(path))
    try:
        img = Image.open(path)
    except Exception:
        return res

    try:
        try:
            exif = img.getexif()  # public API, Pillow >= 6
        except AttributeError:
            exif = img._getexif() or {}  # very old Pillow
        if not exif:
            return res

        # Human-readable tag names; skip blobs and the GPS IFD pointer.
        tags = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
        res.fields = {
            k: str(v)
            for k, v in tags.items()
            if k not in ("MakerNote", "GPSInfo")
        }

        res.created = tags.get("DateTimeOriginal") or tags.get("DateTime")
        res.camera_make = tags.get("Make")
        res.camera_model = tags.get("Model")
        res.software = tags.get("Software")

        gps = _gps_ifd(exif, tags)
        if gps:
            gps_tags = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps.items()}
            lat = _dms_to_decimal(
                gps_tags.get("GPSLatitude"), gps_tags.get("GPSLatitudeRef")
            )
            lon = _dms_to_decimal(
                gps_tags.get("GPSLongitude"), gps_tags.get("GPSLongitudeRef")
            )
            if lat is not None and lon is not None:
                res.gps_lat = lat
                res.gps_lon = lon
                res.gps_alt = _altitude_m(gps_tags)
                res.has_gps = True
                res.gps_dms = _dms_text(
                    gps_tags.get("GPSLatitude"), gps_tags.get("GPSLatitudeRef")
                )
        return res
    finally:
        try:
            img.close()
        except Exception:
            pass
