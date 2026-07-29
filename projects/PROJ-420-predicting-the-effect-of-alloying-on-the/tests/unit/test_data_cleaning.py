import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Mock config for testing
class MockConfig:
    def __init__(self, temp_dir):
        self.data_dir = Path(temp_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "processed").mkdir(exist_ok=True)

@pytest.fixture
def mock_config(tmp_path):
    return MockConfig(tmp_path)

@pytest.fixture
def sample_df():
    """Create a sample dataframe with valid composition data."""
    data = {
        'alloy_id': ['A1', 'A2', 'A3'],
        'Poissons_ratio': [0.33, 0.34, 0.32],
        'Youngs_modulus': [70.0, 71.0, 69.0],
        'Cu': [0.05, 0.06, 0.04],
        'Mg': [0.03, 0.04, 0.02],
        'Si': [0.02, 0.03, 0.01],
        'Zn': [0.01, 0.02, 0.005],
        'Mn': [0.005, 0.01, 0.005],
        'Al': [0.885, 0.865, 0.925] # Balance
    }
    return pd.DataFrame(data)

def test_ilr_transformation_basic(sample_df):
    """Test basic ILR transformation on valid data."""
    from data_cleaning import apply_ilr_transformation
    
    # Ensure sum is 1 (compositional data requirement)
    comp_cols = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    current_sum = sample_df[comp_cols].sum(axis=1)
    # The sample data is not perfectly normalized, so we normalize it first
    # to strictly satisfy the ILR requirement of sum=1 for the components being transformed.
    # In real data, this should already be done by T012.
    sample_df_normalized = sample_df.copy()
    sample_df_normalized[comp_cols] = sample_df_normalized[comp_cols].div(
        sample_df_normalized[comp_cols].sum(axis=1), axis=0
    )
    
    result = apply_ilr_transformation(sample_df_normalized)
    
    # Check that new columns were added
    expected_cols = ['ilr_1', 'ilr_2', 'ilr_3', 'ilr_4'] # 5 components -> 4 coordinates
    for col in expected_cols:
        assert col in result.columns, f"Missing column: {col}"
    
    # Check that values are numeric
    for col in expected_cols:
        assert pd.api.types.is_numeric_dtype(result[col]), f"Column {col} is not numeric"

def test_ilr_transformation_zero_handling():
    """Test ILR transformation handles zero values correctly."""
    from data_cleaning import apply_ilr_transformation
    
    data = {
        'Cu': [0.0, 0.05],
        'Mg': [0.05, 0.04],
        'Si': [0.02, 0.03],
        'Zn': [0.01, 0.02],
        'Mn': [0.005, 0.01],
    }
    df = pd.DataFrame(data)
    
    # This should not raise an error but log a warning and replace zeros
    result = apply_ilr_transformation(df)
    
    # Verify columns exist
    assert 'ilr_1' in result.columns

def test_ilr_transformation_missing_columns(sample_df):
    """Test ILR transformation raises error if columns are missing."""
    from data_cleaning import apply_ilr_transformation
    
    # Remove a required column
    df_missing = sample_df.drop(columns=['Cu'])
    
    with pytest.raises(ValueError, match="Missing required composition columns"):
        apply_ilr_transformation(df_missing)

def test_run_ilr_pipeline(mock_config, sample_df):
    """Test the full pipeline including file I/O."""
    from data_cleaning import run_ilr_pipeline
    import pandas as pd
    
    # Create the input file manually
    input_path = mock_config.data_dir / "processed" / "filtered_alloys.csv"
    
    # Normalize composition for the test
    comp_cols = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    sample_df[comp_cols] = sample_df[comp_cols].div(
        sample_df[comp_cols].sum(axis=1), axis=0
    )
    
    sample_df.to_csv(input_path, index=False)
    
    # Mock get_config to return our temp config
    import data_cleaning
    original_get_config = data_cleaning.get_config
    data_cleaning.get_config = lambda: mock_config
    
    try:
        result_df = run_ilr_pipeline()
        
        # Verify output file exists
        output_path = mock_config.data_dir / "processed" / "filtered_alloys_ilr.csv"
        assert output_path.exists(), "Output file was not created"
        
        # Verify content
        loaded_df = pd.read_csv(output_path)
        assert 'ilr_1' in loaded_df.columns
        assert len(loaded_df) == len(sample_df)
    finally:
        data_cleaning.get_config = original_get_config