import os
import sys
import pytest
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.align import (
    bin_behavioral_data,
    check_stationarity,
    calculate_block_accuracy,
    run_behavioral_binning_pipeline
)

def create_mock_epochs_data(subject_id: str, n_blocks: int = 5, trials_per_block: int = 20):
    """Create a mock epochs DataFrame for testing."""
    data = []
    for b in range(n_blocks):
        for t in range(trials_per_block):
            # Vary accuracy slightly to test stationarity
            # Block 0: 0.8, Block 1: 0.82, Block 2: 0.81, etc. (stationary)
            # Or Block 0: 0.5, Block 1: 0.6, Block 2: 0.7 (non-stationary)
            base_acc = 0.8 + (b * 0.01) 
            # Introduce a small random variation
            acc = np.clip(base_acc + np.random.normal(0, 0.02), 0, 1)
            data.append({
                'trial_id': f"{subject_id}_b{b}_t{t}",
                'stimulus_type': 'standard' if t % 2 == 0 else 'deviant',
                'response_correct': 1 if np.random.random() < acc else 0,
                'accuracy': acc,
                'block_id': b
            })
    return pd.DataFrame(data)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    tmpdir = tempfile.mkdtemp()
    data_dir = Path(tmpdir) / "data"
    preprocessed_dir = data_dir / "preprocessed"
    preprocessed_dir.mkdir(parents=True)
    
    # Create mock data for a subject
    subject_id = "sub-test-01"
    df = create_mock_epochs_data(subject_id)
    df.to_csv(preprocessed_dir / f"{subject_id}_epochs.csv", index=False)
    
    yield data_dir
    shutil.rmtree(tmpdir)

@pytest.fixture
def temp_data_dir_non_stationary():
    """Create a temporary directory with non-stationary data."""
    tmpdir = tempfile.mkdtemp()
    data_dir = Path(tmpdir) / "data"
    preprocessed_dir = data_dir / "preprocessed"
    preprocessed_dir.mkdir(parents=True)
    
    subject_id = "sub-test-02"
    # Create data with a strong trend
    data = []
    n_blocks = 10
    for b in range(n_blocks):
        for t in range(20):
            # Strong linear trend: 0.4 to 0.9
            acc = 0.4 + (b * 0.06)
            data.append({
                'trial_id': f"{subject_id}_b{b}_t{t}",
                'stimulus_type': 'standard',
                'response_correct': 1 if np.random.random() < acc else 0,
                'accuracy': acc,
                'block_id': b
            })
    df = pd.DataFrame(data)
    df.to_csv(preprocessed_dir / f"{subject_id}_epochs.csv", index=False)
    
    yield data_dir
    shutil.rmtree(tmpdir)

def test_calculate_block_accuracy():
    """Test accuracy calculation."""
    df = pd.DataFrame({
        'block_id': [1, 1, 2, 2],
        'response_correct': [1, 0, 1, 1]
    })
    acc1 = calculate_block_accuracy(df, 1)
    acc2 = calculate_block_accuracy(df, 2)
    assert abs(acc1 - 0.5) < 1e-6
    assert abs(acc2 - 1.0) < 1e-6

def test_check_stationarity_stable():
    """Test stationarity check on stable data."""
    # Small variations around 0.8
    accs = [0.80, 0.81, 0.79, 0.80, 0.81]
    assert check_stationarity(accs) is True

def test_check_stationarity_trending():
    """Test stationarity check on trending data."""
    # Strong trend from 0.4 to 0.9
    accs = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    assert check_stationarity(accs) is False

def test_bin_behavioral_data_success(temp_data_dir):
    """Test successful binning of behavioral data."""
    output_dir = temp_data_dir / "output"
    result = bin_behavioral_data("sub-test-01", temp_data_dir, output_dir)
    
    assert result is not None
    assert 'subject_id' in result.columns
    assert 'block_id' in result.columns
    assert 'accuracy' in result.columns
    assert 'trial_count' in result.columns
    assert 'is_stationary' in result.columns
    assert len(result) > 0
    
    # Check output file was created
    assert (output_dir / "behavioral_binned_sub-test-01.csv").exists()

def test_bin_behavioral_data_small_blocks(temp_data_dir):
    """Test that blocks with < MIN_BLOCK_SIZE are excluded."""
    # Create data with small blocks
    tmpdir = tempfile.mkdtemp()
    data_dir = Path(tmpdir) / "data"
    preprocessed_dir = data_dir / "preprocessed"
    preprocessed_dir.mkdir(parents=True)
    
    subject_id = "sub-small"
    data = []
    # Block 0: 5 trials (too small)
    for t in range(5):
        data.append({'trial_id': f"{subject_id}_b0_t{t}", 'stimulus_type': 'std', 
                     'response_correct': 1, 'accuracy': 1.0, 'block_id': 0})
    # Block 1: 20 trials (valid)
    for t in range(20):
        data.append({'trial_id': f"{subject_id}_b1_t{t}", 'stimulus_type': 'std', 
                     'response_correct': 1, 'accuracy': 1.0, 'block_id': 1})
    
    pd.DataFrame(data).to_csv(preprocessed_dir / f"{subject_id}_epochs.csv", index=False)
    
    result = bin_behavioral_data(subject_id, data_dir, None)
    
    assert result is not None
    # Only block 1 should be present
    assert len(result) == 1
    assert result.iloc[0]['block_id'] == 1
    
    shutil.rmtree(tmpdir)

def test_bin_behavioral_data_non_stationary(temp_data_dir_non_stationary):
    """Test handling of non-stationary subjects."""
    output_dir = temp_data_dir_non_stationary / "output"
    result = bin_behavioral_data("sub-test-02", temp_data_dir_non_stationary, output_dir)
    
    assert result is not None
    # All blocks should be marked as non-stationary
    assert (result['is_stationary'] == False).all()

def test_run_behavioral_binning_pipeline(temp_data_dir):
    """Test the full pipeline aggregation."""
    output_dir = temp_data_dir / "output"
    # Add another subject
    subject_id2 = "sub-test-03"
    df = create_mock_epochs_data(subject_id2)
    (temp_data_dir / "preprocessed" / f"{subject_id2}_epochs.csv").to_csv(
        temp_data_dir / "preprocessed" / f"{subject_id2}_epochs.csv", index=False
    )
    
    subjects = ["sub-test-01", "sub-test-03"]
    combined = run_behavioral_binning_pipeline(subjects, temp_data_dir, output_dir)
    
    assert combined is not None
    assert len(combined) > 0
    assert 'subject_id' in combined.columns
    # Should have entries for both subjects
    assert len(combined['subject_id'].unique()) == 2