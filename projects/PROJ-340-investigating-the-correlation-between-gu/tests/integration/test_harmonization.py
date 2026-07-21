"""
Integration tests for the multi-cohort harmonization logic.
"""
import os
import sys
import json
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.harmonize_data import (
    run_harmonization, 
    HarmonizationError, 
    DATA_PROCESSED, 
    DATA_METADATA,
    DATA_RAW
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with sample data files."""
    temp_dir = tempfile.mkdtemp()
    
    # Create raw data subdirectory
    raw_dir = Path(temp_dir) / "data" / "raw"
    raw_dir.mkdir(parents=True)
    
    # Create microbiome data
    micro_data = pd.DataFrame({
        "subject_id": ["S001", "S002", "S003"],
        "age": [25, 30, 45],
        "sex": [0, 1, 0],
        "bmi": [22.5, 24.1, 28.3],
        "bacteroides": [1500, 1450, 1600],
        "firmicutes": [3200, 3100, 3400]
    })
    micro_path = raw_dir / "microbiome.csv"
    micro_data.to_csv(micro_path, index=False)
    
    # Create sleep data
    sleep_data = pd.DataFrame({
        "subject_id": ["S001", "S002", "S003"],
        "age": [25, 30, 45],
        "sex": [0, 1, 0],
        "bmi": [22.5, 24.1, 28.3],
        "sleep_duration": [7.2, 6.8, 6.5],
        "sws_duration": [1.5, 1.3, 1.2]
    })
    sleep_path = raw_dir / "sleep.csv"
    sleep_data.to_csv(sleep_path, index=False)
    
    yield temp_dir, micro_path, sleep_path
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_harmonization_by_id(temp_data_dir):
    """Test harmonization when subject IDs match."""
    temp_dir, micro_path, sleep_path = temp_data_dir
    
    # Temporarily override global paths for testing
    original_raw = DATA_RAW
    original_processed = DATA_PROCESSED
    original_metadata = DATA_METADATA
    
    # We will pass paths explicitly to avoid global state changes
    try:
        df_harm, meta = run_harmonization(
            micro_path=micro_path,
            sleep_path=sleep_path,
            strategy="id"
        )
        
        assert len(df_harm) == 3
        assert "subject_id" in df_harm.columns
        assert "bacteroides" in df_harm.columns
        assert "sleep_duration" in df_harm.columns
        assert meta["strategy_used"] == "id"
        assert meta["final_harmonized_count"] == 3
        
    finally:
        pass # No need to restore global vars as we passed explicit paths

def test_harmonization_no_match():
    """Test harmonization fails when no matches are found."""
    with tempfile.TemporaryDirectory() as temp_dir:
        raw_dir = Path(temp_dir) / "data" / "raw"
        raw_dir.mkdir(parents=True)
        
        # Create non-matching IDs
        micro_data = pd.DataFrame({
            "subject_id": ["A001", "A002"],
            "age": [25, 30],
            "bacteroides": [1500, 1450]
        })
        (raw_dir / "microbiome.csv").to_csv(micro_data, index=False)
        
        sleep_data = pd.DataFrame({
            "subject_id": ["B001", "B002"],
            "age": [25, 30],
            "sleep_duration": [7.2, 6.8]
        })
        (raw_dir / "sleep.csv").to_csv(sleep_data, index=False)
        
        with pytest.raises(HarmonizationError):
            run_harmonization(
                micro_path=raw_dir / "microbiome.csv",
                sleep_path=raw_dir / "sleep.csv",
                strategy="id"
            )

def test_harmonization_metadata_strategy():
    """Test harmonization using metadata matching."""
    with tempfile.TemporaryDirectory() as temp_dir:
        raw_dir = Path(temp_dir) / "data" / "raw"
        raw_dir.mkdir(parents=True)
        
        # Create data with same metadata but different IDs
        micro_data = pd.DataFrame({
            "id": ["X1", "X2"],
            "age": [25, 30],
            "sex": [0, 1],
            "bmi": [22.5, 24.1],
            "bacteroides": [1500, 1450]
        })
        (raw_dir / "microbiome.csv").to_csv(micro_data, index=False)
        
        sleep_data = pd.DataFrame({
            "pid": ["Y1", "Y2"],
            "age": [25, 30],
            "sex": [0, 1],
            "bmi": [22.5, 24.1],
            "sleep_duration": [7.2, 6.8]
        })
        (raw_dir / "sleep.csv").to_csv(sleep_data, index=False)
        
        df_harm, meta = run_harmonization(
            micro_path=raw_dir / "microbiome.csv",
            sleep_path=raw_dir / "sleep.csv",
            strategy="metadata"
        )
        
        assert len(df_harm) == 2
        assert meta["strategy_used"] == "metadata"