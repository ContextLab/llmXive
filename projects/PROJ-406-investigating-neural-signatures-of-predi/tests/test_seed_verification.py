import subprocess
import sys
from pathlib import Path
from llmxive_toolkit import paths

def test_seed_verification_log():
    """Run the seed verification script and ensure the log contains two identical lines."""
    # Execute the script
    result = subprocess.run(
        [sys.executable, "-m", "src.utils.generate_seed_log"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script exited with {result.returncode}"

    log_path = paths.outputs("seed_verification.log")
    assert log_path.is_file(), "seed_verification.log was not created"

    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 2, f"Expected 2 lines, got {len(lines)}"
    assert lines[0] == lines[1], "The two random draws are not identical"