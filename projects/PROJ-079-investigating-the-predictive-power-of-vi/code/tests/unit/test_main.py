import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
from src.main import aggregate_by_strain
from src.config import DATA_PROCESSED_PATH

@pytest.fixture
def sample_merged_df():
    """Create a sample merged dataframe with multiple samples per strain."""
    data = {
        'strain_accession': ['strain_A', 'strain_A', 'strain_B', 'strain_B', 'strain_C'],
        'feature_1': [1.0, 1.0, 2.0, 2.0, 3.0],
        'feature_2': [10.0, 10.0, 20.0, 20.0, 30.0],
        'isg_score': [0.5, 0.7, 1.2, 1.4, 0.9]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_processed_dir():
    """Create a temporary directory for processed data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override the config path for testing
        global DATA_PROCESSED_PATH
        original_path = DATA_PROCESSED_PATH
        DATA_PROCESSED_PATH = tmpdir
        yield tmpdir
        DATA_PROCESSED_PATH = original_path

def test_aggregate_by_strain_basic(sample_merged_df, temp_processed_dir):
    """Test basic aggregation: groups by strain and averages isg_score."""
    result = aggregate_by_strain(sample_merged_df)
    
    # Check number of unique strains
    assert len(result) == 3, "Should have 3 unique strains"
    
    # Check strain_accession values
    assert set(result['strain_accession'].tolist()) == {'strain_A', 'strain_B', 'strain_C'}
    
    # Check aggregated isg_score
    # strain_A: (0.5 + 0.7) / 2 = 0.6
    # strain_B: (1.2 + 1.4) / 2 = 1.3
    # strain_C: 0.9
    assert result.loc[result['strain_accession'] == 'strain_A', 'isg_score'].iloc[0] == pytest.approx(0.6)
    assert result.loc[result['strain_accession'] == 'strain_B', 'isg_score'].iloc[0] == pytest.approx(1.3)
    assert result.loc[result['strain_accession'] == 'strain_C', 'isg_score'].iloc[0] == pytest.approx(0.9)
    
    # Check that feature columns are preserved (first value)
    assert result.loc[result['strain_accession'] == 'strain_A', 'feature_1'].iloc[0] == 1.0
    assert result.loc[result['strain_accession'] == 'strain_B', 'feature_2'].iloc[0] == 20.0

def test_aggregate_by_strain_output_file(sample_merged_df, temp_processed_dir):
    """Test that the function saves the output to the correct file."""
    aggregate_by_strain(sample_merged_df)
    
    output_path = Path(temp_processed_dir) / "aggregated_dataset.csv"
    assert output_path.exists(), "Output file should be created"
    
    saved_df = pd.read_csv(output_path)
    assert len(saved_df) == 3
    assert 'strain_accession' in saved_df.columns
    assert 'isg_score' in saved_df.columns

def test_aggregate_by_strain_missing_columns(sample_merged_df, temp_processed_dir):
    """Test that the function raises KeyError if required columns are missing."""
    df_missing = sample_merged_df.drop(columns=['isg_score'])
    
    with pytest.raises(KeyError, match="isg_score"):
        aggregate_by_strain(df_missing)
    
    df_missing_strain = sample_merged_df.drop(columns=['strain_accession'])
    with pytest.raises(KeyError, match="strain_accession"):
        aggregate_by_strain(df_missing_strain)

def test_aggregate_by_strain_non_numeric_isg(sample_merged_df, temp_processed_dir):
    """Test that the function raises ValueError if isg_score is not numeric."""
    df_non_numeric = sample_merged_df.copy()
    df_non_numeric['isg_score'] = df_non_numeric['isg_score'].astype(str)
    
    with pytest.raises(ValueError, match="isg_score.*not a numeric column"):
        aggregate_by_strain(df_non_numeric)
