import os
import subprocess
import tempfile
import pytest

def test_r_packages_installation():
    """
    Test that the R installation script runs without error.
    This test verifies that the R environment can be initialized
    with the required Bioconductor packages.
    """
    # Path to the R installation script
    r_script_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "code",
        "R",
        "install_packages.R"
    )

    if not os.path.exists(r_script_path):
        pytest.skip("R installation script not found, skipping test.")

    # Run the R script
    try:
        result = subprocess.run(
            ["Rscript", r_script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        # Check if the script ran successfully
        assert result.returncode == 0, (
            f"R script failed with return code {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
        
        # Verify that the expected packages were installed
        expected_packages = [
            "DESeq2",
            "org.At.tair.db",
            "biomaRt",
            "sva",
            "GEOquery"
        ]
        
        for pkg in expected_packages:
            assert pkg in result.stdout or pkg in result.stderr, (
                f"Package {pkg} installation message not found in output."
            )
            
    except subprocess.TimeoutExpired:
        pytest.fail("R installation script timed out.")
    except FileNotFoundError:
        pytest.skip("Rscript not found in PATH, skipping test.")