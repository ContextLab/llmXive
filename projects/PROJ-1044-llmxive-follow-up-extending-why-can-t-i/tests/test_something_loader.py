"""
Unit test for :pyfunc:`src.data.something_loader.something_stream`.

The test streams the first five video URLs from the Something‑Something V2
dataset, downloads each video to a temporary file, and checks that OpenCV can
read at least one frame.  This validates that the loader returns real,
reachable video URLs and that the files contain visual data.
"""

import os
import tempfile

import cv2
import pytest
import requests

from src.data.something_loader import something_stream


@pytest.mark.timeout(300)
def test_load_five_videos():
    """
    Load five videos via the streaming loader and assert that each contains
    at least one readable frame.
    """
    # Use a fixed seed for reproducibility and limit the iterator to five items.
    iterator = something_stream(seed=123, max_examples=5)

    for video_url, label in iterator:
        # Basic sanity check on the returned values.
        assert isinstance(video_url, str) and video_url.startswith("http")
        assert isinstance(label, str) and len(label) > 0

        # Download the video to a temporary location.
        with requests.get(video_url, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep‑alive chunks
                        tmp_file.write(chunk)
                tmp_path = tmp_file.name

        # Use OpenCV to read the first frame.
        cap = cv2.VideoCapture(tmp_path)
        try:
            ret, frame = cap.read()
        finally:
            cap.release()
            os.remove(tmp_path)  # Clean up the temporary file.

        assert ret, f"OpenCV failed to read a frame from {video_url}"
        assert frame is not None and frame.size > 0, "Empty frame returned"
