"""Integration test for the ``generate_significance`` script.

The test creates a minimal ``results/metrics.csv`` file with deterministic
values for five seeds, runs the script, and checks that the expected
``results/significance.csv`` file is produced and contains valid p‑values.
"""
import csv
from pathlib import Path
import subprocess
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

@pytest.fixture
def dummy_metrics(tmp_path: Path):
    """Create a dummy ``metrics.csv`` with five seeds for both models."""
    results_dir = PROJECT_ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = results_dir / "metrics.csv"
    with metrics_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["seed", "model", "mae", "rmse"])
        writer.writeheader()
        # Deterministic values – GNN slightly better than RF
        for seed in range(1, 6):
            writer.writerow({"seed": seed, "model": "gnn", "mae": 0.1 * seed, "rmse": 0.2 * seed})
            writer.writerow({"seed": seed, "model": "rf", "mae": 0.12 * seed, "rmse": 0.22 * seed})
    return metrics_path

def test_generate_significance_creates_csv(dummy_metrics: Path):
    """Run the script and verify the output CSV exists and looks correct."""
    script_path = PROJECT_ROOT / "code" / "analysis" / "generate_significance.py"
    # Execute the script using the same Python interpreter
    result = subprocess.run([sys.executable, str(script_path)], cwd=PROJECT_ROOT, capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    output_path = PROJECT_ROOT / "results" / "significance.csv"
    assert output_path.is_file(), "significance.csv was not created"

    with output_path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Expect two rows: mae and rmse
    assert len(rows) == 2
    metrics = {row["metric"]: float(row["p_value"]) for row in rows}
    # p‑values should be > 0 and <= 1
    for p in metrics.values():
        assert 0.0 < p <= 1.0, f"Invalid p‑value: {p}"