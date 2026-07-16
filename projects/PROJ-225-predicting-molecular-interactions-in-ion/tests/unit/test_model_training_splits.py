import pytest
import pandas as pd
import os
import shutil
from code.model_training import save_splits, stratified_split

@pytest.fixture
def sample_df():
    """Create a sample dataframe with structural families."""
    data = {
        'cation_id': ['cat1'] * 100 + ['cat2'] * 100,
        'anion_id': ['an1'] * 50 + ['an2'] * 50 + ['an3'] * 50 + ['an4'] * 50,
        'total_energy': [1.0] * 100 + [2.0] * 100,
        'structural_family': ['family_A'] * 60 + ['family_B'] * 40 + ['family_A'] * 40 + ['family_B'] * 60
    }
    return pd.DataFrame(data)

@pytest.fixture
def clean_processed_dir():
    """Ensure data/processed is clean for testing."""
    dir_path = "data/processed"
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path, exist_ok=True)
    yield
    # Cleanup after test
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

def test_save_splits_creates_files(sample_df, clean_processed_dir):
    """Test that save_splits creates the three parquet files."""
    # Perform a split first
    train_df, val_df, test_df = stratified_split(
        sample_df, 
        target_col='total_energy', 
        structural_family_col='structural_family'
    )
    
    # Save splits
    paths = save_splits(train_df, val_df, test_df)
    
    # Verify files exist
    assert os.path.exists(paths['train'])
    assert os.path.exists(paths['val'])
    assert os.path.exists(paths['test'])
    
    # Verify row counts match
    loaded_train = pd.read_parquet(paths['train'])
    loaded_val = pd.read_parquet(paths['val'])
    loaded_test = pd.read_parquet(paths['test'])
    
    assert len(loaded_train) == len(train_df)
    assert len(loaded_val) == len(val_df)
    assert len(loaded_test) == len(test_df)
    
    # Verify columns are preserved
    assert list(loaded_train.columns) == list(sample_df.columns)
    assert list(loaded_val.columns) == list(sample_df.columns)
    assert list(loaded_test.columns) == list(sample_df.columns)

def test_save_splits_handles_empty_df(clean_processed_dir):
    """Test behavior with empty dataframes."""
    empty_df = pd.DataFrame(columns=['cation_id', 'anion_id', 'total_energy', 'structural_family'])
    
    train_df, val_df, test_df = stratified_split(
        empty_df,
        target_col='total_energy',
        structural_family_col='structural_family'
    )
    
    paths = save_splits(train_df, val_df, test_df)
    
    assert os.path.exists(paths['train'])
    assert os.path.exists(paths['val'])
    assert os.path.exists(paths['test'])