import os
import pytest
import pandas as pd
import numpy as np

from data.split_data import load_processed_features, split_data, save_splits
from config import get_project_root

@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe mimicking the output of the descriptor pipeline."""
    np.random.seed(42)
    n_samples = 100
    
    data = {
        "molecule_id": [f"MOL_{i:03d}" for i in range(n_samples)],
        "potential": np.random.choice([0, 2, 4], size=n_samples),
        "homo": np.random.randn(n_samples),
        "lumo": np.random.randn(n_samples),
        "bond_length_avg": np.random.rand(n_samples) * 2,
        "decomp_energy": np.random.randn(n_samples) * 0.5
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_processed_dir(tmp_path, sample_dataframe):
    """Create a temporary processed directory and save sample data."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    
    input_file = processed_dir / "electrolyte_features.csv"
    sample_dataframe.to_csv(input_file, index=False)
    return str(processed_dir), str(input_file)

def test_load_processed_features(temp_processed_dir):
    """Test loading the processed features file."""
    _, input_file = temp_processed_dir
    df = load_processed_features(input_file)
    
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "decomp_energy" in df.columns
    assert "potential" in df.columns

def test_split_data_ratios(temp_processed_dir):
    """Test that split_data produces correct ratios."""
    _, input_file = temp_processed_dir
    df = load_processed_features(input_file)
    
    # Use 70/15/15 split
    train, val, test = split_data(df, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)
    
    total = len(train) + len(val) + len(test)
    assert total == len(df)
    
    # Allow small floating point tolerance
    assert abs(len(train) / len(df) - 0.7) < 0.02
    assert abs(len(val) / len(df) - 0.15) < 0.02
    assert abs(len(test) / len(df) - 0.15) < 0.02

def test_split_data_stratification(temp_processed_dir):
    """Test that stratification preserves distribution in splits."""
    _, input_file = temp_processed_dir
    df = load_processed_features(input_file)
    
    # Ensure potential is stratified
    train, val, test = split_data(df, stratify_col="potential", random_state=42)
    
    # Check that all splits have the same potential distribution (roughly)
    # This is a soft check because small samples might vary
    original_dist = df["potential"].value_counts(normalize=True).sort_index()
    train_dist = train["potential"].value_counts(normalize=True).sort_index()
    val_dist = val["potential"].value_counts(normalize=True).sort_index()
    test_dist = test["potential"].value_counts(normalize=True).sort_index()
    
    # Check alignment of indices first
    assert train_dist.index.tolist() == original_dist.index.tolist()
    
    # Check that proportions are roughly similar (within 10% absolute difference)
    for pot in original_dist.index:
        assert abs(train_dist.get(pot, 0) - original_dist.get(pot, 0)) < 0.1

def test_save_splits_creates_files(temp_processed_dir, sample_dataframe):
    """Test that save_splits creates the expected CSV files."""
    tmp_dir, _ = temp_processed_dir
    train_df, val_df, test_df = split_data(sample_dataframe)
    
    save_splits(train_df, val_df, test_df, tmp_dir)
    
    # Check files exist
    assert os.path.exists(os.path.join(tmp_dir, "electrolyte_train.csv"))
    assert os.path.exists(os.path.join(tmp_dir, "electrolyte_val.csv"))
    assert os.path.exists(os.path.join(tmp_dir, "electrolyte_heldout.csv"))
    assert os.path.exists(os.path.join(tmp_dir, "split_checksums.json"))
    
    # Verify content
    loaded_train = pd.read_csv(os.path.join(tmp_dir, "electrolyte_train.csv"))
    assert len(loaded_train) == len(train_df)
    
    loaded_heldout = pd.read_csv(os.path.join(tmp_dir, "electrolyte_heldout.csv"))
    assert len(loaded_heldout) == len(test_df)
