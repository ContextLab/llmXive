import subprocess
import sys
from pathlib import Path

def test_download_script_runs_successfully():
    """Execute the download script and assert it exits with code 0 and creates the log."""
    script_path = Path(__file__).resolve().parents[2] / "code" / "download_datasets.py"
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed with stderr: {result.stderr}"
    # Verify that the log file was created and contains at least one entry.
    log_file = Path(__file__).resolve().parents[2] / "data" / "raw" / "download_log.txt"
    assert log_file.is_file(), "download_log.txt was not created"
    content = log_file.read_text()
    assert "=== Download run @" in content, "Log file does not contain a run header"
    # Basic sanity check: each resource name should appear in the log.
    for name in [
        "epic_kitchens_sample.zip",
        "dynamic_reliability_heuristic.py",
        "robocasa_benchmark.zip",
        "robotwin_benchmark.zip",
    ]:
        assert name in content, f"{name} not reported in download log"