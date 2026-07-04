"""Simple smoke test for the download_data script."""

import subprocess
import sys
from pathlib import Path

def test_download_data_runs_successfully():
    """
    Executes the download_data script and checks that it exits with code 0
    and that the expected output file is created.
    """
    project_root = Path(__file__).resolve().parents[2]
    script_path = project_root / "code" / "download_data.py"
    raw_dir = project_root / "data" / "raw"
    output_file = raw_dir / "oqmd_li_rocksalt.csv"

    # Ensure a clean start
    if output_file.exists():
        output_file.unlink()

    result = subprocess.run(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # The script should complete without raising an exception
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # The output file must exist after successful execution
    assert output_file.is_file(), "Expected output CSV was not created."