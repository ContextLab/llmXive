import subprocess
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent

def test_black_config_valid():
    """Verify that black can parse the configuration and format a file without error."""
    # Create a temporary file with unformatted code
    test_code = "x=1+2\n"
    test_file = PROJECT_ROOT / "test_temp_format.py"
    
    try:
        test_file.write_text(test_code)
        
        # Run black on the file
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", str(test_file)],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        
        # If the file is unformatted, black returns 1, which is expected for the check
        # We just want to ensure it didn't crash due to config issues
        assert result.returncode in [0, 1], f"Black failed with config error: {result.stderr}"
        
    finally:
        if test_file.exists():
            test_file.unlink()

def test_ruff_config_valid():
    """Verify that ruff can parse the configuration and lint a file without error."""
    test_file = PROJECT_ROOT / "test_temp_lint.py"
    
    try:
        # Write a file with a minor issue (unused import) to trigger a lint result
        test_code = "import os\nimport sys\nprint('hello')\n"
        test_file.write_text(test_code)
        
        # Run ruff check
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(test_file)],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        
        # Ruff should run successfully (returncode 0 if clean, 1 if issues found)
        # We verify it doesn't crash due to config errors
        assert result.returncode in [0, 1], f"Ruff failed with config error: {result.stderr}"
        
    finally:
        if test_file.exists():
            test_file.unlink()