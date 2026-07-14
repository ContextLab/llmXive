"""
Integration test that runs the full pipeline via ``code/main.py`` and
verifies that the two required processed CSV files are created.
"""
import subprocess
from pathlib import Path

def test_full_pipeline():
    # Execute the pipeline script.
    result = subprocess.run(
        ["python", "code/main.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"

    # Verify that the expected outputs exist.
    clone_csv = Path("data/processed/clone_metrics.csv")
    perplexity_csv = Path("data/processed/perplexity_scores.csv")
    assert clone_csv.is_file(), "clone_metrics.csv missing"
    assert perplexity_csv.is_file(), "perplexity_scores.csv missing"
