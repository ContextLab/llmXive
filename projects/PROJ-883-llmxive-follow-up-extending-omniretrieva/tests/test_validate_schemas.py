"""Test that the contract schemas validate their sample instances."""

import subprocess
import sys
from pathlib import Path

def test_validate_schemas_success():
    """Run the validation script and assert it exits with code 0."""
    script_path = Path(__file__).resolve().parents[2] / "code" / "validate_schemas.py"
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    assert result.returncode == 0, f"Validation failed: {result.stdout}\\n{result.stderr}"
    assert "All schemas validated successfully." in result.stdout

# The test will be discovered and executed by pytest automatically.