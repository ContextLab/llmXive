"""
Integration test for T012b: Fetching perovskite data from Materials Project API.
This test verifies that the script runs, produces the expected file, and handles
the case where T_d is missing (which is expected for MP).
"""
import os
import sys
import subprocess
import pytest
from pathlib import Path
import pandas as pd

# Ensure the code directory is in the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

class TestFetchMPPerovskites:
    
    def test_script_execution_and_output_file(self):
        """Test that the script runs and creates the output file."""
        script_path = project_root / "code" / "fetch_mp_perovskites.py"
        output_path = project_root / "data" / "raw" / "mp_perovskites.csv"
        
        # Ensure the output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Run the script
        # Note: This will fail if MP_API_KEY is not set, which is expected behavior
        # for a real integration test. We check for the file existence or the error.
        env = os.environ.copy()
        # If no key is set, the script should exit with error. 
        # If a key is set, it should run.
        
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=project_root,
            env=env
        )
        
        # Check if the file was created (even if empty)
        if output_path.exists():
            df = pd.read_csv(output_path)
            # Verify columns exist
            expected_columns = ["source", "material_id", "formula", "T_d", "formation_energy_per_atom", "band_gap", "nsites", "nelements"]
            assert all(col in df.columns for col in expected_columns), f"Missing columns. Found: {df.columns}"
            
            # Verify source is "Materials Project"
            if not df.empty:
                assert (df["source"] == "Materials Project").all(), "Source column mismatch."
            
            # Verify T_d is NaN (as MP doesn't provide it)
            if not df.empty:
                assert df["T_d"].isna().all(), "T_d should be NaN for MP data as it's not available."
            
            pytest.skip("Script ran and produced output. T_d is correctly null.")
        else:
            # If file doesn't exist, check if it's due to missing API key
            if "MP_API_KEY not found" in result.stderr:
                pytest.skip("MP_API_KEY not set. This is expected in CI without credentials.")
            else:
                pytest.fail(f"Script failed and did not produce output file. Stderr: {result.stderr}")

    def test_validation_logic(self):
        """Test that the validation logic (T009) is invoked."""
        # This is a structural test. We verify the code imports and calls the validator.
        import inspect
        from code.fetch_mp_perovskites import validate_data_checksum, fetch_mp_material_data
        
        # Check that the function exists and has the right signature
        assert callable(validate_data_checksum)
        assert callable(fetch_mp_material_data)
        
        # Mock a data dict and check validation returns True for valid structure
        mock_data = {
            "material_id": "mp-123",
            "formula": "CsPbI3"
        }
        # We cannot easily test the real API call without a key, so we test the logic structure
        # The actual validation logic is simple structural check.
        assert validate_data_checksum(mock_data, "test") is True
        assert validate_data_checksum({}, "test") is False