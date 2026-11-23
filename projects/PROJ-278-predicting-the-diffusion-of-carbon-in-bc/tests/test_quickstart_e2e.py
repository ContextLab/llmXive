import os
import pytest
from pathlib import Path
import subprocess
import sys

# Path to the project root
PROJECT_ROOT = Path(__file__).parent.parent

@pytest.mark.integration
def test_quickstart_e2e_reproducibility():
    """
    End-to-end test to verify the quickstart.md workflow runs successfully.
    This test executes the validation script which in turn checks all artifacts.
    """
    # Ensure we are in the project root
    os.chdir(PROJECT_ROOT)

    # Construct the command to run the validation script
    # Assuming the script is invoked via python code/05_validate.py
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "code" / "05_validate.py")
    ]

    # Run the command
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300, # 5 minutes timeout
            check=False
        )
        
        # Assert exit code is 0 (success)
        assert result.returncode == 0, (
            f"Quickstart validation failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
        
        # Assert that the output contains success messages
        assert "Validation PASSED" in result.stdout or "Validation PASSED" in result.stderr, \
            "Validation did not report success in output logs."
            
    except subprocess.TimeoutExpired:
        pytest.fail("Quickstart validation timed out after 5 minutes.")
    except Exception as e:
        pytest.fail(f"Error running quickstart validation: {str(e)}")
