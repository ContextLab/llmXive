"""
Unit test for the Something‑Something V2 streaming loader.

The test streams a few videos, writes each to a temporary file, and uses
OpenCV to read the first frame.  It asserts that:
  * at least five items are produced,
  * the downloaded bytes are non‑empty,
  * OpenCV can decode a frame (i.e. the video is not corrupted).
"""

import pathlib
import sys
import tempfile

import cv2
import pytest

# Ensure the project root is on the import path
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from src.data.something_loader import something_stream

@pytest.mark.timeout(600)
def test_something_loader_yields_five_with_frames():
    """
    Stream five videos, write each to a temp file, and verify that a
    non‑empty frame can be read with OpenCV.
    """
    iterator = something_stream(seed=42, max_examples=5)
    items = list(iterator)
    assert len(items) >= 5, "Expected at least 5 items from the loader"

    for idx, (video_bytes, label) in enumerate(items, start=1):
        # Basic sanity checks on the returned data.
        assert isinstance(video_bytes, (bytes, bytearray)), "Video data must be bytes"
        assert len(video_bytes) > 0, f"Video {idx} returned empty bytes"
        assert isinstance(label, str) and label, f"Label {idx} is invalid"

        # Write bytes to a temporary file and attempt to read the first frame.
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = pathlib.Path(tmp.name)

        cap = cv2.VideoCapture(str(tmp_path))
        ret, frame = cap.read()
        cap.release()
        tmp_path.unlink()  # clean up

        assert ret, f"OpenCV failed to read a frame from video {idx}"
        assert frame is not None and frame.size > 0, f"Empty frame from video {idx}"
