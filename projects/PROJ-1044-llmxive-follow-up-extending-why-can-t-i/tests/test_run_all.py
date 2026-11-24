"""
Integration test for the quick‑start entry point.

It runs the pipeline driver with the default configuration and checks that:
  * the process exits with status 0,
  * the stdout contains the expected ``=== Pipeline Summary ===`` marker,
  * the three key artifacts required by the quick‑start guide exist.
"""

import subprocess
import sys
from pathlib import Path

def test_run_all_success(tmp_path: Path, monkeypatch):
    # Ensure the working directory is the project root (where the test lives)
    cwd = Path(__file__).resolve().parents[1]
    env = dict(**os.environ)

    # Run the pipeline driver with the config file
    cmd = [
        sys.executable,
        "-m",
        "src.pipeline.run_all",
        "--config",
        "configs/run.yaml",
    ]
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )

    # Basic exit‑code check
    assert result.returncode == 0, f"run_all exited with {result.returncode}\\nSTDOUT:{result.stdout}\\nSTDERR:{result.stderr}"

    # Look for the summary marker in stdout
    assert "=== Pipeline Summary ===" in result.stdout

    # Verify that the three quick‑start artifacts were created
    expected_paths = [
        Path("data/patches/manifest.csv"),
        Path("data/counterfactuals/temp_metadata.csv"),
        Path("figures/threshold_retention.png"),
    ]
    for p in expected_paths:
        assert (cwd / p).is_file(), f"Expected artifact {p} not found"
