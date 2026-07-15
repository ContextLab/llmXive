"""
Integration test for ``src.experiment.curate_clips``.

The test creates a temporary directory with two tiny video files generated
via OpenCV (one meeting the criteria, one exceeding the duration limit) and
verifies that only the valid clip appears in the resulting CSV.
"""

import csv
import os
from pathlib import Path

import cv2
import numpy as np
import pytest

from src.experiment.curate_clips import curate_clips

@pytest.fixture
def temporary_video_dir(tmp_path: Path):
    """
    Create a temporary directory containing two synthetic video clips:
    * ``short_valid.mp4`` – 640×360, 5 s duration (meets criteria)
    * ``long_invalid.mp4`` – 640×360, 12 s duration (fails duration)
    """
    fps = 30
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    # Helper to write a solid‑color video
    def write_video(path: Path, frames: int):
        out = cv2.VideoWriter(str(path), fourcc, fps, (640, 360))
        frame = np.full((360, 640, 3), 127, dtype=np.uint8)  # gray frame
        for _ in range(frames):
            out.write(frame)
        out.release()

    short_path = tmp_path / "short_valid.mp4"
    long_path = tmp_path / "long_invalid.mp4"

    write_video(short_path, frames=5 * fps)   # 5 s
    write_video(long_path, frames=12 * fps)  # 12 s

    return tmp_path

def test_curate_clips_filters_correctly(temporary_video_dir, tmp_path):
    output_csv = tmp_path / "curated.csv"
    curated = curate_clips(temporary_video_dir, output_csv)

    # Only the short video should be kept
    assert len(curated) == 1
    assert curated[0].name == "short_valid.mp4"

    # Verify CSV contents
    with output_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["clip_path"].endswith("short_valid.mp4")
    assert int(rows[0]["width"]) >= 640
    assert int(rows[0]["height"]) >= 360
    assert float(rows[0]["duration_sec"]) <= 10.0