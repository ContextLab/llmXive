"""
Unit test for the optical‑flow pre‑compute script (T004).

The test creates a tiny synthetic video (a few frames of a moving
white square on a black background), runs the pre‑compute script on it
and asserts that:

* a ``.npy`` file is created in ``data/flow/orig/``,
* the manifest contains an entry for that file,
* the stored flow tensor has the expected shape (num_frames‑1, H, W, 2).
"""

import shutil
from pathlib import Path

import numpy as np
import cv2
import pytest

from llmxive_toolkit import paths
from src.data.optical_flow_precompute import main as run_precompute

@pytest.fixture
def synthetic_video(tmp_path: Path) -> Path:
    """Create a 3‑frame synthetic video (64×64) with a moving square."""
    video_path = tmp_path / "test_video.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(video_path), fourcc, 5.0, (64, 64))
    for i in range(3):
        frame = np.zeros((64, 64, 3), dtype=np.uint8)
        cv2.rectangle(frame, (5 + i * 5, 20), (25 + i * 5, 40), (255, 255, 255), -1)
        out.write(frame)
    out.release()
    return video_path

def test_precompute_flow_creates_files(synthetic_video: Path, monkeypatch: pytest.MonkeyPatch):
    # Redirect the script to use a temporary videos directory
    temp_videos_dir = synthetic_video.parent
    temp_flow_dir = paths.data("flow", "orig_test")
    temp_manifest = paths.data("checksums", "manifest_test.csv")

    # Ensure a clean state
    if temp_flow_dir.exists():
        shutil.rmtree(temp_flow_dir)
    if temp_manifest.exists():
        temp_manifest.unlink()

    # Monkey‑patch the default arguments
    monkeypatch.setattr(
        "src.data.optical_flow_precompute.paths",
        paths,
    )
    # Run the pre‑compute script
    exit_code = run_precompute(
        [
            "--videos-dir",
            str(temp_videos_dir),
            "--flow-dir",
            str(temp_flow_dir),
            "--manifest",
            str(temp_manifest),
        ]
    )
    assert exit_code == 0

    # Check that a .npy file was created
    npy_files = list(temp_flow_dir.glob("*.npy"))
    assert len(npy_files) == 1
    flow_tensor = np.load(npy_files[0])
    # 3 frames → 2 flow fields
    assert flow_tensor.shape[0] == 2
    assert flow_tensor.shape[-1] == 2  # (dx, dy)

    # Verify manifest entry
    manifest_content = temp_manifest.read_text(encoding="utf-8").strip().splitlines()
    assert len(manifest_content) == 1
    rel_path, _ = manifest_content[0].split(",", 1)
    expected_rel = npy_files[0].relative_to(paths.root).as_posix()
    assert rel_path == expected_rel