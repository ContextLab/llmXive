"""
Simple integration test for ``code/data_curation/download_clips.py``.

The test runs the script's ``main`` function and verifies that:
  * The verification pool CSV is created.
  * The output directory ``data/raw/clips`` exists.
  * At least one clip file and a manifest JSON are produced.
"""

import json
from pathlib import Path

import pytest

# Import the module under test
from data_curation.download_clips import main, INPUT_POOL_PATH, OUTPUT_DIR, MANIFEST_PATH

def test_download_clips_end_to_end(tmp_path, monkeypatch):
    """
    Run the download pipeline in a temporary working directory.

    ``tmp_path`` is a fresh temporary directory provided by pytest.
    We monkey‑patch the project‑relative paths so that all artefacts are
    written inside the temporary folder, leaving the real repository
    untouched.
    """
    # Redirect the module‑level paths to the temporary directory
    monkeypatch.setattr("data_curation.download_clips.INPUT_POOL_PATH", tmp_path / "manually_verified_pool.csv")
    monkeypatch.setattr("data_curation.download_clips.OUTPUT_DIR", tmp_path / "clips")
    monkeypatch.setattr("data_curation.download_clips.MANIFEST_PATH", tmp_path / "clips" / "sampling_manifest.json")

    # Execute the pipeline
    success = main()
    assert success, "Pipeline reported failure"

    # Verify that the verification pool CSV exists and has the required columns
    pool_csv = tmp_path / "manually_verified_pool.csv"
    assert pool_csv.is_file(), "Verification pool CSV was not created"
    df = pd.read_csv(pool_csv)
    for col in ["video_id", "source_dataset", "label"]:
        assert col in df.columns, f"Missing column {col} in verification pool CSV"

    # Verify that at least one clip was downloaded
    clips_dir = tmp_path / "clips"
    assert clips_dir.is_dir(), "Clips output directory missing"
    mp4_files = list(clips_dir.glob("*.mp4"))
    assert len(mp4_files) >= 1, "No MP4 clips were written"

    # Verify manifest JSON
    manifest_file = tmp_path / "clips" / "sampling_manifest.json"
    assert manifest_file.is_file(), "Manifest JSON missing"
    with open(manifest_file) as f:
        manifest = json.load(f)
    assert manifest["successful"] == manifest["total_requested"], "Not all clips downloaded successfully"
    for entry in manifest["clips"]:
        assert entry["status"] in {"downloaded", "already_present"}, "Unexpected manifest status"

# The test module is executed by the platform's pytest runner automatically.