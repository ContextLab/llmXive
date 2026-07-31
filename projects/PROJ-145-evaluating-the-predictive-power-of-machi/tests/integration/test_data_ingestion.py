"""
Integration test for data ingestion pipeline (T012).
Verifies that the script runs and produces the expected output file.
"""
import os
import pandas as pd
import pytest
from pathlib import Path

# Add parent to path for imports if running from tests
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.data_ingestion import process_and_save_heas_train, filter_min_elements
from code.config import DATA_PROCESSED_DIR, ensure_dirs

@pytest.mark.integration
def test_ingestion_creates_file():
    """Test that the ingestion script creates the output CSV file."""
    ensure_dirs()
    output_path = os.path.join(DATA_PROCESSED_DIR, "heas_train.csv")
    
    # Remove existing file if present to ensure fresh run
    if os.path.exists(output_path):
        os.remove(output_path)
    
    # Run the ingestion
    result_path = process_and_save_heas_train(output_path)
    
    # Assert file exists
    assert os.path.exists(result_path), f"Output file {result_path} was not created."
    
    # Assert file is not empty (unless dataset is truly empty, which is unlikely for this dataset)
    df = pd.read_csv(result_path)
    assert len(df) > 0, "Output CSV is empty."
    
    # Assert required columns exist
    required_cols = ["target_energy", "target_hmix", "composition"]
    for col in required_cols:
        assert col in df.columns, f"Column {col} is missing from the output."

@pytest.mark.integration
def test_filter_logic():
    """Test the filter_min_elements function with a mock dataframe."""
    data = {
        "composition": [
            "Fe:0.2,Cr:0.2,Ni:0.2,Mn:0.2,Co:0.2", # 5 elements
            "Fe:0.5,Ni:0.5",                      # 2 elements
            "Al:0.1,Co:0.1,Cr:0.1,Fe:0.1,Ni:0.1,Ti:0.1", # 6 elements
            "Cu:0.5,Zn:0.5"                       # 2 elements
        ]
    }
    df = pd.DataFrame(data)
    
    filtered_df = filter_min_elements(df, min_elements=5)
    
    assert len(filtered_df) == 2, "Filter should return exactly 2 rows."
    assert filtered_df.iloc[0]["composition"] == "Fe:0.2,Cr:0.2,Ni:0.2,Mn:0.2,Co:0.2"
    assert filtered_df.iloc[1]["composition"] == "Al:0.1,Co:0.1,Cr:0.1,Fe:0.1,Ni:0.1,Ti:0.1"
