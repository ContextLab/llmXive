import pytest
import pandas as pd
import os
from pathlib import Path
import tempfile
import shutil

from ingestion import main

@pytest.fixture
def mock_unified_data():
    """
    Creates a temporary CSV file with mock data for T013 testing.
    Includes samples that should be filtered (pH out of range, heterogeneous)
    and samples that should remain.
    """
    data = {
        'sample_id': ['S001', 'S002', 'S003', 'S004', 'S005', 'S006', 'S007', 'S008'],
        'timestamp': [
            '2023-06-01T10:00:00', '2023-06-01T10:15:00', '2023-06-01T10:30:00',
            '2023-06-01T11:00:00', '2023-06-01T11:15:00', '2023-06-01T11:30:00',
            '2023-06-01T12:00:00', '2023-06-01T12:15:00'
        ],
        'pH': [7.2, 7.3, 0.5, 7.1, 10.5, 7.0, 7.5, 7.4], # S003 (0.5) and S005 (10.5) are outliers
        'temp': [2.5, 2.6, 2.4, 2.3, 2.5, 2.4, 2.7, 2.6],
        'pH_sd': [0.05, 0.06, 0.04, 0.03, 0.05, 0.04, 0.30, 0.05], # S007 has high SD (0.30 > 0.2)
        'location': ['SiteA', 'SiteA', 'SiteA', 'SiteB', 'SiteB', 'SiteB', 'SiteC', 'SiteC'],
        'fastq_path': ['/data/raw/S001.fastq'] * 8,
        'deployment_event': ['DE01'] * 8,
        'sensor_id': ['SENSOR_A'] * 8,
        'coordinates': ['45.1, -123.5'] * 8,
        'pH_heterogeneous': [False, False, False, False, False, False, True, False]
    }
    return pd.DataFrame(data)

def test_t013_filtering(mock_unified_data, tmp_path):
    """
    Test that T013 correctly filters out:
    1. pH < 1.0 or pH > 10.0
    2. pH_heterogeneous == True
    """
    # Setup input file
    input_file = tmp_path / "unified_sample_table.csv"
    mock_unified_data.to_csv(input_file, index=False)
    
    # Setup output file path
    output_file = tmp_path / "filtered_unified_sample_table.csv"
    
    # Mock the global paths or modify the script to accept arguments?
    # Since main() uses hardcoded paths, we need to temporarily patch or
    # rely on the fact that we can run the script with the file in place.
    # However, main() expects files in data/processed/.
    # We will simulate the environment by creating the directory structure.
    
    data_dir = Path("data/processed")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy mock data to the expected location
    shutil.copy(input_file, data_dir / "unified_sample_table.csv")
    
    try:
        # Run the main function (which executes T013 logic)
        # We need to be careful not to mess up the global state if run in a test suite.
        # But for this specific test, we assume it's run in isolation or the side effects are acceptable.
        
        # Re-import to ensure we get the latest code if needed, but usually not necessary
        import importlib
        import ingestion
        importlib.reload(ingestion)
        
        ingestion.main()
        
        # Check output
        assert output_file.exists(), "Filtered output file was not created."
        
        result_df = pd.read_csv(output_file)
        
        # Verify filtering logic
        # Expected to be removed: S003 (pH 0.5), S005 (pH 10.5), S007 (pH_heterogeneous=True)
        # Expected to remain: S001, S002, S004, S006, S008
        expected_ids = {'S001', 'S002', 'S004', 'S006', 'S008'}
        result_ids = set(result_df['sample_id'].tolist())
        
        assert result_ids == expected_ids, f"Expected {expected_ids}, got {result_ids}"
        
        # Verify no outliers or heterogeneous samples remain
        assert not any(result_df['pH'] < 1.0), "Outlier pH < 1.0 found in filtered data."
        assert not any(result_df['pH'] > 10.0), "Outlier pH > 10.0 found in filtered data."
        assert not any(result_df['pH_heterogeneous'] == True), "Heterogeneous samples found in filtered data."
        
    finally:
        # Cleanup
        if (data_dir / "unified_sample_table.csv").exists():
            (data_dir / "unified_sample_table.csv").unlink()
        if output_file.exists():
            output_file.unlink()
        if data_dir.exists():
            data_dir.rmdir()
            # Try to remove parent if empty, but be careful not to remove real data
            if data_dir.parent.exists() and not any(data_dir.parent.iterdir()):
                data_dir.parent.rmdir()