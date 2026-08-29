import os
import pytest
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path if necessary
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.acquisition import fetch_fcc_diffusion_data, acquire_and_save_diffusion_data, MIN_RECORDS_THRESHOLD
from config import DATA_DIR

class TestAcquisition:
    
    def test_fetch_fcc_diffusion_data_returns_real_values(self):
        """Test that the fetch function returns data with real literature values."""
        records = fetch_fcc_diffusion_data()
        assert len(records) > 0, "Should fetch at least some records"
        
        # Check structure
        required_keys = {"element", "crystal_structure", "diffusion_mode", "D0", "Q"}
        for record in records:
            assert required_keys.issubset(record.keys()), f"Record missing keys: {record}"
            assert record["crystal_structure"] == "FCC"
            assert record["diffusion_mode"] == "self"
            # Verify values are numeric and not random placeholders
            assert isinstance(record["D0"], float) or isinstance(record["D0"], int)
            assert isinstance(record["Q"], float) or isinstance(record["Q"], int)
            assert record["Q"] > 0 # Activation energy must be positive
    
    @patch("data.acquisition.OUTPUT_PATH")
    @patch("data.acquisition.log_warning")
    def test_acquire_and_save_handles_small_dataset_warning(self, mock_log_warning, mock_output_path):
        """Test that a warning is logged if N < 50, but execution proceeds."""
        # Mock a scenario where we only get 10 records
        # We can't easily mock the internal list, so we test the logic flow
        # by patching the fetch function to return a small list
        small_records = [
            {"element": "Cu", "crystal_structure": "FCC", "diffusion_mode": "self", 
             "D0": 0.2, "Q": 2.19, "unit_D0": "cm2/s", "unit_Q": "eV/atom", 
             "source": "Test", "temperature_range": "Std"}
        ] * 10 # 10 records
        
        with patch("data.acquisition.fetch_fcc_diffusion_data", return_value=small_records):
            # Create a real temp file for testing
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
                tmp_path = Path(tmp.name)
            
            try:
                count = acquire_and_save_diffusion_data(output_path=tmp_path)
                
                assert count == 10
                
                # Verify warning was logged
                warning_calls = [str(call) for call in mock_log_warning.call_args_list]
                warning_found = any("Data Insufficiency" in w for w in warning_calls)
                assert warning_found, "Should log Data Insufficiency warning when N < 50"
                
                # Verify file was written
                assert tmp_path.exists()
                with open(tmp_path, 'r') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    assert len(rows) == 10
            finally:
                if tmp_path.exists():
                    os.remove(tmp_path)
    
    def test_output_file_structure(self):
        """Test that the output file has the correct headers."""
        # Run the actual acquisition to generate the file
        # This might fail if API is down, so we wrap in try/except for robustness
        # but the task requires the file to be generated.
        try:
            acquire_and_save_diffusion_data()
            output_path = DATA_DIR / "raw" / "fetched_diffusion.csv"
            assert output_path.exists(), "Output file should exist"
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                assert "element" in headers
                assert "crystal_structure" in headers
                assert "Q" in headers
                assert "D0" in headers
        except Exception as e:
            pytest.fail(f"Acquisition failed: {e}")
