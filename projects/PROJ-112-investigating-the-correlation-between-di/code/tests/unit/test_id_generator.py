"""
Unit tests for the ID Generator module.
"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from src.preprocessing.id_generator import (
    generate_sample_id,
    generate_sample_ids_dataframe,
    run_id_generation,
    get_project_root
)

def test_generate_sample_id_deterministic():
    """Test that the same inputs produce the same ID."""
    cohort = "AGP"
    original_id = "sample_123"
    salt = "llmXive_v1"
    
    id1 = generate_sample_id(cohort, original_id, salt)
    id2 = generate_sample_id(cohort, original_id, salt)
    
    assert id1 == id2
    assert len(id1) == 64  # SHA256 hex length
    assert id1.isalnum()

def test_generate_sample_id_unique():
    """Test that different inputs produce different IDs."""
    cohort = "AGP"
    salt = "llmXive_v1"
    
    id1 = generate_sample_id(cohort, "sample_123", salt)
    id2 = generate_sample_id(cohort, "sample_456", salt)
    id3 = generate_sample_id("UKBB", "sample_123", salt)
    
    assert id1 != id2
    assert id1 != id3
    assert id2 != id3

def test_generate_sample_id_case_insensitive_cohort():
    """Test that cohort case is normalized."""
    id1 = generate_sample_id("agp", "sample_123", "salt")
    id2 = generate_sample_id("AGP", "sample_123", "salt")
    id3 = generate_sample_id("AgP", "sample_123", "salt")
    
    assert id1 == id2
    assert id2 == id3

def test_generate_sample_ids_dataframe():
    """Test ID generation on a DataFrame."""
    data = {
        "cohort_id": ["AGP", "UKBB", "AGP"],
        "original_id": ["A1", "B1", "A2"],
        "value": [10, 20, 30]
    }
    df = pd.DataFrame(data)
    
    result_df = generate_sample_ids_dataframe(df, "cohort_id", "original_id")
    
    assert "sample_id" in result_df.columns
    assert len(result_df) == 3
    assert result_df["sample_id"].iloc[0] != result_df["sample_id"].iloc[1]
    assert result_df["sample_id"].iloc[0] == result_df["sample_id"].iloc[0] # Idempotent check

def test_run_id_generation_file_io():
    """Test the full file I/O pipeline."""
    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.tsv"
        output_path = Path(tmpdir) / "output.tsv"
        
        # Create input data
        data = {
            "cohort_id": ["AGP", "UKBB"],
            "original_id": ["X1", "Y1"],
            "col3": [1, 2]
        }
        df_input = pd.DataFrame(data)
        df_input.to_csv(input_path, sep='\t', index=False)
        
        # Run generation
        run_id_generation(input_path, output_path)
        
        # Verify output exists
        assert output_path.exists()
        
        # Verify content
        df_output = pd.read_csv(output_path, sep='\t')
        assert "sample_id" in df_output.columns
        assert len(df_output) == 2
        assert df_output["sample_id"].iloc[0] != df_output["sample_id"].iloc[1]

def test_run_id_generation_missing_column():
    """Test error handling for missing columns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        data = {"wrong_col": ["A"], "id": ["1"]}
        pd.DataFrame(data).to_csv(input_path, index=False)
        
        with pytest.raises(ValueError):
            run_id_generation(input_path, output_path, cohort_col="wrong_col", id_col="missing")