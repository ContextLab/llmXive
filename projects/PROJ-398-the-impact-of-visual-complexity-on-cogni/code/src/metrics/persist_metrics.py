"""
src/metrics/persist_metrics.py

This module provides a simple utility to persist the visual‑complexity metrics
computed by ``src.metrics.extract`` into a CSV file located at
``src.config.METRICS_CSV_PATH`` (which resolves to ``data/processed/metrics.csv``).

The implementation follows the existing project API surface:
  * ``list_image_files`` – returns an iterable of absolute image paths from the
    stimuli directory.
  * ``process_images`` – consumes the list of image paths and returns a list of
    dictionaries, each containing the calculated metrics for a single image.
  * ``ensure_directories_exist`` – creates any missing parent directories for a
    given path.
  * ``METRICS_CSV_PATH`` – the final destination CSV file.

The ``persist_metrics`` function is intentionally side‑effect‑only (writes a file)
and returns the list of metric dictionaries for possible downstream use.
The module also exposes a ``main`` entry‑point so the script can be executed
directly via ``python -m src.metrics.persist_metrics`` or ``python
code/src/metrics/persist_metrics.py`` as required by the task specification.
"""

import csv
import os
from pathlib import Path
from typing import List, Dict

# Project‑level imports – these names are guaranteed to exist according to the
# provided API surface.
from src.config import METRICS_CSV_PATH, ensure_directories_exist
from src.metrics.extract import list_image_files, process_images

__all__ = ["persist_metrics", "main"]


def persist_metrics() -> List[Dict]:
    """
    Compute visual‑complexity metrics for all images in the stimuli archive and
    persist them to ``METRICS_CSV_PATH``.

    Returns
    -------
    List[Dict]
        A list of dictionaries where each dictionary corresponds to one image and
        contains the computed metrics (e.g. ``image_id``, ``entropy``,
        ``color_variance``, ``object_count``).  The list is also written to disk
        as a CSV file whose header matches the dictionary keys.
    """
    # ----------------------------------------------------------------------
    # 1. Gather image file paths
    # ----------------------------------------------------------------------
    image_paths = list_image_files()
    if not image_paths:
        raise RuntimeError(
            "No image files were found by `list_image_files`. "
            "Ensure that the stimuli archive exists and contains images."
        )

    # ----------------------------------------------------------------------
    # 2. Compute metrics for each image
    # ----------------------------------------------------------------------
    metrics: List[Dict] = process_images(image_paths)

    if not metrics:
        raise RuntimeError(
            "Metric extraction returned an empty list. "
            "Check the implementation of `process_images`."
        )

    # ----------------------------------------------------------------------
    # 3. Ensure the destination directory exists
    # ----------------------------------------------------------------------
    csv_path = Path(METRICS_CSV_PATH)
    ensure_directories_exist(csv_path.parent)

    # ----------------------------------------------------------------------
    # 4. Write CSV
    # ----------------------------------------------------------------------
    # Use the keys from the first metric dict as the CSV header. All subsequent
    # dicts must contain the same keys; if they do not, the CSV writer will raise.
    fieldnames = list(metrics[0].keys())

    with csv_path.open(mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in metrics:
            writer.writerow(row)

    return metrics


def main() -> None:
    """
    Command‑line entry point.

    Running this script will compute the metrics and write them to disk.
    Any exception is allowed to propagate – the CI / test harness expects a
    failure if the real data cannot be processed.
    """
    persist_metrics()
    print(f"Metrics successfully persisted to {METRICS_CSV_PATH}")


if __name__ == "__main__":
    main()