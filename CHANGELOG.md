# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Fixed

- `eagleeye2 exif` honours `GPSAltitudeRef`, so a photo taken below sea level
  reports a negative altitude instead of a positive one, and a photo with no
  altitude tag reports `None` instead of a fake 0 m.
- GPS is read through Pillow's public `Exif.get_ifd()` API instead of the
  private `Image._getexif()`, and the tag dump no longer includes the raw GPS
  IFD pointer or the MakerNote blob.
- Added `tests/test_exif.py` (14 tests, generated JPEG/PNG/WebP fixtures, no
  network or face models needed).

## [1.0.0] - 2026-08-29

### Added

- Initial release
