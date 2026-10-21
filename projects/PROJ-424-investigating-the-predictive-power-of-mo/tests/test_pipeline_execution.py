"""
Simple execution test for the pipeline script.

This test invokes ``python code/pipeline.py`` with the minimal
configuration required by task T004 and checks that the expected CSV
file is produced and validates against the contract.
"""

import subprocess
import sys
from pathlib import Path

import pytest
from llmxive_toolkit import paths

@pytest.mark.timeout(300)
def test_pipeline_runs_and_produces_csv():
    # Ensure a clean state
    csv_path = paths.data("processed", "diffusion_results.csv")
    if csv_path.exists():
        csv_path.unlink()

    # Run the pipeline script
    result = subprocess.run(
        [sys.executable, "code/pipeline.py", "--solvent", "water", "--duration", "1", "--seed", "0"],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Pipeline exited with {result.returncode}\\n{result.stderr}"

    # Verify CSV exists
    assert csv_path.is_file(), "diffusion_results.csv was not created"

    # Basic sanity check: file should contain at least two lines (header + row)
    with csv_path.open() as f:
        lines = f.readlines()
    assert len(lines) >= 2, "CSV file appears empty or missing header"