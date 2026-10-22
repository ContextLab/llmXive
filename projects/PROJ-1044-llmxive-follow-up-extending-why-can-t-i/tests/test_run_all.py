"""
Test that the ``src.pipeline.run_all`` entry‑point accepts the historic
command‑line arguments, creates the checksum manifest, and prints a
summary containing the expected fields.
"""

import subprocess
import sys
from pathlib import Path

import pytest

@pytest.mark.parametrize(
    "cli_args",
    [
        [
            "--num_videos",
            "10",
            "--lambda_values",
            "0.0",
            "0.1",
            "--seeds",
            "1",
            "2",
            "--flow_divergence_thresh",
            "0.15",
            "--feature_sim_thresh",
            "0.9",
            "--output_dir",
            "test_output",
        ],
        # Also test the config‑file path (uses the quick‑start style)
        ["--config", "configs/run.yaml"],
    ],
)
def test_run_all_cli(cli_args, tmp_path, monkeypatch):
    """
    Run the module as a subprocess and verify:
    * Exit code is 0.
    * ``data/checksums/manifest.csv`` exists after execution.
    * The printed summary contains the phrase ``Checksum manifest written``.
    """
    # Ensure we are in the project root
    cwd = Path(__file__).parents[2]  # project root
    env = {**dict(**os.environ), "PYTHONPATH": str(cwd)}
    result = subprocess.run(
        [sys.executable, "-m", "src.pipeline.run_all"] + cli_args,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Non‑zero exit: {result.stderr}"
    assert "Checksum manifest written" in result.stdout

    manifest = Path("data/checksums/manifest.csv")
    assert manifest.is_file(), "Manifest file was not created"
