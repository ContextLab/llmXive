"""
Unit test for ``code/data/generate_processed_data.py``.

The test runs the script in a temporary directory and checks that the three
expected Parquet files are created and contain a non‑empty DataFrame.
"""
import subprocess
import sys
from pathlib import Path

import pytest

@pytest.mark.integration
def test_generate_processed_data_creates_outputs(tmp_path: Path):
    # Run the script with a temporary processed directory.
    script = Path("code/data/generate_processed_data.py")
    processed_dir = tmp_path / "processed"
    cmd = [
        sys.executable,
        str(script),
        "--raw-dir",
        "data/raw",          # use the project's raw directory (download performed if needed)
        "--processed-dir",
        str(processed_dir),
        "--subset-size",
        "1000",              # smaller size speeds up CI while still exercising the logic
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Expected artefacts
    molecules = processed_dir / "molecules_10k.parquet"
    feats_3d = processed_dir / "features_3d.parquet"
    feats_2d = processed_dir / "features_2d.parquet"

    for path in (molecules, feats_3d, feats_2d):
        assert path.is_file(), f"Missing expected file: {path}"
        # Verify that the parquet file can be read and is non‑empty.
        import pandas as pd

        df = pd.read_parquet(path)
        assert not df.empty, f"Parquet file {path} contains no rows"