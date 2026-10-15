import subprocess
import sys
from pathlib import Path

def test_analyze_results_runs_successfully():
    """Execute the analysis script and verify that the expected output files are created."""
    script = Path("code/analyze_results.py")
    assert script.exists()

    # Run the script with explicit arguments
    result = subprocess.run(
        [sys.executable, str(script), "--input", "data/logs/simulation_results.csv", "--output-dir", "results"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, f"Script failed: {result.stdout}\\n{result.stderr}"

    # Check that the two output artifacts exist and are non‑empty
    regression_path = Path("results", "regression_summary.json")
    hypothesis_path = Path("results", "hypothesis_summary.md")
    assert regression_path.is_file() and regression_path.stat().st_size > 0
    assert hypothesis_path.is_file() and hypothesis_path.stat().st_size > 0