import subprocess
import sys

def test_verify_seed_pinning_exit_code():
    """The compliance script should exit with code 0 when no violations exist."""
    result = subprocess.run(
        [sys.executable, "code/utils/verify_seed_pinning.py"],
        cwd=".",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script exited with {result.returncode}, output: {result.stdout}"