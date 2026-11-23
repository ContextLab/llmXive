import os
import json
import pytest
import pandas as pd
import numpy as np
from preprocess import genotype_stratified_split, save_split_indices, save_split_log

@pytest.fixture
def harmonized_dataset_path(tmp_path):
    """Create a temporary harmonized dataset file."""
    interim_dir = tmp_path / "interim"
    interim_dir.mkdir()
    
    # Create a realistic dataset with multiple genotypes
    np.random.seed(42)
    n_samples = 200
    n_genotypes = 20
    
    genotype_ids = [f"GEN_{i}" for i in range(n_genotypes)]
    df_genotypes = [genotype_ids[i % n_genotypes] for i in range(n_samples)]
    
    df = pd.DataFrame({
        'sample_id': range(n_samples),
        'genotype_id': df_genotypes,
        'resistance': np.random.rand(n_samples) * 10,
        'metabolite_1': np.random.rand(n_samples),
        'metabolite_2': np.random.rand(n_samples),
        'metabolite_3': np.random.rand(n_samples)
    })
    
    csv_path = interim_dir / "harmonized.csv"
    df.to_csv(csv_path, index=False)
    
    return str(csv_path)

def test_genotype_split_integration(harmonized_dataset_path, tmp_path):
    """Integration test for genotype-stratified split."""
    # Load the dataset
    df = pd.read_csv(harmonized_dataset_path)
    
    # Perform split
    train_indices, test_indices = genotype_stratified_split(df)
    
    # Verify no leakage
    train_genotypes = set(df.iloc[train_indices]['genotype_id'])
    test_genotypes = set(df.iloc[test_indices]['genotype_id'])
    overlap = train_genotypes.intersection(test_genotypes)
    
    assert len(overlap) == 0, f"Genotype leakage detected: {overlap}"
    
    # Verify coverage
    all_indices = set(range(len(df)))
    assert set(train_indices).union(set(test_indices)) == all_indices
    assert set(train_indices).intersection(set(test_indices)) == set()
    
    # Verify split ratios (approximately 80/20)
    train_ratio = len(train_indices) / len(df)
    test_ratio = len(test_indices) / len(df)
    
    assert 0.75 <= train_ratio <= 0.85, f"Train ratio {train_ratio} outside expected range"
    assert 0.15 <= test_ratio <= 0.25, f"Test ratio {test_ratio} outside expected range"
    
    # Save and verify outputs
    output_dir = tmp_path / "interim"
    output_dir.mkdir()
    
    save_split_indices(train_indices, test_indices, filepath=str(output_dir / "split_indices.json"))
    save_split_log(train_indices, test_indices, filepath=str(output_dir / "split_log.txt"))
    
    # Verify files exist
    assert (output_dir / "split_indices.json").exists()
    assert (output_dir / "split_log.txt").exists()
    
    # Verify JSON content
    with open(output_dir / "split_indices.json", 'r') as f:
        split_data = json.load(f)
    
    assert len(split_data['train_indices']) == len(train_indices)
    assert len(split_data['test_indices']) == len(test_indices)
    
    # Verify log content
    with open(output_dir / "split_log.txt", 'r') as f:
        log_content = f.read()
    
    assert "Total samples" in log_content
    assert "Train samples" in log_content
    assert "Test samples" in log_content
    assert str(len(df)) in log_content  # Total samples count