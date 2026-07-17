import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_master_dataset import main, load_processed_earthquakes, load_processed_pressure_anomalies, generate_master_dataset
from config import get_processed_path

@pytest.fixture
def setup_test_data(tmp_path):
    """
    Setup minimal test data files required for T017.
    Since T016 and T015 are marked completed, we simulate their output
    to ensure T017 can run in isolation for testing.
    """
    processed_path = tmp_path / "processed"
    processed_path.mkdir(parents=True)
    
    # Mock T016 output: earthquakes_deduplicated.csv
    eq_data = {
        'event_id': ['EQ001', 'EQ002'],
        'magnitude': [5.0, 4.5],
        'depth': [10.0, 15.0],
        'lat': [60.0, 61.0],
        'lon': [-150.0, -151.0],
        'timestamp': ['2018-01-01', '2018-01-02']
    }
    eq_df = pd.DataFrame(eq_data)
    eq_df.to_csv(processed_path / "earthquakes_deduplicated.csv", index=False)
    
    # Mock T014/015 output: pressure_anomalies.csv
    pres_data = {
        'event_id': ['EQ001', 'EQ002'],
        'anomaly_value': [0.5, -0.2],
        'timestamp': ['2018-01-01', '2018-01-02'],
        'is_control': [False, False]
    }
    pres_df = pd.DataFrame(pres_data)
    pres_df.to_csv(processed_path / "pressure_anomalies.csv", index=False)
    
    return processed_path

def test_generate_master_dataset_integration(setup_test_data, monkeypatch):
    """
    Integration test for T017.
    Verifies that master_dataset.csv is created and contains expected structure.
    """
    processed_path = setup_test_data
    output_file = processed_path / "master_dataset.csv"
    
    # Mock config to use tmp_path
    import config
    original_get_processed_path = config.get_processed_path
    config.get_processed_path = lambda: processed_path
    
    try:
        # Run the generation
        result = main()
        
        # Assert exit code (0 for success)
        assert result == 0, "Main function should return 0 on success"
        
        # Assert file exists
        assert output_file.exists(), f"Output file {output_file} was not created"
        
        # Assert content
        master_df = pd.read_csv(output_file)
        
        # Check row count (2 events)
        assert len(master_df) == 2, f"Expected 2 rows, got {len(master_df)}"
        
        # Check required columns
        required_cols = ['event_id', 'magnitude', 'depth', 'lat', 'lon', 'timestamp', 'anomaly_value', 'is_control']
        for col in required_cols:
            assert col in master_df.columns, f"Missing column: {col}"
        
        # Check data integrity
        assert master_df['event_id'].iloc[0] == 'EQ001'
        assert master_df['anomaly_value'].iloc[0] == 0.5
        
    finally:
        # Restore original function
        config.get_processed_path = original_get_processed_path

def test_load_processed_earthquakes(setup_test_data, monkeypatch):
    """Test loading of earthquake data."""
    import config
    original_get_processed_path = config.get_processed_path
    config.get_processed_path = lambda: setup_test_data
    
    try:
        df = load_processed_earthquakes()
        assert len(df) == 2
        assert 'event_id' in df.columns
    finally:
        config.get_processed_path = original_get_processed_path

def test_load_processed_pressure_anomalies(setup_test_data, monkeypatch):
    """Test loading of pressure anomaly data."""
    import config
    original_get_processed_path = config.get_processed_path
    config.get_processed_path = lambda: setup_test_data
    
    try:
        df = load_processed_pressure_anomalies()
        assert len(df) == 2
        assert 'anomaly_value' in df.columns
    finally:
        config.get_processed_path = original_get_processed_path