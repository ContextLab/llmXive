"""
Unit tests for the data splitting functionality in preprocessing.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from code.src.preprocessing import split_data_stratified, save_split_data, process_tumor_type_split

@pytest.fixture
def sample_data():
    """Create a sample dataframe with stratifiable response labels."""
    np.random.seed(42)
    n_samples = 100
    data = {
        'sample_id': [f'S{i}' for i in range(n_samples)],
        'tumor_type': ['BRCA'] * n_samples,
        'response_label': np.random.choice(['Responder', 'NonResponder'], n_samples, p=[0.3, 0.7]),
        'GENE_A': np.random.randn(n_samples),
        'GENE_B': np.random.randn(n_samples),
        'GENE_C': np.random.randn(n_samples)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_split_data_stratified_balanced(sample_data):
    """Test that stratified split maintains class distribution."""
    discovery, training = split_data_stratified(
        sample_data, 
        strata_col='response_label', 
        test_size=0.2, 
        random_state=42
    )
    
    # Check sizes
    assert len(discovery) == 20  # 20% of 100
    assert len(training) == 80
    
    # Check stratification (proportions should be similar)
    disc_prop = discovery['response_label'].value_counts(normalize=True)
    train_prop = training['response_label'].value_counts(normalize=True)
    
    # Allow some tolerance for small sample sizes
    for label in ['Responder', 'NonResponder']:
        assert abs(disc_prop.get(label, 0) - train_prop.get(label, 0)) < 0.1

def test_split_data_stratified_imbalanced(sample_data):
    """Test split with imbalanced classes."""
    # Create highly imbalanced data
    data = sample_data.copy()
    data['response_label'] = ['Responder'] * 5 + ['NonResponder'] * 95
    
    discovery, training = split_data_stratified(
        data, 
        strata_col='response_label', 
        test_size=0.2, 
        random_state=42
    )
    
    # Check sizes
    assert len(discovery) == 20
    assert len(training) == 80
    
    # Check that both classes are present in both splits (if possible)
    assert 'Responder' in discovery['response_label'].values
    assert 'Responder' in training['response_label'].values

def test_split_data_missing_strata_column(sample_data):
    """Test that split fails gracefully with missing stratification column."""
    with pytest.raises(ValueError, match="Stratification column"):
        split_data_stratified(
            sample_data, 
            strata_col='non_existent_column', 
            test_size=0.2
        )

def test_save_split_data(sample_data, temp_output_dir):
    """Test that save_split_data creates files correctly."""
    discovery, training = split_data_stratified(
        sample_data, 
        strata_col='response_label', 
        test_size=0.2
    )
    
    save_split_data(discovery, training, 'BRCA', temp_output_dir)
    
    # Check files exist
    assert (temp_output_dir / 'BRCA_discovery_set.csv').exists()
    assert (temp_output_dir / 'BRCA_training_set.csv').exists()
    
    # Check content
    disc_df = pd.read_csv(temp_output_dir / 'BRCA_discovery_set.csv')
    train_df = pd.read_csv(temp_output_dir / 'BRCA_training_set.csv')
    
    assert len(disc_df) == 20
    assert len(train_df) == 80
    assert 'response_label' in disc_df.columns
    assert 'response_label' in train_df.columns

def test_process_tumor_type_split(sample_data, temp_output_dir):
    """Test the full pipeline for a single tumor type."""
    # Save input file
    input_file = temp_output_dir / 'BRCA_processed.csv'
    sample_data.to_csv(input_file, index=False)
    
    # Process
    tumor_type, n_disc, n_train = process_tumor_type_split(
        input_file, 
        temp_output_dir, 
        discovery_ratio=0.2
    )
    
    # Check results
    assert tumor_type == 'BRCA'
    assert n_disc == 20
    assert n_train == 80
    
    # Check output files
    assert (temp_output_dir / 'BRCA_discovery_set.csv').exists()
    assert (temp_output_dir / 'BRCA_training_set.csv').exists()

def test_split_data_small_classes(sample_data):
    """Test split with very small class sizes (edge case)."""
    # Create data with only 2 responders
    data = sample_data.copy()
    data.loc[:1, 'response_label'] = 'Responder'
    data.loc[2:, 'response_label'] = 'NonResponder'
    
    # Should not raise, but might warn
    discovery, training = split_data_stratified(
        data, 
        strata_col='response_label', 
        test_size=0.2, 
        random_state=42
    )
    
    # Check sizes
    assert len(discovery) == 20
    assert len(training) == 80
    
    # Check that responders are distributed (if possible)
    # With only 2 responders and 80/20 split, it's possible one goes to each
    disc_responders = (discovery['response_label'] == 'Responder').sum()
    train_responders = (training['response_label'] == 'Responder').sum()
    
    assert disc_responders + train_responders == 2