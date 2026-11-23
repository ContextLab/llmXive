"""
Curate neutral stimuli for baseline tasks.

This script scans the raw stimulus directory (populated by
``src/experiment/fetch_and_archive.py`` / T014a), computes a visual
complexity metric (object count using the YOLOv8n detector), and copies
images with low complexity (default: fewer than 2 detected objects) to a
dedicated ``neutral`` directory.  The resulting images are used by the
baseline condition in later experiment stages.

The script can be executed directly:

    python -m src.experiment.curate_neutral

or imported and called programmatically via :func:`curate_neutral`.
"""

import argparse
import logging
import shutil
from pathlib import Path
from typing import List

# The object‑count function is part of the metric extraction pipeline.
# It loads a YOLOv8n model (CPU‑only) and returns the number of detected
# objects in the given image.
from src.metrics.extract import count_objects_yolo

__all__ = ["curate_neutral", "main"]

# Configure a basic logger; the test suite can capture this if needed.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s – %(message)s",
)
logger = logging.getLogger(__name__)

def _iter_image_files(directory: Path) -> List[Path]:
    """Return a list of image file paths in *directory*.

    Supported extensions are common raster formats. The function does
    not recurse into sub‑directories – the raw stimulus directory is
    expected to be flat.
    """
    extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    return [
        p
        for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() in extensions
    ]

def curate_neutral(
    raw_dir: Path = Path("data/stimuli/raw"),
    neutral_dir: Path = Path("data/stimuli/neutral"),
    max_object_count: int = 2,
) -> List[Path]:
    """
    Filter raw stimulus images and copy those with low visual complexity
    to the neutral stimuli directory.

    Parameters
    ----------
    raw_dir: Path
        Directory containing the originally fetched stimulus images.
    neutral_dir: Path
        Destination directory for images that satisfy the low‑complexity
        criterion. The directory is created if it does not exist.
    max_object_count: int
        Upper bound (exclusive) for the number of detected objects.
        Images with ``object_count < max_object_count`` are considered
        neutral.

    Returns
    -------
    List[Path]
        Paths of the images that were copied to *neutral_dir*.
    """
    raw_dir = Path(raw_dir)
    neutral_dir = Path(neutral_dir)

    if not raw_dir.is_dir():
        raise FileNotFoundError(f"Raw stimulus directory not found: {raw_dir}")

    neutral_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Scanning %s for candidate neutral stimuli", raw_dir)

    selected: List[Path] = []
    for img_path in _iter_image_files(raw_dir):
        try:
            object_count = count_objects_yolo(img_path)
            logger.debug(
                "Image %s – detected %d objects", img_path.name, object_count
            )
        except Exception as exc:  # pragma: no cover – defensive
            logger.warning(
                "Failed to process %s (will skip). Error: %s", img_path, exc
            )
            continue

        if object_count < max_object_count:
            dest = neutral_dir / img_path.name
            shutil.copy2(img_path, dest)
            selected.append(dest)
            logger.info(
                "Selected neutral stimulus: %s (objects=%d)", img_path.name, object_count
            )
        else:
            logger.debug(
                "Image %s excluded (objects=%d >= %d)",
                img_path.name,
                object_count,
                max_object_count,
            )

    logger.info(
        "Neutral curation complete – %d images copied to %s",
        len(selected),
        neutral_dir,
    )
    return selected

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Curate low‑complexity (neutral) stimuli from the raw archive."
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/stimuli/raw"),
        help="Directory containing raw stimulus images (default: data/stimuli/raw).",
    )
    parser.add_argument(
        "--neutral-dir",
        type=Path,
        default=Path("data/stimuli/neutral"),
        help="Directory to store selected neutral stimuli (default: data/stimuli/neutral).",
    )
    parser.add_argument(
        "--max-object-count",
        type=int,
        default=2,
        help="Maximum number of detected objects for an image to be considered neutral (default: 2).",
    )
    return parser.parse_args()

def main() -> None:
    """Entry‑point for the ``python -m src.experiment.curate_neutral`` command."""
    args = _parse_args()
    curate_neutral(
        raw_dir=args.raw_dir,
        neutral_dir=args.neutral_dir,
        max_object_count=args.max_object_count,
    )

if __name__ == "__main__":
    main()
