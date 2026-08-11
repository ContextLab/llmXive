import os
import pandas as pd
import pytest
from pathlib import Path
import shutil
import tempfile

from ingestion import run_ingestion_pipeline, main

@pytest.fixture
def mock_data_dir():
    """Create temporary directory with mock data files."""
    temp_dir = tempfile.mkdtemp()
    raw_dir = Path(temp_dir) / "data" / "raw"
    processed_dir = Path(temp_dir) / "data" / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock pH data
    ph_data = """timestamp,value,deployment_event,sensor_id,coordinates,location
2023-06-15 08:30:00,6.85,EVT001,SENSOR01,12.345,-67.890,Site_A
2023-06-15 08:45:00,6.92,EVT001,SENSOR01,12.345,-67.890,Site_A
2023-06-15 09:00:00,6.78,EVT001,SENSOR01,12.345,-67.890,Site_A
2023-06-15 08:30:00,7.12,EVT001,SENSOR02,12.350,-67.895,Site_B
2023-06-15 08:45:00,7.05,EVT001,SENSOR02,12.350,-67.895,Site_B
2023-06-15 09:00:00,7.18,EVT001,SENSOR02,12.350,-67.895,Site_B
2023-06-15 08:30:00,6.55,EVT001,SENSOR03,12.360,-67.900,Site_C
2023-06-15 08:45:00,6.48,EVT001,SENSOR03,12.360,-67.900,Site_C
2023-06-15 09:00:00,6.62,EVT001,SENSOR03,12.360,-67.900,Site_C
"""
    
    # Create mock temperature data
    temp_data = """timestamp,value,deployment_event,sensor_id,coordinates,location
2023-06-15 08:30:00,22.3,EVT001,SENSOR01,12.345,-67.890,Site_A
2023-06-15 08:45:00,22.5,EVT001,SENSOR01,12.345,-67.890,Site_A
2023-06-15 09:00:00,22.4,EVT001,SENSOR01,12.345,-67.890,Site_A
2023-06-15 08:30:00,21.8,EVT001,SENSOR02,12.350,-67.895,Site_B
2023-06-15 08:45:00,21.9,EVT001,SENSOR02,12.350,-67.895,Site_B
2023-06-15 09:00:00,22.0,EVT001,SENSOR02,12.350,-67.895,Site_B
2023-06-15 08:30:00,23.1,EVT001,SENSOR03,12.360,-67.900,Site_C
2023-06-15 08:45:00,23.2,EVT001,SENSOR03,12.360,-67.900,Site_C
2023-06-15 09:00:00,23.0,EVT001,SENSOR03,12.360,-67.900,Site_C
"""
    
    (raw_dir / "pH_data.csv").write_text(ph_data)
    (raw_dir / "temperature_data.csv").write_text(temp_data)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_unified_output_columns(mock_data_dir):
    """Test that unified_sample_table.csv has all required columns (T014)."""
    raw_dir = Path(mock_data_dir) / "data" / "raw"
    processed_dir = Path(mock_data_dir) / "data" / "processed"
    
    ph_csv = str(raw_dir / "pH_data.csv")
    temp_csv = str(raw_dir / "temperature_data.csv")
    output_unified = str(processed_dir / "unified_sample_table.csv")
    output_filtered = str(processed_dir / "filtered_unified_sample_table.csv")
    rejected_log = str(processed_dir / "rejected_samples.log")
    
    # Run pipeline
    run_ingestion_pipeline(
        ph_csv_path=ph_csv,
        temp_csv_path=temp_csv,
        output_path=output_unified,
        filtered_output_path=output_filtered,
        rejected_log_path=rejected_log
    )
    
    # Check unified output exists
    assert os.path.exists(output_unified), "unified_sample_table.csv not created"
    
    # Load and check columns
    df = pd.read_csv(output_unified)
    
    required_columns = [
        'sample_id', 'timestamp', 'pH', 'temp', 'pH_sd', 
        'location', 'fastq_path', 'deployment_event', 'sensor_id', 'coordinates'
    ]
    
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Check data types
    assert df['pH'].dtype in ['float64', 'float32'], "pH should be numeric"
    assert df['temp'].dtype in ['float64', 'float32'], "temp should be numeric"
    assert df['pH_sd'].dtype in ['float64', 'float32'], "pH_sd should be numeric"
    
    # Check that we have data
    assert len(df) > 0, "Unified table is empty"

def test_unified_output_before_filtering(mock_data_dir):
    """Test that unified output contains all samples before filtering (T014 vs T013)."""
    raw_dir = Path(mock_data_dir) / "data" / "raw"
    processed_dir = Path(mock_data_dir) / "data" / "processed"
    
    ph_csv = str(raw_dir / "pH_data.csv")
    temp_csv = str(raw_dir / "temperature_data.csv")
    output_unified = str(processed_dir / "unified_sample_table.csv")
    output_filtered = str(processed_dir / "filtered_unified_sample_table.csv")
    rejected_log = str(processed_dir / "rejected_samples.log")
    
    # Run pipeline
    run_ingestion_pipeline(
        ph_csv_path=ph_csv,
        temp_csv_path=temp_csv,
        output_path=output_unified,
        filtered_output_path=output_filtered,
        rejected_log_path=rejected_log
    )
    
    df_unified = pd.read_csv(output_unified)
    df_filtered = pd.read_csv(output_filtered)
    
    # Unified should have all aligned samples
    # Filtered should be a subset (or equal if no outliers)
    assert len(df_unified) >= len(df_filtered), "Filtered table should be subset of unified"

def test_unified_output_file_exists(mock_data_dir):
    """Test that the unified output file is actually written to disk."""
    raw_dir = Path(mock_data_dir) / "data" / "raw"
    processed_dir = Path(mock_data_dir) / "data" / "processed"
    
    ph_csv = str(raw_dir / "pH_data.csv")
    temp_csv = str(raw_dir / "temperature_data.csv")
    output_unified = str(processed_dir / "unified_sample_table.csv")
    output_filtered = str(processed_dir / "filtered_unified_sample_table.csv")
    rejected_log = str(processed_dir / "rejected_samples.log")
    
    # Run pipeline
    run_ingestion_pipeline(
        ph_csv_path=ph_csv,
        temp_csv_path=temp_csv,
        output_path=output_unified,
        filtered_output_path=output_filtered,
        rejected_log_path=rejected_log
    )
    
    # Verify file exists and is not empty
    assert os.path.exists(output_unified), "Output file not created on disk"
    assert os.path.getsize(output_unified) > 0, "Output file is empty"
    
    # Verify it can be read as CSV
    df = pd.read_csv(output_unified)
    assert len(df) > 0, "Output file contains no data"