"""
Verify that the Something‑Something loader yields at least five
decodable video frames using OpenCV.
"""

import pathlib
import sys

import cv2
import pytest

# Ensure the project root is on the import path
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from src.data.something_loader import something_stream

@pytest.mark.timeout(300)
def test_something_loader_five_videos(tmp_path):
    """
    Stream five videos and assert that each can be opened by OpenCV.
    """
    iterator = something_stream(seed=42, max_examples=5)
    count = 0
    for video_bytes, label in iterator:
        # Write to a temporary file and attempt to open with OpenCV
        video_path = tmp_path / f"video_{count}.mp4"
        video_path.write_bytes(video_bytes)

        cap = cv2.VideoCapture(str(video_path))
        opened = cap.isOpened()
        cap.release()
        assert opened, f"OpenCV failed to open video {video_path}"
        count += 1

    assert count == 5, f"Expected 5 videos, got {count}"