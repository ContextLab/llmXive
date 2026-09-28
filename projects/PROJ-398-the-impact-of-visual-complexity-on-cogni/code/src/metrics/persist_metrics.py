"""
Persist computed visual complexity metrics to a CSV file.

This module is part of the **US1** pipeline. After extracting metrics from
background images (entropy, color variance, object count) the results must be
saved to ``data/processed/metrics.csv`` so that downstream analysis tasks can
consume them.

The implementation re‑uses the public API from ``src.metrics.extract``:
  * ``list_image_files`` – returns a list of image file paths.
  * ``process_images`` – given a list of image paths returns a list of dictionaries
    with the computed metrics for each image.

The CSV schema follows the ``BackgroundFrame`` contract used throughout the
project and must contain the columns:
    - ``image_id``        – filename without extension
    - ``entropy``         – Shannon entropy of the image
    - ``color_variance``  – variance across colour channels
    - ``object_count``    – number of detected objects (YOLOv8n)

The path to the output CSV is defined in ``src.config`` as ``METRICS_CSV_PATH``.
The function also guarantees that the parent directories exist before writing.
"""

import csv
from pathlib import Path
from typing import List, Dict

from src.config import METRICS_CSV_PATH, ensure_directories_exist
from src.metrics.extract import list_image_files, process_images


def _prepare_output_path() -> Path:
    """
    Ensure the directory hierarchy for the metrics CSV exists and return the full
    path to the CSV file.
    """
    ensure_directories_exist()
    # ``METRICS_CSV_PATH`` is an absolute ``Path`` defined in ``src.config``.
    return METRICS_CSV_PATH


def _row_from_metric_dict(metric: Dict) -> Dict:
    """
    Convert the raw metric dictionary returned by ``process_images`` into the
    CSV row format required by the ``BackgroundFrame`` schema.

    ``process_images`` returns a dict with at least the following keys:
        - ``image_path`` (Path)
        - ``entropy`` (float)
        - ``color_variance`` (float)
        - ``object_count`` (int)

    The CSV expects ``image_id`` (filename without suffix) and the three metric
    columns.
    """
    image_path: Path = metric["image_path"]
    return {
        "image_id": image_path.stem,
        "entropy": metric["entropy"],
        "color_variance": metric["color_variance"],
        "object_count": metric["object_count"],
    }


def persist_metrics(image_dir: Path) -> None:
    """
    Compute metrics for every image in ``image_dir`` and write them to the
    ``METRICS_CSV_PATH`` CSV file.

    Parameters
    ----------
    image_dir: Path
        Directory containing the raw stimulus images (e.g. ``data/stimuli/raw``).
    """
    # Resolve to an absolute path for safety.
    image_dir = image_dir.expanduser().resolve()
    if not image_dir.is_dir():
        raise NotADirectoryError(f"Image directory does not exist: {image_dir}")

    # 1. Discover image files.
    image_files: List[Path] = list_image_files(image_dir)

    # 2. Compute metrics using the existing extraction pipeline.
    # ``process_images`` returns a list of dictionaries, each containing the
    # raw metrics plus the original ``image_path``.
    raw_metrics: List[Dict] = process_images(image_files)

    # 3. Transform to the CSV schema.
    rows: List[Dict] = [_row_from_metric_dict(m) for m in raw_metrics]

    # 4. Write CSV.
    output_path = _prepare_output_path()
    with output_path.open(mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=["image_id", "entropy", "color_variance", "object_count"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """
    Entry point used by the pipeline and the test suite.

    The function reads the environment variable ``RAW_STIMULI_DIR`` if set;
    otherwise it falls back to the conventional location
    ``data/stimuli/raw`` relative to the project root.
    """
    import os

    default_dir = Path("data") / "stimuli" / "raw"
    raw_dir = Path(os.getenv("RAW_STIMULI_DIR", default_dir))
    persist_metrics(raw_dir)


if __name__ == "__main__":
    main()
