"""
Unit test that ensures the project's noop stage runs without error.
The test invokes the same command as `code/verify_noop.py` but
asserts the return code directly, providing an additional verification
layer for the skeleton creation task.
"""
import sys
import subprocess
from pathlib import Path

def test_noop_stage_executes_successfully():
    """
    Execute `python -m code.main --stage noop` and assert a zero exit code.
    """
    cmd = [sys.executable, "-m", "code.main", "--stage", "noop"]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    # Write a temporary log for debugging (optional)
    log_path = Path("logs") / "test_noop_stage.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Return code: {result.returncode}\\n")
        f.write("STDOUT:\\n")
        f.write(result.stdout or "")
        f.write("\\nSTDERR:\\n")
        f.write(result.stderr or "")

    assert result.returncode == 0, (
        f"Noop stage exited with non‑zero status {result.returncode}. "
        f"See {log_path} for details."
    )