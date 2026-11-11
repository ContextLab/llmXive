import subprocess
import sys
from pathlib import Path

def test_verify_checksums_success(tmp_path):
    """
    Integration test that runs the verification script on the existing
    data/checksums.txt. The script should exit with status 0 and produce
    a log file containing only “OK” entries.
    """
    project_root = Path(__file__).resolve().parents[2]  # project root
    script_path = project_root / "scripts" / "verify_checksums.sh"

    # Ensure the log directory is clean before the run
    log_path = project_root / "data" / "env_evidence" / "checksum_verify.log"
    if log_path.exists():
        log_path.unlink()

    # Run the script
    result = subprocess.run(
        [str(script_path)], cwd=str(project_root), capture_output=True, text=True
    )

    # The script should exit with code 0
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # The log file must exist and contain only OK lines (plus headers)
    assert log_path.is_file()
    log_contents = log_path.read_text()
    assert "ALL FILES MATCH" in log_contents
    # No line should contain the word FAIL
    assert "FAIL" not in log_contents.upper()