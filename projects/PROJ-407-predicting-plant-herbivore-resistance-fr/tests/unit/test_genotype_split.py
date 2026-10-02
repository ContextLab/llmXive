import os
import json
import pytest
import pandas as pd
import numpy as np
from preprocess import genotype_stratified_split, save_split_indices, save_split_log, load_interim_dataset

@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe with genotype_id for testing."""
    np.random.seed(42)
    n_samples = 100
    n_genotypes = 10
    
    # Create genotype IDs (10 genotypes, 10 samples each)
    genotype_ids = [f"GEN_{i}" for i in range(n_genotypes)]
    df_genotypes = [genotype_ids[i % n_genotypes] for i in range(n_samples)]
    
    # Create sample data
    df = pd.DataFrame({
        'sample_id': range(n_samples),
        'genotype_id': df_genotypes,
        'resistance': np.random.rand(n_samples) * 10,
        'metabolite_1': np.random.rand(n_samples),
        'metabolite_2': np.random.rand(n_samples)
    })
    
    return df

@pytest.fixture
def temp_interim_dir(tmp_path):
    """Create a temporary interim directory."""
    interim_dir = tmp_path / "interim"
    interim_dir.mkdir()
    return interim_dir

def test_genotype_stratified_split_no_leakage(sample_dataframe):
    """Test that genotype-stratified split prevents genotype leakage."""
    train_indices, test_indices = genotype_stratified_split(sample_dataframe)
    
    train_genotypes = set(sample_dataframe.iloc[train_indices]['genotype_id'])
    test_genotypes = set(sample_dataframe.iloc[test_indices]['genotype_id'])
    
    # Ensure no genotype appears in both train and test sets
    overlap = train_genotypes.intersection(test_genotypes)
    assert len(overlap) == 0, f"Genotype leakage detected: {overlap}"

def test_genotype_stratified_split_coverage(sample_dataframe):
    """Test that all samples are assigned to either train or test."""
    train_indices, test_indices = genotype_stratified_split(sample_dataframe)
    
    all_indices = set(range(len(sample_dataframe)))
    train_set = set(train_indices)
    test_set = set(test_indices)
    
    # Check that all samples are in either train or test
    assert train_set.union(test_set) == all_indices
    # Check that there is no overlap
    assert train_set.intersection(test_set) == set()

def test_save_split_indices(tmp_path, sample_dataframe):
    """Test saving split indices to JSON."""
    train_indices, test_indices = genotype_stratified_split(sample_dataframe)
    
    output_file = tmp_path / "split_indices.json"
    save_split_indices(train_indices, test_indices, filepath=str(output_file))
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert 'train_indices' in data
    assert 'test_indices' in data
    assert len(data['train_indices']) == len(train_indices)
    assert len(data['test_indices']) == len(test_indices)

def test_save_split_log(tmp_path, sample_dataframe):
    """Test saving split log to text file."""
    train_indices, test_indices = genotype_stratified_split(sample_dataframe)
    
    output_file = tmp_path / "split_log.txt"
    save_split_log(train_indices, test_indices, filepath=str(output_file))
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        content = f.read()
    
    assert "Total samples" in content
    assert "Train samples" in content
    assert "Test samples" in content
    assert "Train ratio" in content
    assert "Test ratio" in content

def test_genotype_stratified_split_missing_column():
    """Test that an error is raised if genotype_id column is missing."""
    df = pd.DataFrame({
        'sample_id': [0, 1, 2],
        'resistance': [1, 2, 3]
    })
    
    with pytest.raises(ValueError, match="Column 'genotype_id' not found"):
        genotype_stratified_split(df)
