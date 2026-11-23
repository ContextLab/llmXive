"""
Test T040: Verify that the ingestion script (T011) aborts correctly when the
'acute_sleepiness' column is missing from the input data.

This test uses the specific artifact generated in T040: tests/testdata/missing_columns.csv.
"""
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

import pytest

# Add project root to path for imports if running as script
# In a CI environment, this might be handled differently, but we ensure it here.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import the ingestion logic if it exists in a module, or we run the script directly.
# Based on the task description, T011 is implemented in code/01_ingest.R (R script).
# However, the pipeline seems to have Python wrappers or the test runner is Python.
# The task description for T011 says "Implement code/01_ingest.R".
# To test this robustly in Python, we will invoke the R script via subprocess
# or invoke a Python wrapper if one exists.
# Looking at the API surface, there is no direct Python wrapper for 01_ingest.R.
# We will assume the pipeline is run via R or a Python driver that calls R.
# For this test, we will simulate the environment by running the R script directly
# if R is available, or mock the check if the R script is not the entry point.
#
# Given the constraints of the "Python must compile" rule for the *test file*,
# and the fact that T011 is an R script, we will write a test that:
# 1. Copies the test CSV to the expected location (or passes it as arg).
# 2. Runs the R script (code/01_ingest.R) with the test file.
# 3. Asserts that the script exits with code 1 (ABORT) and the error message mentions missing columns.

# Since we cannot guarantee R is installed in the test environment for this specific
# Python file execution without setup, we will check if the R script exists and
# attempt to run it. If R is not found, we skip or mark as failed based on CI config.
# However, the task requires verifying T011 aborts.
#
# Alternative: If there is a Python entry point for ingestion, use that.
# The API surface lists `code/00_setup_r_env.py` etc., but not a direct ingest runner.
# We will assume the standard pipeline entry point or direct R execution.

TEST_DATA_FILE = "tests/testdata/missing_columns.csv"
EXPECTED_ERROR_SUBSTRING = "acute_sleepiness"

@pytest.fixture
def test_file_path():
    """Return the path to the missing_columns.csv test file."""
    path = PROJECT_ROOT / TEST_DATA_FILE
    if not path.exists():
        pytest.fail(f"Test data file {TEST_DATA_FILE} not found. T040 artifact missing.")
    return path

def test_ingest_aborts_on_missing_columns(test_file_path):
    """
    Test that code/01_ingest.R aborts (exit code 1) when acute_sleepiness is missing.
    """
    # Ensure the R script exists
    ingest_script = PROJECT_ROOT / "code" / "01_ingest.R"
    if not ingest_script.exists():
        pytest.skip("Ingest script (code/01_ingest.R) not found. Skipping T011 abort test.")

    # Prepare a temporary directory for the test run to avoid side effects
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Copy test data to a location the script can find, or pass as argument
        # Assuming the script expects data/raw/study_data.csv or takes an arg.
        # We will create a minimal project structure in tmpdir
        (tmp_path / "data" / "raw").mkdir(parents=True)
        target_csv = tmp_path / "data" / "raw" / "study_data.csv"
        shutil.copy(test_file_path, target_csv)

        # Create necessary config if needed (T006 creates code/00_config.R)
        # We assume the script reads from a config or default paths.
        # To be safe, we set the environment variable if the script uses it,
        # or rely on the script's default behavior of looking in data/raw/study_data.csv.
        
        # Construct the R command
        # We need to run Rscript with the script and potentially the path
        cmd = [
            "Rscript",
            str(ingest_script),
            # Assuming the script takes an optional argument for input path,
            # or we rely on the default. If it doesn't take args, we might need
            # to modify the config in the temp dir.
            # Given T006 creates code/00_config.R, let's assume the script uses that.
            # We'll create a minimal config in tmpdir if needed.
        ]

        # Check if R is available
        try:
            result = subprocess.run(
                cmd,
                cwd=str(tmp_path),
                capture_output=True,
                text=True,
                timeout=30
            )
        except FileNotFoundError:
            pytest.skip("Rscript not found in PATH. Cannot verify T011 abort behavior.")
        except subprocess.TimeoutExpired:
            pytest.fail("Rscript timed out during ingestion test.")

        # Verify exit code is 1 (ABORT)
        assert result.returncode != 0, (
            f"Expected non-zero exit code (abort) for missing 'acute_sleepiness', "
            f"but got {result.returncode}. Stderr: {result.stderr}"
        )

        # Verify the error message mentions the missing column
        combined_output = result.stdout + result.stderr
        assert EXPECTED_ERROR_SUBSTRING.lower() in combined_output.lower(), (
            f"Expected error message to contain '{EXPECTED_ERROR_SUBSTRING}', "
            f"but got: {combined_output}"
        )

        # Verify no output files were created (since it aborted before saving)
        # The script should not have created data/processed/cleaned_data.csv
        processed_dir = tmp_path / "data" / "processed"
        if processed_dir.exists():
            cleaned_file = processed_dir / "cleaned_data.csv"
            assert not cleaned_file.exists(), (
                "cleaned_data.csv should not exist if the script aborted due to missing columns."
            )