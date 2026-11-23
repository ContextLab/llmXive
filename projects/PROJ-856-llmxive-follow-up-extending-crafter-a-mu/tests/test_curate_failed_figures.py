import subprocess
import sys
from pathlib import Path

def test_curate_fails_without_verified_source():
    """
    The script must exit with a non‑zero status and emit the required
    error message when the verified dataset URL is not reachable.
    """
    result = subprocess.run(
        [sys.executable, "-m", "src.curators.curate_failed_figures", "--output-dir", "data_test"],
        capture_output=True,
        text=True,
    )
    # The script should have printed the error to stderr.
    assert "Verified dataset source not available" in result.stderr
    # Non‑zero exit code indicates the expected failure.
    assert result.returncode != 0

def test_no_artifacts_created_on_failure():
    """
    When the script aborts, it must not leave partial output directories.
    """
    output_dir = Path("data_test")
    # Ensure a clean state.
    if output_dir.exists():
        for child in output_dir.rglob("*"):
            child.unlink()
        output_dir.rmdir()
    # Run the script (expected to fail).
    subprocess.run(
        [sys.executable, "-m", "src.curators.curate_failed_figures", "--output-dir", str(output_dir)],
        capture_output=True,
        text=True,
    )
    # The top‑level output directory should not exist because the script
    # aborts before creating any sub‑folders.
    assert not output_dir.exists()