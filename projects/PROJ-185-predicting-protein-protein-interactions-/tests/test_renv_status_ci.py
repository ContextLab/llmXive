"""
Unit test that runs `Rscript -e "renv::status()"` and fails on non-zero exit.

This test verifies that the R environment is properly initialized and that
renv can successfully report its status. It ensures the R project is
correctly configured before running any R-dependent pipeline steps.
"""
import subprocess
import sys
import pytest
from pathlib import Path

def test_renv_status_command_success():
    """
    Test that running `Rscript -e "renv::status()"` exits with code 0.
    
    This confirms that:
    1. R is installed and accessible in PATH
    2. The renv package is installed and functional
    3. The renv project is properly initialized (renv.lock exists)
    """
    # Construct the command to run renv status
    cmd = [
        "Rscript",
        "-e",
        "renv::status()"
    ]
    
    try:
        # Run the command and capture output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout for R startup
        )
        
        # Assert the command succeeded
        if result.returncode != 0:
            pytest.fail(
                f"Rscript command failed with exit code {result.returncode}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )
        
        # Verify that the output contains expected renv status information
        output = result.stdout + result.stderr
        assert "renv" in output.lower(), "Expected 'renv' in output to confirm package execution"
        
    except subprocess.TimeoutExpired:
        pytest.fail("Rscript command timed out after 60 seconds")
    except FileNotFoundError:
        pytest.fail(
            "Rscript not found in PATH. Ensure R is installed and accessible. "
            "This is required for T003d verification."
        )
    except Exception as e:
        pytest.fail(f"Unexpected error running Rscript: {e}")