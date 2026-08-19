import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import json

from src.preprocessing import (
    load_batch_corrected_data,
    split_data_stratified,
    save_split_data,
    process_tumor_type_split,
    get_tumor_types_from_batch_corrected
)

@pytest.fixture
def sample_data():
    """Create sample batch-corrected data with response labels."""
    np.random.seed(42)
    n_samples = 100
    n_genes = 50
    
    data = {
        'sample_id': [f'SAMPLE_{i:03d}' for i in range(n_samples)],
        'response_label': np.random.choice(['Responder', 'Non-Responder'], n_samples),
    }
    
    # Add gene expression columns
    for i in range(n_genes):
        data[f'GENE_{i}'] = np.random.randn(n_samples)
    
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_split_data_stratified_balanced(sample_data):
    """Test stratified split with balanced classes."""
    # Ensure balanced classes
    sample_data['response_label'] = ['Responder'] * 50 + ['Non-Responder'] * 50
    
    discovery, training = split_data_stratified(sample_data, test_size=0.3, random_state=42)
    
    # Check sizes
    assert len(discovery) + len(training) == len(sample_data)
    assert abs(len(discovery) / len(sample_data) - 0.3) < 0.05  # ~30% discovery
    
    # Check stratification is approximately maintained
    discovery_dist = discovery['response_label'].value_counts()
    training_dist = training['response_label'].value_counts()
    
    # Both splits should have both classes
    assert 'Responder' in discovery_dist.index
    assert 'Non-Responder' in discovery_dist.index
    assert 'Responder' in training_dist.index
    assert 'Non-Responder' in training_dist.index

def test_split_data_stratified_imbalanced(sample_data):
    """Test stratified split with imbalanced classes."""
    # Create imbalanced classes (80/20 split)
    sample_data['response_label'] = (
        ['Responder'] * 80 + ['Non-Responder'] * 20
    )
    
    discovery, training = split_data_stratified(sample_data, test_size=0.3, random_state=42)
    
    # Check sizes
    assert len(discovery) + len(training) == len(sample_data)
    
    # Check that both classes are present in both splits
    assert len(discovery[discovery['response_label'] == 'Non-Responder']) > 0
    assert len(training[training['response_label'] == 'Non-Responder']) > 0

def test_split_data_missing_strata_column(sample_data):
    """Test that split fails gracefully when response_label is missing."""
    df_no_label = sample_data.drop(columns=['response_label'])
    
    with pytest.raises(ValueError, match="response_label"):
        split_data_stratified(df_no_label, test_size=0.3)

def test_save_split_data(sample_data, temp_output_dir):
    """Test saving split data to CSV files."""
    discovery, training = split_data_stratified(sample_data, test_size=0.3)
    
    discovery_path, training_path = save_split_data(
        discovery, training, "TEST", temp_output_dir
    )
    
    # Check files exist
    assert discovery_path.exists()
    assert training_path.exists()
    
    # Check content can be loaded
    loaded_discovery = pd.read_csv(discovery_path)
    loaded_training = pd.read_csv(training_path)
    
    assert len(loaded_discovery) == len(discovery)
    assert len(loaded_training) == len(training)

def test_process_tumor_type_split(temp_output_dir):
    """Test end-to-end processing of a single tumor type."""
    # Create a mock batch-corrected file
    batch_corrected_path = temp_output_dir / "BRCA_batch_corrected.csv"
    sample_data = pd.DataFrame({
        'sample_id': [f'S{i}' for i in range(50)],
        'response_label': ['Responder'] * 25 + ['Non-Responder'] * 25,
        'GENE_1': np.random.randn(50)
    })
    sample_data.to_csv(batch_corrected_path, index=False)
    
    # Process
    result = process_tumor_type_split("BRCA", temp_output_dir, test_size=0.3)
    
    # Check result
    assert result['status'] == 'success'
    assert result['tumor_type'] == 'BRCA'
    assert result['total_samples'] == 50
    assert result['discovery_samples'] + result['training_samples'] == 50
    
    # Check output files exist
    discovery_path = temp_output_dir / "BRCA_discovery_set.csv"
    training_path = temp_output_dir / "BRCA_training_set.csv"
    assert discovery_path.exists()
    assert training_path.exists()

def test_split_data_small_classes(temp_output_dir):
    """Test handling of very small classes."""
    # Create data with a class that has only 2 samples
    sample_data = pd.DataFrame({
        'sample_id': [f'S{i}' for i in range(20)],
        'response_label': ['Responder'] * 18 + ['Non-Responder'] * 2,
        'GENE_1': np.random.randn(20)
    })
    
    # This should still work with stratified split
    discovery, training = split_data_stratified(sample_data, test_size=0.3, random_state=42)
    
    # Both splits should have at least one Non-Responder
    assert len(discovery[discovery['response_label'] == 'Non-Responder']) >= 1
    assert len(training[training['response_label'] == 'Non-Responder']) >= 1

def test_get_tumor_types_from_batch_corrected(temp_output_dir):
    """Test scanning for batch-corrected files."""
    # Create some mock batch-corrected files
    (temp_output_dir / "BRCA_batch_corrected.csv").touch()
    (temp_output_dir / "LUAD_batch_corrected.csv").touch()
    (temp_output_dir / "other_file.csv").touch()  # Should be ignored
    
    types = get_tumor_types_from_batch_corrected(temp_output_dir)
    
    assert "BRCA" in types
    assert "LUAD" in types
    assert "other_file" not in types
    assert len(types) == 2

def test_load_batch_corrected_data_missing_file(temp_output_dir):
    """Test that loading a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="not found"):
        load_batch_corrected_data("BRCA", temp_output_dir)

def test_load_batch_corrected_data_missing_columns(temp_output_dir):
    """Test that loading a file without required columns raises ValueError."""
    bad_file = temp_output_dir / "BRCA_batch_corrected.csv"
    bad_data = pd.DataFrame({
        'sample_id': ['S1', 'S2'],
        'gene_1': [1.0, 2.0]
        # Missing 'response_label'
    })
    bad_data.to_csv(bad_file, index=False)
    
    with pytest.raises(ValueError, match="response_label"):
        load_batch_corrected_data("BRCA", temp_output_dir)
