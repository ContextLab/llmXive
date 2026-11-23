"""
tests/test_metrics_no_objects.py

This test ensures that the ``count_objects_yolo`` function correctly
returns ``0`` for an image that contains no detectable objects, satisfying
task **T020**.
"""

import pathlib
import tempfile

import cv2
import numpy as np
import pytest

from src.metrics.extract import count_objects_yolo, process_images

@pytest.fixture
def blank_image_path() -> pathlib.Path:
    """Create a plain white image (no objects) on disk and return its path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = pathlib.Path(tmpdir) / "blank.png"
        # 640x360 white image – simple enough that YOLO should detect nothing.
        blank = np.full((360, 640, 3), 255, dtype=np.uint8)
        cv2.imwrite(str(img_path), blank)
        yield img_path

def test_count_objects_yolo_returns_zero_on_blank_image(blank_image_path: pathlib.Path):
    """The core requirement of T020."""
    assert count_objects_yolo(blank_image_path) == 0

def test_process_images_writes_zero_object_count(tmp_path: pathlib.Path, blank_image_path: pathlib.Path):
    """
    Run the full pipeline on a directory containing only the blank image and
    verify that the CSV records ``object_count = 0`` for that entry.
    """
    # Prepare input directory with the blank image
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / blank_image_path.name).write_bytes(blank_image_path.read_bytes())

    output_csv = tmp_path / "metrics.csv"
    process_images(input_dir, output_csv)

    # Read back the CSV and check the object count column
    import csv

    with output_csv.open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["image_id"] == blank_image_path.name
    assert rows[0]["object_count"] == "0"