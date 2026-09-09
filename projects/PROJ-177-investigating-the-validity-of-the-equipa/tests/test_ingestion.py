"""
Tests for the ingestion module, specifically for driving log ingestion.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingestion import ingest_driving_logs, DataIngestionError


@pytest.fixture
def temp_input_dir(tmp_path):
    """Create a temporary directory with sample driving log data."""
    input_dir = tmp_path / "data" / "raw"
    input_dir.mkdir(parents=True)
    
    # Create a sample CSV driving log
    data = {
        'timestamp': pd.date_range(start='2023-01-01', periods=10, freq='1s'),
        'frequency': [10.0, 10.5, 10.2, 10.8, 11.0, np.nan, 11.2, 11.5, 11.3, 11.0],
        'amplitude': [1.0, 1.1, 1.05, 1.2, 1.15, 1.1, 1.25, 1.3, 1.2, 1.1]
    }
    df = pd.DataFrame(data)
    csv_path = input_dir / "driving_signal_log.csv"
    df.to_csv(csv_path, index=False)
    
    return input_dir


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "data" / "derived"
    output_dir.mkdir(parents=True)
    return output_dir


def test_ingest_driving_logs(temp_input_dir, temp_output_dir):
    """Test that driving logs are correctly ingested and written to output."""
    output_path = temp_output_dir / "driving_signals.csv"
    
    result_df = ingest_driving_logs(
        input_dir=str(temp_input_dir),
        output_path=str(output_path)
    )
    
    # Check that output file exists
    assert output_path.exists(), "Output file was not created."
    
    # Check that the result dataframe has the expected columns
    assert 'timestamp' in result_df.columns
    assert 'frequency' in result_df.columns
    assert 'amplitude' in result_df.columns
    
    # Check that interpolation worked (NaN in frequency should be filled)
    assert not result_df['frequency'].isna().any(), "Interpolation failed to fill missing values."
    
    # Check that the number of rows is preserved (or adjusted if filtering happened)
    assert len(result_df) == 10, "Row count mismatch after ingestion."


def test_ingest_driving_logs_missing_file(tmp_path):
    """Test that an error is raised if input directory is missing."""
    input_dir = tmp_path / "non_existent_dir"
    output_path = tmp_path / "output.csv"
    
    with pytest.raises(FileNotFoundError):
        ingest_driving_logs(
            input_dir=str(input_dir),
            output_path=str(output_path)
        )


def test_ingest_driving_logs_no_valid_files(tmp_path):
    """Test that an error is raised if no valid driving signal files are found."""
    input_dir = tmp_path / "data" / "raw"
    input_dir.mkdir(parents=True)
    
    # Create a file that doesn't match naming conventions or is empty
    empty_file = input_dir / "random_file.txt"
    empty_file.write_text("This is not a driving log.")
    
    output_path = tmp_path / "output.csv"
    
    with pytest.raises(FileNotFoundError):
        ingest_driving_logs(
            input_dir=str(input_dir),
            output_path=str(output_path)
        )


def test_ingest_driving_logs_json_input(tmp_path):
    """Test ingestion of JSON formatted driving logs."""
    input_dir = tmp_path / "data" / "raw"
    input_dir.mkdir(parents=True)
    
    data = {
        'time': [0, 1, 2, 3, 4],
        'freq': [10.0, 10.5, 10.2, 10.8, 11.0]
    }
    df = pd.DataFrame(data)
    json_path = input_dir / "drive_data.json"
    df.to_json(json_path, orient='records')
    
    output_path = tmp_path / "output.csv"
    
    result_df = ingest_driving_logs(
        input_dir=str(input_dir),
        output_path=str(output_path)
    )
    
    assert result_df is not None
    assert 'freq' in result_df.columns or 'frequency' in result_df.columns
    assert len(result_df) == 5