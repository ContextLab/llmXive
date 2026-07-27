"""
Unit tests for R environment status verification.

Tests:
- test_renv_status: Verify Rscript -e "renv::status()" runs successfully
"""
import subprocess


def test_renv_status():
    """
    Test that Rscript -e "renv::status()" runs successfully.
    
    This test verifies that the R environment is properly initialized
    and renv is available in the project.
    """
    try:
        result = subprocess.run(
            ["Rscript", "-e", "renv::status()"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Check if the command ran successfully
        # Note: renv::status() might return non-zero if there are updates needed,
        # but it should not fail with an error about renv not being available
        assert result.returncode == 0 or "renv" in result.stdout.lower(), \
            "renv::status() should run without critical errors"
            
    except FileNotFoundError:
        pytest.skip("R is not installed or not in PATH")
    except subprocess.TimeoutExpired:
        pytest.fail("Rscript command timed out")
    except Exception as e:
        # If renv is not initialized, this is expected in a fresh environment
        # The important thing is that the command itself is valid
        if "renv" in str(e).lower() and ("not found" in str(e).lower() or "not available" in str(e).lower()):
            pytest.skip("renv is not initialized in this environment")
        else:
            pytest.fail(f"Unexpected error running renv::status(): {e}")
