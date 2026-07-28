import subprocess
import sys
from pathlib import Path

def test_directories_exist():
    """CI test that verifies all skeleton directories exist."""
    script_path = Path(__file__).resolve().parent.parent.parent / "ci" / "check_skeleton_ci.py"
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    assert result.returncode == 0, f"CI check failed: {result.stderr}"
