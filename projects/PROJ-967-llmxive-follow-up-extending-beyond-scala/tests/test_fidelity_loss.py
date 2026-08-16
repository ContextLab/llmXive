import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from code.fidelity_loss import (
    calculate_fidelity_loss,
    load_raw_data,
    save_cleaned_data,
    save_summary,
)


@pytest.fixture
def sample_data():
    """Create a sample dataframe matching the expected schema."""
    data = {
        "prompt": ["prompt1", "prompt2", "prompt3", "prompt4", "prompt5"],
        "image_url": ["url1", "url2", "url3", "url4", "url5"],
        "teacher_scores": [
            {"Alignment": 4.5, "Realism": 3.0, "Aesthetics": 4.0, "Plausibility": 3.5},
            {"Alignment": 5.0, "Realism": 4.5, "Aesthetics": 4.5, "Plausibility": 4.0},
            {"Alignment": 3.0, "Realism": 3.0, "Aesthetics": 3.0, "Plausibility": 3.0},
            {"Alignment": 4.0, "Realism": 4.0, "Aesthetics": 4.0, "Plausibility": 4.0},
            {"Alignment": 5.0, "Realism": 5.0, "Aesthetics": 5.0, "Plausibility": 5.0},
        ],
        "student_scalar": [4.0, 4.8, 2.5, 3.5, 5.2],
        "human_annotations": [
            {"Alignment": 4.2, "Realism": 3.2, "Aesthetics": 4.1, "Plausibility": 3.6},
            {"Alignment": 5.1, "Realism": 4.4, "Aesthetics": 4.6, "Plausibility": 4.1},
            {"Alignment": 2.8, "Realism": 3.1, "Aesthetics": 2.9, "Plausibility": 3.2},
            {"Alignment": 4.0, "Realism": 4.0, "Aesthetics": 4.0, "Plausibility": 4.0},
            {"Alignment": 5.0, "Realism": 5.0, "Aesthetics": 5.0, "Plausibility": 5.0},
        ],
        "primary_dimension": ["Alignment", "Alignment", "Realism", "Aesthetics", "Plausibility"],
        "excluded_reason": [None, None, None, None, None],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_data_with_missing():
    """Create sample data with missing values to test exclusion logic."""
    data = {
        "prompt": ["p1", "p2", "p3", "p4", "p5", "p6"],
        "image_url": ["u1", "u2", "u3", "u4", "u5", "u6"],
        "teacher_scores": [
            {"Alignment": 4.0, "Realism": 3.0, "Aesthetics": 4.0, "Plausibility": 3.5},
            {"Alignment": 5.0, "Realism": 4.5, "Aesthetics": 4.5, "Plausibility": 4.0},
            {"Alignment": 3.0, "Realism": 3.0, "Aesthetics": 3.0, "Plausibility": 3.0},
            {"Alignment": 4.0, "Realism": 4.0, "Aesthetics": 4.0, "Plausibility": 4.0},
            {"Alignment": 5.0, "Realism": 5.0, "Aesthetics": 5.0, "Plausibility": 5.0},
            {"Alignment": 4.0, "Realism": 4.0, "Aesthetics": 4.0, "Plausibility": 4.0},
        ],
        "student_scalar": [4.0, None, 2.5, 3.5, 5.2, 4.0],  # Missing student_scalar at index 1
        "human_annotations": [
            {"Alignment": 4.2, "Realism": 3.2, "Aesthetics": 4.1, "Plausibility": 3.6},
            {"Alignment": 5.1, "Realism": 4.4, "Aesthetics": 4.6, "Plausibility": 4.1},
            {"Alignment": 2.8, "Realism": 3.1, "Aesthetics": 2.9, "Plausibility": 3.2},
            None,  # Missing human_annotations at index 3
            {"Alignment": 5.0, "Realism": 5.0, "Aesthetics": 5.0, "Plausibility": 5.0},
            {"Alignment": 4.0, "Realism": 4.0, "Aesthetics": 4.0, "Plausibility": 4.0},
        ],
        "primary_dimension": ["Alignment", "Alignment", "Realism", "Aesthetics", "Plausibility", "InvalidDim"],
        "excluded_reason": [None, None, None, None, None, None],
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    import logging
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    return logger


def test_calculate_fidelity_loss_valid(sample_data, mock_logger):
    """Test fidelity loss calculation on valid data."""
    df, excluded = calculate_fidelity_loss(sample_data, mock_logger)
    
    # Check that fidelity_loss column exists
    assert 'fidelity_loss' in df.columns
    
    # Check that no samples were excluded
    assert len(excluded) == 0
    
    # Check calculated values (MAE = |student - human|)
    # Index 0: |4.0 - 4.2| = 0.2
    assert abs(df.iloc[0]['fidelity_loss'] - 0.2) < 1e-6
    # Index 1: |4.8 - 5.1| = 0.3
    assert abs(df.iloc[1]['fidelity_loss'] - 0.3) < 1e-6
    # Index 2: |2.5 - 2.8| = 0.3 (Realism dimension)
    assert abs(df.iloc[2]['fidelity_loss'] - 0.3) < 1e-6


def test_calculate_fidelity_loss_missing_values(sample_data_with_missing, mock_logger):
    """Test fidelity loss calculation with missing values."""
    df, excluded = calculate_fidelity_loss(sample_data_with_missing, mock_logger)
    
    # Check that fidelity_loss column exists
    assert 'fidelity_loss' in df.columns
    
    # Check exclusion counts
    assert len(excluded) == 3  # Missing student_scalar, missing human_annotations, invalid dimension
    
    # Check exclusion reasons
    reasons = [exc['reason'] for exc in excluded]
    assert 'missing_student_scalar' in reasons
    assert 'missing_human_annotations' in reasons
    assert 'invalid_primary_dimension' in reasons
    
    # Check that valid samples have fidelity_loss
    valid_indices = [0, 4, 5]  # These should be valid
    for idx in valid_indices:
        assert pd.notna(df.iloc[idx]['fidelity_loss'])


def test_save_cleaned_data(sample_data, mock_logger):
    """Test saving cleaned data to parquet."""
    df, _ = calculate_fidelity_loss(sample_data, mock_logger)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_cleaned.parquet"
        save_cleaned_data(df, output_path, mock_logger)
        
        assert output_path.exists()
        
        # Verify we can load it back
        loaded_df = pd.read_parquet(output_path)
        assert len(loaded_df) == len(df)
        assert 'fidelity_loss' in loaded_df.columns


def test_save_summary(sample_data, mock_logger):
    """Test saving summary statistics."""
    df, excluded = calculate_fidelity_loss(sample_data, mock_logger)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        summary_path = Path(tmpdir) / "test_summary.json"
        save_summary(excluded, df, summary_path, mock_logger)
        
        assert summary_path.exists()
        
        with open(summary_path, 'r') as f:
            summary = json.load(f)
        
        assert 'mean' in summary
        assert 'median' in summary
        assert 'count' in summary
        assert 'excluded_count' in summary
        assert summary['count'] == 5
        assert summary['excluded_count'] == 0


def test_load_raw_data_missing_file(mock_logger):
    """Test loading data from a non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_raw_data(mock_logger, Path("non_existent_file.parquet"))


def test_load_raw_data_missing_columns(mock_logger):
    """Test loading data with missing required columns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a parquet with missing columns
        df = pd.DataFrame({"only_one_column": [1, 2, 3]})
        temp_path = Path(tmpdir) / "bad_data.parquet"
        df.to_parquet(temp_path)
        
        with pytest.raises(ValueError) as exc_info:
            load_raw_data(mock_logger, temp_path)
        
        assert "Missing required columns" in str(exc_info.value)
