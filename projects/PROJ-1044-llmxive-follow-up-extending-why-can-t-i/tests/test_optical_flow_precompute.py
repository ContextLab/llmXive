"""
Integration test for ``src/data/optical_flow_precompute.py``.

The test creates a very small synthetic video (a few frames of a moving
square), runs the pre‑compute script, and checks that:

* At least one ``.npy`` file is created under ``data/flow/orig/``.
* The corresponding manifest entry exists and matches the file's SHA‑256.
* The saved NumPy array has the expected shape (num_pairs, H, W, 2).
"""

import shutil
from pathlib import Path

import cv2
import numpy as np
import pytest

from src.data.optical_flow_precompute import main as precompute_main

@pytest.fixture(scope="function")
def synthetic_video(tmp_path: Path) -> Path:
    """Create a tiny synthetic video (10×10, 3 frames) with a moving square."""
    video_dir = tmp_path / "data" / "videos" / "orig"
    video_dir.mkdir(parents=True, exist_ok=True)
    video_path = video_dir / "synthetic.mp4"

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(video_path), fourcc, 5.0, (10, 10))

    # Frame 0: black
    frame0 = np.zeros((10, 10, 3), dtype=np.uint8)
    out.write(frame0)

    # Frame 1: square at (2,2)
    frame1 = frame0.copy()
    cv2.rectangle(frame1, (2, 2), (4, 4), (255, 255, 255), -1)
    out.write(frame1)

    # Frame 2: square moved to (4,4)
    frame2 = frame0.copy()
    cv2.rectangle(frame2, (4, 4), (6, 6), (255, 255, 255), -1)
    out.write(frame2)

    out.release()
    return video_path

def test_precompute_creates_flow_and_manifest(tmp_path: Path, synthetic_video: Path):
    # Redirect the default data directories to the temporary location.
    # The script uses relative paths from the project root, so we monkey‑patch
    # Path.cwd() via the ``tmp_path`` fixture.
    original_cwd = Path.cwd()
    try:
        # Change cwd to the temporary directory that contains the synthetic video.
        # The script will look for ``data/videos/orig/*.mp4`` relative to this cwd.
        (tmp_path / "data" / "flow" / "orig").mkdir(parents=True, exist_ok=True)
        (tmp_path / "data" / "checksums").mkdir(parents=True, exist_ok=True)
        # Move the synthetic video into the expected location.
        target_dir = tmp_path / "data" / "videos" / "orig"
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(synthetic_video), target_dir / synthetic_video.name)

        # Run the pre‑compute script.
        ret = precompute_main()
        assert ret == 0, "pre‑compute script exited with non‑zero status"

        # Verify that a .npy file was created.
        flow_file = tmp_path / "data" / "flow" / "orig" / "synthetic.npy"
        assert flow_file.is_file(), ".npy flow file was not created"

        # Load the flow and check its shape (should be 2 pairs, H=10, W=10, 2 channels).
        flow_array = np.load(flow_file)
        assert flow_array.shape == (2, 10, 10, 2)

        # Verify manifest entry.
        manifest = tmp_path / "data" / "checksums" / "manifest.csv"
        assert manifest.is_file(), "manifest.csv was not created"
        content = manifest.read_text().strip()
        assert content, "manifest.csv is empty"
        rel_path, sha = content.split(",", 1)
        assert rel_path == flow_file.relative_to(original_cwd).as_posix()
        # Compute expected SHA‑256 and compare.
        import hashlib

        h = hashlib.sha256()
        with flow_file.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        expected_sha = h.hexdigest()
        assert sha == expected_sha, "SHA‑256 in manifest does not match the file"
    finally:
        # Restore original cwd to avoid side effects on other tests.
        Path.cwd().chdir(original_cwd)
