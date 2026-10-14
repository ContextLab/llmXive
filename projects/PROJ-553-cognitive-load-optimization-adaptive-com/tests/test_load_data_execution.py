"""
Integration test for the data loader script (T004).

This test simply runs the ``code/load_data.py`` module with the ``--download``
flag and checks that the expected output file ``data/processed/interactions.csv``
exists and contains at least the required canonical columns.

The test does **not** assert any particular number of rows – the public
datasets may or may not be reachable from the CI environment.  The important
thing is that the script exits cleanly (exit code 0) and writes the file.
"""

import subprocess
import sys
from pathlib import Path

def test_load_data_creates_interactions_file(tmp_path, capsys):
    """
    Run the loader and verify the interactions CSV exists with required columns.
    """
    # Ensure we are running from the project root
    project_root = Path(__file__).resolve().parents[2]

    script_path = project_root / "code" / "load_data.py"
    cmd = [sys.executable, str(script_path), "--download"]

    result = subprocess.run(
        cmd,
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # The script must exit with status 0
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Check that the expected warning (if any) was printed – we allow both
    # presence or absence because a public dataset might actually contain
    # a load label column.
    expected_warning = (
        "Public dataset lacks concurrent load labels. Manual Golden Set (T007g) is required."
    )
    # No assert on warning; just ensure script ran.

    # Verify the output file exists
    interactions_path = project_root / "data" / "processed" / "interactions.csv"
    assert interactions_path.is_file(), "interactions.csv was not created"

    # Verify required columns are present
    import pandas as pd

    df = pd.read_csv(interactions_path)
    required = [
        "interaction_id",
        "latency",
        "error",
        "hint",
        "pause",
        "response_time_ms",
        "timestamp",
    ]
    for col in required:
        assert col in df.columns, f"Missing required column {col} in interactions.csv"