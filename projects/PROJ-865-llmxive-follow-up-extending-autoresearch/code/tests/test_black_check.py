import subprocess
import sys
from pathlib import Path
import pytest

def test_black_check_passes():
    """
    Verify that `black --check` on the `code/` directory returns exit code 0.
    This ensures all Python files in the project adhere to Black formatting standards.
    """
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        pytest.fail(f"Code directory does not exist: {code_dir}")
    
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--quiet", str(code_dir)],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, (
        f"Black formatting check failed.\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}\n"
        f"Return code: {result.returncode}"
    )
