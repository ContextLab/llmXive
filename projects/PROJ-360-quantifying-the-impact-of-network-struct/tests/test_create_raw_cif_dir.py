"""
Test that ``code/create_raw_cif_dir.py`` creates the required directory.
The test runs the script as a subprocess and then checks that the
``data/raw/cif`` directory exists.
"""
import subprocess
import sys
from pathlib import Path

def test_create_raw_cif_dir():
    script_path = Path("code/create_raw_cif_dir.py")
    # Execute the script
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    assert result.returncode == 0, f"Script exited with {result.returncode}: {result.stderr}"
    # Verify the directory was created
    cif_dir = Path("data") / "raw" / "cif"
    assert cif_dir.is_dir(), f"Directory {cif_dir} was not created"