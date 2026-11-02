"""EXIF / GPS extraction tests. No network, no face models, Pillow only."""

from __future__ import annotations

import pytest

pytest.importorskip("PIL")

from PIL import Image  # noqa: E402

from eagleeye2.exif import (  # noqa: E402
    _altitude_m,
    _dms_text,
    _dms_to_decimal,
    extract_exif,
)

GPS_ABOVE = {
    1: "S", 2: (33.0, 51.0, 54.0),
    3: "E", 4: (151.0, 12.0, 36.0),
    5: b"\x00", 6: 55.0,
}
GPS_BELOW = {
    1: "S", 2: (33.0, 51.0, 54.0),
    3: "E", 4: (151.0, 12.0, 36.0),
    5: b"\x01", 6: 55.0,
}
GPS_NO_ALT = {
    1: "N", 2: (43.0, 15.0, 45.0),
    3: "W", 4: (79.0, 50.0, 20.0),
}


def make_photo(tmp_path, gps=None, fmt="JPEG", ext="jpg"):
    path = tmp_path / f"photo.{ext}"
    exif = Image.Exif()
    exif[0x010F] = "TestMake"
    exif[0x0110] = "TestModel"
    if gps is not None:
        exif[0x8825] = gps
    Image.new("RGB", (8, 8), "gray").save(path, format=fmt, exif=exif)
    return path


def test_altitude_missing_is_none():
    assert _altitude_m({}) is None
    assert _altitude_m({"GPSAltitudeRef": b"\x00"}) is None


def test_altitude_above_sea_level_positive():
    assert _altitude_m({"GPSAltitude": 55.0, "GPSAltitudeRef": b"\x00"}) == 55.0
    assert _altitude_m({"GPSAltitude": 55.0}) == 55.0


def test_altitude_below_sea_level_negative():
    assert _altitude_m({"GPSAltitude": 55.0, "GPSAltitudeRef": b"\x01"}) == -55.0
    assert _altitude_m({"GPSAltitude": 12, "GPSAltitudeRef": 1}) == -12.0


def test_altitude_bad_value_is_none():
    assert _altitude_m({"GPSAltitude": "n/a"}) is None
    assert _altitude_m({"GPSAltitude": 10.0, "GPSAltitudeRef": "junk"}) == 10.0


def test_dms_to_decimal_hemispheres():
    assert _dms_to_decimal((33, 51, 54), "S") == -33.865
    assert _dms_to_decimal((33, 51, 54), "N") == 33.865
    assert _dms_to_decimal((151, 12, 36), "W") == -151.21


def test_dms_to_decimal_bad_input():
    assert _dms_to_decimal(None, "N") is None
    assert _dms_to_decimal((1, 2), "N") is None


def test_dms_text():
    assert _dms_text((33, 51, 54), "S") == "33\u00b051'54.00\" S"
    assert _dms_text(None, "N") is None


@pytest.mark.parametrize("fmt,ext", [("JPEG", "jpg"), ("PNG", "png"), ("WEBP", "webp")])
def test_extract_exif_below_sea_level(tmp_path, fmt, ext):
    res = extract_exif(make_photo(tmp_path, GPS_BELOW, fmt, ext))
    assert res.has_gps is True
    assert res.gps_lat == -33.865
    assert res.gps_lon == 151.21
    assert res.gps_alt == -55.0
    assert res.gps_dms == "33\u00b051'54.00\" S"


def test_extract_exif_above_sea_level(tmp_path):
    res = extract_exif(make_photo(tmp_path, GPS_ABOVE))
    assert res.gps_alt == 55.0
    assert res.camera_make == "TestMake"
    assert res.camera_model == "TestModel"


def test_extract_exif_without_altitude_tag(tmp_path):
    res = extract_exif(make_photo(tmp_path, GPS_NO_ALT))
    assert res.has_gps is True
    assert res.gps_lat == 43.2625
    assert res.gps_alt is None


def test_extract_exif_without_gps(tmp_path):
    res = extract_exif(make_photo(tmp_path))
    assert res.has_gps is False
    assert res.gps_lat is None
    assert res.gmaps_url is None
    assert res.camera_make == "TestMake"


def test_extract_exif_missing_file(tmp_path):
    res = extract_exif(tmp_path / "nope.jpg")
    assert res.fields == {}
    assert res.has_gps is False
