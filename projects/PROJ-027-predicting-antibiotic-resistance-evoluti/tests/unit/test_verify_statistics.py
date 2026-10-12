"""
Unit test for the statistical sanity‑check script (verify_statistics.py).

The test creates minimal valid permutation_results.json and
sensitivity_sweep.csv files in a temporary directory, runs the script,
and asserts that it exits with status 0 and that the verification summary
contains the expected entries.
"""

import sys
import json
import tempfile
from pathlib import Path
import subprocess

import pytest

# Import the script as a module to reuse helper functions if needed
SCRIPT_PATH = Path(__file__).resolve().parents[2] / "code" / "04_validate" / "verify_statistics.py"


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data/processed directory with required inputs."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)

    # Minimal valid permutation_results.json (>=1000 permutations)
    perm_file = processed_dir / "permutation_results.json"
    perm_content = {
        "p_value": 0.03,
        "significance": True,
        "permutation_count": 1500,
        "observed_statistic": 1.23,
    }
    perm_file.write_text(json.dumps(perm_content), encoding="utf-8")

    # Minimal valid sensitivity_sweep.csv
    sweep_file = processed_dir / "sensitivity_sweep.csv"
    sweep_content = """threshold,false_positive_rate,false_negative_rate,fp_rate_range
0.4,0.10,0.20,0.10-0.20
0.45,0.12,0.18,0.12-0.18
0.5,0.15,0.15,0.15-0.15
0.55,0.18,0.12,0.12-0.18
0.6,0.20,0.10,0.10-0.20
"""
    sweep_file.write_text(sweep_content, encoding="utf-8")

    return tmp_path


def test_verify_statistics_success(temp_data_dir, monkeypatch):
    """
    Run verify_statistics.py against the temporary data and ensure it succeeds.
    """
    # Patch the llmxive toolkit paths function to point to our temp directory
    from llmxive_toolkit import paths as toolkit_paths

    def fake_data(*parts):
        # parts[0] should be 'processed' for our use‑case
        return Path(temp_data_dir) / "data" / Path(*parts)

    monkeypatch.setattr(toolkit_paths, "data", fake_data)

    # Execute the script as a subprocess to mimic real execution
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify that verification_summary.json now exists and contains the expected keys
    summary_path = Path(temp_data_dir) / "data" / "processed" / "verification_summary.json"
    assert summary_path.is_file(), "verification_summary.json was not created"

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert "statistics_check" in summary, "statistics_check entry missing"
    stats = summary["statistics_check"]
    assert stats["pass"] is True
    assert stats["permutation_check"]["pass"] is True
    assert stats["sensitivity_check"]["pass"] is True
    assert "checked_at" in stats

    # The overall_pass flag should reflect the successful checks
    assert summary["overall_pass"] is True