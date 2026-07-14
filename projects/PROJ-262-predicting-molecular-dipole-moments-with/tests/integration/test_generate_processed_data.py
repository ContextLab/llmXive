"""Integration test for ``code/data/generate_processed_data.py``.

The test simply runs the script and asserts that the three expected parquet
files exist after execution.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

@pytest.mark.integration
def test_generate_processed_data_creates_files(tmp_path: pathlib.Path) -> None:
    # Change working directory to the repository root for relative paths
    repo_root = pathlib.Path(__file__).resolve().parents[3]
    # Ensure a clean ``data/processed`` directory for the test
    processed_dir = repo_root / "data" / "processed"
    if processed_dir.exists():
        for p in processed_dir.iterdir():
            p.unlink()
    else:
        processed_dir.mkdir(parents=True)

    # Run the script
    result = subprocess.run(
        [sys.executable, str(repo_root / "code" / "data" / "generate_processed_data.py")],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Expected output files
    expected_files = [
        processed_dir / "molecules_10k.parquet",
        processed_dir / "features_3d.parquet",
        processed_dir / "features_2d.parquet",
    ]
    for f in expected_files:
        assert f.is_file(), f"Missing expected file: {f}"
