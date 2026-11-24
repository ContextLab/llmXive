"""
Verify that the Something-Something loader yields at least five
decodable videos and that each frame can be decoded by OpenCV.
"""

import pathlib
import sys

import cv2

# Ensure the project root is on the import path
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.data.something_loader import something_stream


def test_something_loader_five_videos(tmp_path):
    """
    Stream five videos and assert that each can be opened by OpenCV
    and that every frame can be decoded without error.
    """
    iterator = something_stream(seed=42, max_examples=5)
    count = 0
    for video_bytes, label in iterator:
        # Write to a temporary file
        video_path = tmp_path / f"video_{count}.mp4"
        video_path.write_bytes(video_bytes)

        cap = cv2.VideoCapture(str(video_path))
        assert cap.isOpened(), f"OpenCV failed to open video {video_path}"
        # Iterate over all frames
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                # End of video stream
                break
            assert frame is not None, f"Frame {frame_idx} is None in {video_path}"
            assert frame.ndim == 3, (
                f"Frame {frame_idx} does not have 3 dimensions in {video_path}"
            )
            assert frame.shape[2] == 3, (
                f"Frame {frame_idx} does not have 3 channels in {video_path}"
            )
            frame_idx += 1
        cap.release()
        # Ensure at least one frame was read
        assert frame_idx > 0, f"No frames read from video {video_path}"
        count += 1

    assert count == 5, f"Expected 5 videos, got {count}"


def test_something_loader_reproducible():
    """The same seed must produce the identical stream of bytes."""
    stream_a = list(something_stream(seed=7, max_examples=5))
    stream_b = list(something_stream(seed=7, max_examples=5))
    assert len(stream_a) == 5
    assert [b for b, _ in stream_a] == [b for b, _ in stream_b]