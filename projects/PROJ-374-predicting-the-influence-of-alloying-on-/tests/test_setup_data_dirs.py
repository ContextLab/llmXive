import os
from pathlib import Path
import subprocess
import sys

def test_data_directories_created(tmp_path: Path):
    """
    Run the setup_data_dirs script and verify that the expected directories exist.
    """
    # Determine project root relative to this test file
    project_root = Path(__file__).resolve().parents[2]  # tests/ -> code/ -> project root
    script_path = project_root / "code" / "setup_data_dirs.py"

    # Execute the script
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    assert result.returncode == 0, f"Script exited with error: {result.stderr}"

    # Verify directories
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    assert raw_dir.is_dir(), f"Missing directory: {raw_dir}"
    assert processed_dir.is_dir(), f"Missing directory: {processed_dir}"