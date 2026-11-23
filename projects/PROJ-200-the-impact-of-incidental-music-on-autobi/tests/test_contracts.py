"""
Unit tests for contract validation.

The test simply imports the validation script and runs its main()
function, asserting that it exits with a zero status code.  This
confirms that the JSON Schema files are syntactically correct and
contain the definitions required by the specification.
"""

import subprocess
import sys
from pathlib import Path

import pytest

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Root directory of the repository (one level above ``code``)."""
    return Path(__file__).resolve().parents[2]

def test_contracts_validate(project_root: Path) -> None:
    """
    Execute ``code/validate_contracts.py`` and expect a successful run.

    The script prints a success message and returns exit code 0.
    """
    script_path = project_root / "code" / "validate_contracts.py"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    # The script should exit cleanly.
    assert result.returncode == 0, (
        f"Contract validation script failed (exit {result.returncode}). "
        f"Stdout: {result.stdout}\\nStderr: {result.stderr}"
    )
    # Basic sanity check on output.
    assert "All contract schemas are valid" in result.stdout, (
        "Expected success message not found in script output."
    )