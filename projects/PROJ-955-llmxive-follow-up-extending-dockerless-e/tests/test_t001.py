import subprocess
import sys
from pathlib import Path

def test_dry_run_creates_artifacts():
    """Run the dry‑run CLI and verify that all required artefacts exist."""
    # Execute the module as a subprocess to emulate the quick‑start command.
    result = subprocess.run(
        [sys.executable, "-m", "src.cli.run_pipeline", "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"CLI exited with {result.returncode}: {result.stderr}"

    # Verify the sample CSV was created.
    sample_csv = Path("data/results/sample_run.csv")
    assert sample_csv.is_file(), "sample_run.csv was not created"

    # Verify the source‑code directories required by the pipeline exist.
    assert Path("src/pipeline").is_dir(), "src/pipeline directory missing"
    assert Path("src/cli").is_dir(), "src/cli directory missing"

    # Verify the top‑level data directories exist.
    for d in ["data", "interim", "features", "models", "reports"]:
        assert Path(d).is_dir(), f"Top‑level directory {d} missing"