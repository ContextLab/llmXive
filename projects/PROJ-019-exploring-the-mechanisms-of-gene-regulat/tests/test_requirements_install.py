"""
Test that the project's requirements can be installed without errors.
This provides evidence for verification step T027.
"""

import subprocess
import sys
from pathlib import Path

def test_requirements_install(tmp_path):
    """
    Run `pip install -r requirements.txt` in a subprocess and assert that it exits with code 0.
    The test uses the project's root directory as the working directory.
    """
    # Resolve the path to the requirements file relative to the project root
    project_root = Path(__file__).resolve().parents[2]  # tests/ -> project root
    requirements_file = project_root / "requirements.txt"
    assert requirements_file.is_file(), f"requirements.txt not found at {requirements_file}"

    # Execute pip install
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # For debugging, include the pip output in the assertion message
    assert result.returncode == 0, (
        f"`pip install -r requirements.txt` failed with exit code {result.returncode}\n"
        f"Output:\n{result.stdout}"
    )

    # Optionally, write a marker file indicating success (useful for downstream checks)
    marker_path = project_root / "data" / "processed" / "requirements_installed.txt"
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text("requirements installed successfully")