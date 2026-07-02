import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

from src.model import split_stratified_strain, validate_strains
from src.config import DATA_PROCESSED_PATH, SEED


@pytest.fixture
def sample_aggregated_df():
    """Create a sample aggregated dataset with enough unique strains."""
    # Create 10 unique strains
    strains = [f"strain_{i}" for i in range(10)]
    data = []
    for strain in strains:
        # Add 2 samples per strain to simulate aggregation
        for j in range(2):
            data.append({
                'strain_accession': strain,
                'feature_1': np.random.rand(),
                'feature_2': np.random.rand(),
                'isg_score': np.random.rand()
            })
    return pd.DataFrame(data)


@pytest.fixture
def temp_processed_dir():
    """Create a temporary directory for processed data."""
    temp_dir = tempfile.mkdtemp()
    # Temporarily override DATA_PROCESSED_PATH
    original_path = DATA_PROCESSED_PATH
    # We need to mock the config or use a path that won't conflict
    # For this test, we'll just ensure the directory exists
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_split_stratified_strain_basic(sample_aggregated_df):
    """Test basic functionality of split_stratified_strain."""
    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as tmpdir:
        # We need to patch the config or modify the function to accept output path
        # For now, we'll test the logic directly without file I/O in this unit test
        # by inspecting the returned dataframes
        
        # Temporarily set DATA_PROCESSED_PATH for the test
        import src.config
        original_path = src.config.DATA_PROCESSED_PATH
        src.config.DATA_PROCESSED_PATH = tmpdir
        
        try:
            train_df, test_df = split_stratified_strain(sample_aggregated_df, test_strains=5)
            
            # Check that we got DataFrames back
            assert isinstance(train_df, pd.DataFrame)
            assert isinstance(test_df, pd.DataFrame)
            
            # Check that test set has exactly 5 unique strains
            assert test_df['strain_accession'].nunique() == 5
            
            # Check that train set has the remaining 5 unique strains
            assert train_df['strain_accession'].nunique() == 5
            
            # Check that there is no overlap
            train_strains = set(train_df['strain_accession'].unique())
            test_strains = set(test_df['strain_accession'].unique())
            assert len(train_strains & test_strains) == 0
            
            # Check that all original strains are accounted for
            original_strains = set(sample_aggregated_df['strain_accession'].unique())
            assert train_strains | test_strains == original_strains
            
        finally:
            # Restore original path
            src.config.DATA_PROCESSED_PATH = original_path


def test_split_stratified_strain_minimum_test_strains(sample_aggregated_df):
    """Test that the function enforces minimum test strains of 5."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import src.config
        original_path = src.config.DATA_PROCESSED_PATH
        src.config.DATA_PROCESSED_PATH = tmpdir
        
        try:
            # Try with test_strains=3 (should fail)
            with pytest.raises(SystemExit):
                split_stratified_strain(sample_aggregated_df, test_strains=3)
        finally:
            src.config.DATA_PROCESSED_PATH = original_path


def test_split_stratified_strain_deterministic(sample_aggregated_df):
    """Test that the split is deterministic with SEED=42."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import src.config
        original_path = src.config.DATA_PROCESSED_PATH
        src.config.DATA_PROCESSED_PATH = tmpdir
        
        try:
            train_df1, test_df1 = split_stratified_strain(sample_aggregated_df, test_strains=5)
            train_df2, test_df2 = split_stratified_strain(sample_aggregated_df, test_strains=5)
            
            # Check that the splits are identical
            assert set(train_df1['strain_accession'].unique()) == set(train_df2['strain_accession'].unique())
            assert set(test_df1['strain_accession'].unique()) == set(test_df2['strain_accession'].unique())
        finally:
            src.config.DATA_PROCESSED_PATH = original_path


def test_validate_strains_pass(sample_aggregated_df):
    """Test that validate_strains passes with sufficient strains."""
    # Should not raise
    validate_strains(sample_aggregated_df)


def test_validate_strains_fail():
    """Test that validate_strains fails with insufficient strains."""
    # Create a dataframe with only 3 strains
    strains = [f"strain_{i}" for i in range(3)]
    data = []
    for strain in strains:
        data.append({
            'strain_accession': strain,
            'feature_1': np.random.rand(),
            'isg_score': np.random.rand()
        })
    df = pd.DataFrame(data)
    
    with pytest.raises(SystemExit):
        validate_strains(df)
