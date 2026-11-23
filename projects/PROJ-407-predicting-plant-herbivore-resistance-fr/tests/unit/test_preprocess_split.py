import os
import json
import tempfile
import pandas as pd
import numpy as np
from preprocess import genotype_stratified_split, save_split_indices, save_split_log

def test_genotype_stratified_split_with_genotype():
    """Test split with genotype_id column present."""
    # Create mock data
    n_samples = 100
    df = pd.DataFrame({
        'genotype_id': np.repeat(['A', 'B', 'C'], n_samples // 3),
        'metabolite_1': np.random.rand(n_samples),
        'resistance': np.random.rand(n_samples)
    })
    
    train_idx, test_idx = genotype_stratified_split(df, test_size=0.2)
    
    # Verify no overlap
    assert len(set(train_idx) & set(test_idx)) == 0
    assert len(train_idx) + len(test_idx) == n_samples
    
    # Verify stratification roughly maintained
    train_genotypes = df.iloc[train_idx]['genotype_id'].value_counts()
    test_genotypes = df.iloc[test_idx]['genotype_id'].value_counts()
    
    # Both should have all genotypes represented
    assert set(train_genotypes.index) == set(test_genotypes.index)

def test_genotype_stratified_split_fallback():
    """Test split falls back to random when no stratification column."""
    df = pd.DataFrame({
        'metabolite_1': np.random.rand(50),
        'resistance': np.random.rand(50)
    })
    
    train_idx, test_idx = genotype_stratified_split(df, test_size=0.2)
    
    assert len(train_idx) + len(test_idx) == 50
    assert len(set(train_idx) & set(test_idx)) == 0

def test_save_split_indices():
    """Test saving split indices to JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, 'split.json')
        train_idx = np.array([0, 1, 2])
        test_idx = np.array([3, 4])
        
        save_split_indices(train_idx, test_idx, filepath)
        
        assert os.path.exists(filepath)
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert data['train_indices'] == [0, 1, 2]
        assert data['test_indices'] == [3, 4]

def test_save_split_log():
    """Test saving split log."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, 'log.txt')
        save_split_log(80, 20, 0.8, 0.2, filepath)
        
        assert os.path.exists(filepath)
        with open(filepath, 'r') as f:
            content = f.read()
        
        assert 'Train Samples: 80' in content
        assert 'Test Samples: 20' in content
        assert 'Split Ratio: 80:20' in content