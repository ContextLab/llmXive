import subprocess
import sys
from pathlib import Path

def test_requirements_install():
    """
    Verify that the project's pinned requirements can be installed without error.
    The test runs `python -m pip install -r code/requirements.txt` and asserts
    a zero exit code. All listed packages are already present in the execution
    environment, so pip should report them as satisfied and exit successfully.
    """
    # Resolve the path to the requirements file relative to the repository root
    repo_root = Path(__file__).resolve().parents[2]
    req_file = repo_root / "code" / "requirements.txt"

    # Execute pip install using the current Python interpreter
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # If pip fails, include its stdout/stderr in the assertion message for debugging
    assert result.returncode == 0, (
        f"Pip install exited with code {result.returncode}\\n"
        f"STDOUT:\\n{result.stdout}\\nSTDERR:\\n{result.stderr}"
    )