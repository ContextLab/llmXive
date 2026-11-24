import subprocess
import sys
from pathlib import Path

def test_requirements_install():
    """Test that the project's requirements can be installed without error."""
    # Locate the requirements file relative to the project root
    req_path = Path(__file__).resolve().parents[2] / "code" / "requirements.txt"

    # Verify the file exists and is not empty
    assert req_path.is_file(), f"Requirements file not found at {req_path}"
    assert req_path.stat().st_size > 0, "Requirements file is empty"

    # Run pip install in a subprocess using the current Python interpreter
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Ensure the installation succeeded
    assert result.returncode == 0, f"pip install failed:\n{result.stdout}"