import pytest
import pandas as pd
import json
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import (
    get_data_raw_dir,
    get_data_processed_dir,
    get_max_elements,
    get_composition_sum_threshold
)
from ingestion.cleaner import DataCleaner

@pytest.fixture
def setup_test_environment():
    """
    Creates a temporary directory structure with mock raw data to test the cleaner.
    """
    temp_dir = tempfile.mkdtemp()
    raw_dir = Path(temp_dir) / "raw"
    processed_dir = Path(temp_dir) / "processed"
    raw_dir.mkdir()
    processed_dir.mkdir()

    # Mock data that passes filters
    mock_data = {
        "Sn": [60.0, 95.0, 40.0],
        "Ag": [20.0, 5.0, 30.0],
        "Cu": [20.0, 0.0, 30.0],
        "hardness_hv": [50.0, 60.0, 70.0],
        "measurement_temp_c": [25.0, 24.0, 26.0]
    }
    df_valid = pd.DataFrame(mock_data)
    df_valid.to_csv(raw_dir / "raw_lit.csv", index=False)

    # Mock data that fails element count (>3 elements)
    mock_data_fail_elements = {
        "Sn": [50.0],
        "Ag": [10.0],
        "Cu": [10.0],
        "Zn": [10.0],
        "Pb": [10.0],
        "hardness_hv": [50.0],
        "measurement_temp_c": [25.0]
    }
    df_fail_elements = pd.DataFrame(mock_data_fail_elements)
    df_fail_elements.to_csv(raw_dir / "raw_mp.json", index=False) # Save as csv for simplicity in test

    # Mock data that fails temp
    mock_data_fail_temp = {
        "Sn": [60.0],
        "Ag": [20.0],
        "Cu": [20.0],
        "hardness_hv": [50.0],
        "measurement_temp_c": [100.0] # Too hot
    }
    df_fail_temp = pd.DataFrame(mock_data_fail_temp)
    df_fail_temp.to_csv(raw_dir / "raw_slr.csv", index=False)

    # Mock data that fails composition sum
    mock_data_fail_comp = {
        "Sn": [10.0],
        "Ag": [10.0],
        "Cu": [10.0],
        "hardness_hv": [50.0],
        "measurement_temp_c": [25.0]
    }
    df_fail_comp = pd.DataFrame(mock_data_fail_comp)
    df_fail_comp.to_csv(raw_dir / "raw_openalloy.json", index=False)

    # Store paths for cleanup
    return {
        "temp_dir": temp_dir,
        "raw_dir": raw_dir,
        "processed_dir": processed_dir,
        "original_raw": get_data_raw_dir(),
        "original_processed": get_data_processed_dir()
    }

@pytest.mark.integration
def test_cleaning_pipeline(setup_test_environment):
    """
    Tests the full cleaning pipeline with mock data.
    """
    # Temporarily override config paths if possible, or mock the cleaner's internal paths
    # Since config.py uses global paths, we patch the cleaner instance or run in a way that respects the test data.
    # For this test, we will manually instantiate the cleaner and override its internal directory logic 
    # OR we assume the test environment has set up the global config to point to temp dirs (which is hard with global config).
    # Better approach: Patch the get_* functions or modify the cleaner to accept paths.
    # Given constraints, we will patch the cleaner's internal attributes after instantiation.
    
    # Note: In a real CI, we might need to mock the config module. 
    # For this test, we assume the global config points to the temp dirs or we patch the cleaner.
    # Let's assume we can patch the cleaner's internal paths.
    
    # Actually, let's just run the cleaner and check the outputs relative to the test's expected behavior.
    # We will patch the global config functions if possible, but for simplicity in this snippet:
    # We will create a cleaner and override its processed_dir and raw_dir logic by monkey-patching.
    
    # Simpler approach for this specific test:
    # We will create the DataCleaner and manually set its directories to the temp ones.
    # This requires modifying the class slightly or accessing protected members.
    # Let's assume the cleaner uses the global config. We will need to mock the config module.
    
    # Since we cannot easily mock global config in this snippet without side effects,
    # we will assume the test runner sets up the environment variables or config file.
    # Alternatively, we can just test the logic functions directly.
    
    # Let's test the logic by calling the methods directly with a dataframe.
    cleaner = DataCleaner()
    
    # Override internal paths for this test instance
    cleaner.processed_dir = setup_test_environment['processed_dir']
    # We need to force load_raw_data to look at our temp raw_dir
    # This is tricky with the global config. 
    # We will patch the method.
    original_load = DataCleaner.load_raw_data
    
    def mock_load(self):
        return pd.read_csv(setup_test_environment['raw_dir'] / 'raw_lit.csv')
    
    DataCleaner.load_raw_data = mock_load
    
    try:
        result = cleaner.run_cleaning_pipeline()
        
        # Assertions
        assert len(result) > 0, "Result should not be empty"
        
        # Check output files
        assert (setup_test_environment['processed_dir'] / "solder_hardness_cleaned.csv").exists()
        assert (setup_test_environment['processed_dir'] / ".ingestion_status.json").exists()
        
        # Check status content
        with open(setup_test_environment['processed_dir'] / ".ingestion_status.json") as f:
            status = json.load(f)
            assert "exact_N" in status
            assert status["threshold_status"] in ["N>=100", "50<=N<100", "N<50"]
            
    finally:
        # Restore original method
        DataCleaner.load_raw_data = original_load
        # Cleanup
        shutil.rmtree(setup_test_environment['temp_dir'])
