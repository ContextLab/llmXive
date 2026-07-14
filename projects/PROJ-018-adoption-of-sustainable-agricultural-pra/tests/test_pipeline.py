"""Integration test that runs the full pipeline up to feature engineering.

The test invokes the three core scripts in order and verifies that the
engineered dataset and the validity‑metrics file are produced.
"""
import subprocess
from pathlib import Path

def _run_cmd(cmd: list[str]) -> None:
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
    )
    assert result.returncode == 0, f"Command {' '.join(cmd)} failed: {result.stderr}"

def test_end_to_end_feature_engineering(tmp_path, monkeypatch):
    """Run download → cleaning → feature engineering and check outputs."""
    # Ensure we are in the project root
    project_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(project_root)

    # 1. Synthetic download (the script now falls back to a tiny synthetic dataset)
    _run_cmd(["python", "code/01_download_data.py", "--synthetic"])

    # 2. Clean the data
    _run_cmd(["python", "code/02_clean_data.py"])

    # 3. Engineer features (this also produces validity metrics)
    _run_cmd(["python", "code/03_engineer_features.py"])

    # Verify outputs
    engineered = Path("data/processed/engineered_data.csv")
    metrics = Path("results/validity_metrics.yaml")
    assert engineered.is_file(), "Engineered data file missing."
    assert metrics.is_file(), "Validity metrics file missing."