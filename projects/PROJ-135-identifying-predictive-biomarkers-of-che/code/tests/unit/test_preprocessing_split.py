"""
Unit tests for the data splitting logic in src/preprocessing.py (T020).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from src.preprocessing import split_data_stratified, process_tumor_type_split, load_processed_data, save_processed_data

@pytest.fixture
def sample_data():
    """Create a sample DataFrame with stratification column."""
    np.random.seed(42)
    n_samples = 100
    data = {
        'gene_A': np.random.randn(n_samples),
        'gene_B': np.random.randn(n_samples),
        'gene_C': np.random.randn(n_samples),
        'response_label': np.random.choice(['Responder', 'NonResponder'], n_samples, p=[0.4, 0.6])
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_split_data_stratified_balanced(sample_data):
    """Test stratified split with balanced-ish classes."""
    discovery, training = split_data_stratified(
        sample_data, 
        strata_column='response_label', 
        test_size=0.3, 
        random_state=42
    )
    
    # Check sizes
    assert len(discovery) + len(training) == len(sample_data)
    assert abs(len(discovery) - len(sample_data) * 0.3) <= 2  # Allow small rounding error
    
    # Check stratification (proportions should be similar)
    disc_prop = discovery['response_label'].value_counts(normalize=True)
    train_prop = training['response_label'].value_counts(normalize=True)
    original_prop = sample_data['response_label'].value_counts(normalize=True)
    
    # Allow some tolerance for small sample sizes
    for label in original_prop.index:
        assert abs(disc_prop.get(label, 0) - original_prop[label]) < 0.1
        assert abs(train_prop.get(label, 0) - original_prop[label]) < 0.1

def test_split_data_stratified_imbalanced():
    """Test stratified split with highly imbalanced classes."""
    n_samples = 200
    data = {
        'gene_A': np.random.randn(n_samples),
        'response_label': ['Responder'] * 20 + ['NonResponder'] * 180  # 10% responders
    }
    df = pd.DataFrame(data)
    
    discovery, training = split_data_stratified(
        df, 
        strata_column='response_label', 
        test_size=0.3, 
        random_state=42
    )
    
    # Check that both sets have responders
    assert discovery['response_label'].sum() > 0
    assert training['response_label'].sum() > 0

def test_split_data_missing_strata_column(sample_data):
    """Test that split fails gracefully if stratification column is missing."""
    with pytest.raises(ValueError, match="Stratification column"):
        split_data_stratified(
            sample_data, 
            strata_column='non_existent_column', 
            test_size=0.3
        )

def test_save_split_data(temp_output_dir, sample_data):
    """Test saving split data to CSV."""
    output_path = os.path.join(temp_output_dir, "test_split.csv")
    save_processed_data(sample_data, output_path)
    
    assert os.path.exists(output_path)
    loaded_df = load_processed_data(output_path)
    assert len(loaded_df) == len(sample_data)
    assert list(loaded_df.columns) == list(sample_data.columns)

def test_process_tumor_type_split(temp_output_dir, sample_data):
    """Test the full process_tumor_type_split function."""
    # Create a mock input file
    input_file = os.path.join(temp_output_dir, "BRCA_batch_corrected.csv")
    save_processed_data(sample_data, input_file)
    
    # Run the split function
    result = process_tumor_type_split(
        tumor_type="BRCA",
        input_path=input_file,
        output_dir=temp_output_dir,
        strata_column='response_label',
        test_size=0.3,
        random_state=42
    )
    
    # Check results
    assert result['tumor_type'] == 'BRCA'
    assert result['total_samples'] == len(sample_data)
    assert os.path.exists(result['discovery_path'])
    assert os.path.exists(result['training_path'])
    
    # Verify files are not empty
    disc_df = load_processed_data(result['discovery_path'])
    train_df = load_processed_data(result['training_path'])
    assert len(disc_df) > 0
    assert len(train_df) > 0

def test_split_data_small_classes():
    """Test that split fails if a class has only 1 sample."""
    n_samples = 10
    data = {
        'gene_A': np.random.randn(n_samples),
        'response_label': ['Responder'] * 1 + ['NonResponder'] * 9  # Only 1 responder
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(RuntimeError, match="Stratified split failed"):
        split_data_stratified(
            df, 
            strata_column='response_label', 
            test_size=0.3
        )