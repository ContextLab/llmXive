"""
Record per‑stimulus metadata.

This script iterates over all stimulus images stored in
``data/stimuli/raw`` and computes three visual‑complexity metrics:
* entropy
* colour variance
* object count (via YOLOv8n)

For each image a JSON side‑car file is written to
``data/stimuli/metadata/<image_id>.json`` containing the three
measurements.  The script can be executed directly:

    python code/src/metrics/record_metadata.py

It is also importable – the :func:`record_metadata` function can be
called from tests or other pipeline stages.
"""

import json
from pathlib import Path
from typing import Dict

from src.metrics.extract import (
    list_image_files,
    compute_entropy,
    compute_color_variance,
    count_objects_yolo,
)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _ensure_directory(path: Path) -> None:
    """Create *path* if it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)


def _write_metadata_file(metadata_path: Path, data: Dict) -> None:
    """Write *data* as pretty‑printed JSON to *metadata_path*."""
    with metadata_path.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, sort_keys=True)


# ----------------------------------------------------------------------
# Core implementation
# ----------------------------------------------------------------------
def record_metadata(
    raw_dir: Path = Path("data/stimuli/raw"),
    metadata_dir: Path = Path("data/stimuli/metadata"),
) -> None:
    """
    Compute and persist per‑stimulus metadata.

    Parameters
    ----------
    raw_dir: Path
        Directory containing the raw stimulus images.
    metadata_dir: Path
        Destination directory for the JSON side‑car files.
    """
    _ensure_directory(metadata_dir)

    # Resolve the list of image files (supports common image extensions)
    image_paths = list_image_files(raw_dir)

    if not image_paths:
        raise FileNotFoundError(f"No image files found in {raw_dir!s}")

    for img_path in image_paths:
        # Compute the three metrics using the existing extraction utilities
        entropy = compute_entropy(img_path)
        colour_variance = compute_color_variance(img_path)
        object_count = count_objects_yolo(img_path)

        metadata = {
            "entropy": entropy,
            "color_variance": colour_variance,
            "object_count": object_count,
        }

        metadata_file = metadata_dir / f"{img_path.stem}.json"
        _write_metadata_file(metadata_file, metadata)


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """CLI entry point – simply forwards to :func:`record_metadata`."""
    record_metadata()


if __name__ == "__main__":
    main()
