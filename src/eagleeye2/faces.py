"""Face detection / embedding / verification via deepface (loaded lazily)."""

from __future__ import annotations

from pathlib import Path

_DeepFace = None


def _df():
    global _DeepFace
    if _DeepFace is None:
        from deepface import DeepFace

        _DeepFace = DeepFace
    return _DeepFace


def embed(photo: str | Path, model: str = "Facenet") -> dict:
    """Embed the face in ``photo``.

    Returns {"embedding": [...], "facial_area": {...}}.
    Raises ValueError when no face is detected.
    """
    reps = _df().represent(
        img_path=str(photo),
        model_name=model,
        enforce_detection=True,
        detector_backend="opencv",
    )
    if not reps:
        raise ValueError(f"No face detected in {photo}")
    return {"embedding": reps[0]["embedding"], "facial_area": reps[0].get("facial_area")}


def verify(
    img1: str | Path,
    img2: str | Path,
    model: str = "Facenet",
    enforce_detection: bool = True,
) -> dict:
    """Verify whether two images show the same person.

    Returns {"verified": bool, "distance": float, "threshold": float}.
    """
    r = _df().verify(
        img1_path=str(img1),
        img2_path=str(img2),
        model_name=model,
        enforce_detection=enforce_detection,
        detector_backend="opencv",
    )
    return {
        "verified": bool(r["verified"]),
        "distance": float(r["distance"]),
        "threshold": float(r["threshold"]),
    }
