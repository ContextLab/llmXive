"""
Integration test for T048: Synthetic Data Rejection in align.py
Verifies that the pipeline correctly rejects synthetic data and continues with valid data.
"""
import os
import sys
import pytest
import tempfile
import shutil
import pandas as pd
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.data.align import (
    run_lagged_alignment_pipeline,
    DataIntegrityError,
    _validate_data_integrity
)
from src.utils.logging import get_logger

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_validate_data_integrity_rejects_synthetic():
    """Test that _validate_data_integrity raises DataIntegrityError for synthetic data."""
    # Create a DataFrame with synthetic source_type
    synthetic_df = pd.DataFrame({
        'subject_id': ['S1', 'S2'],
        'block_id': [1, 2],
        'mmn_amplitude': [1.5, 2.0],
        'source_window_start_trial': [10, 20],
        'source_type': ['synthetic', 'real_stream']
    })
    
    # Should raise DataIntegrityError for the synthetic row
    with pytest.raises(DataIntegrityError, match="Synthetic data detected"):
        _validate_data_integrity(synthetic_df, "Test Data")

def test_validate_data_integrity_allows_real():
    """Test that _validate_data_integrity allows real data."""
    # Create a DataFrame with real source_type
    real_df = pd.DataFrame({
        'subject_id': ['S1', 'S2'],
        'block_id': [1, 2],
        'mmn_amplitude': [1.5, 2.0],
        'source_window_start_trial': [10, 20],
        'source_type': ['real_stream', 'verified_source']
    })
    
    # Should not raise an error
    try:
        _validate_data_integrity(real_df, "Test Data")
    except DataIntegrityError:
        pytest.fail("DataIntegrityError raised for valid real data")

def test_validate_data_integrity_missing_column():
    """Test that _validate_data_integrity handles missing source_type column gracefully."""
    # Create a DataFrame without source_type
    df_no_source = pd.DataFrame({
        'subject_id': ['S1', 'S2'],
        'block_id': [1, 2],
        'mmn_amplitude': [1.5, 2.0],
        'source_window_start_trial': [10, 20]
    })
    
    # Should not raise an error (only logs a warning)
    try:
        _validate_data_integrity(df_no_source, "Test Data")
    except DataIntegrityError:
        pytest.fail("DataIntegrityError raised for data without source_type column")

def test_lagged_alignment_rejects_synthetic_mmn(temp_data_dir):
    """Test that run_lagged_alignment_pipeline rejects synthetic MMN data."""
    # Create synthetic MMN data
    mmn_file = os.path.join(temp_data_dir, "mmn_epochs.csv")
    synthetic_mmn = pd.DataFrame({
        'subject_id': ['S1'],
        'block_id': [1],
        'mmn_amplitude': [1.5],
        'source_window_start_trial': [10],
        'source_type': ['synthetic']
    })
    synthetic_mmn.to_csv(mmn_file, index=False)
    
    # Create real accuracy data
    accuracy_file = os.path.join(temp_data_dir, "accuracy_blocks.csv")
    real_accuracy = pd.DataFrame({
        'subject_id': ['S1'],
        'block_id': [1],
        'trial_start': [50],
        'trial_end': [100],
        'accuracy': [0.85]
    })
    real_accuracy.to_csv(accuracy_file, index=False)
    
    output_file = os.path.join(temp_data_dir, "interim_lagged_mmns.csv")
    
    # Should raise DataIntegrityError
    with pytest.raises(DataIntegrityError, match="Synthetic data detected"):
        run_lagged_alignment_pipeline(mmn_file, accuracy_file, output_file)

def test_lagged_alignment_rejects_synthetic_accuracy(temp_data_dir):
    """Test that run_lagged_alignment_pipeline rejects synthetic accuracy data."""
    # Create real MMN data
    mmn_file = os.path.join(temp_data_dir, "mmn_epochs.csv")
    real_mmn = pd.DataFrame({
        'subject_id': ['S1'],
        'block_id': [1],
        'mmn_amplitude': [1.5],
        'source_window_start_trial': [10],
        'source_type': ['real_stream']
    })
    real_mmn.to_csv(mmn_file, index=False)
    
    # Create synthetic accuracy data
    accuracy_file = os.path.join(temp_data_dir, "accuracy_blocks.csv")
    synthetic_accuracy = pd.DataFrame({
        'subject_id': ['S1'],
        'block_id': [1],
        'trial_start': [50],
        'trial_end': [100],
        'accuracy': [0.85],
        'source_type': ['mock']
    })
    synthetic_accuracy.to_csv(accuracy_file, index=False)
    
    output_file = os.path.join(temp_data_dir, "interim_lagged_mmns.csv")
    
    # Should raise DataIntegrityError
    with pytest.raises(DataIntegrityError, match="Synthetic data detected"):
        run_lagged_alignment_pipeline(mmn_file, accuracy_file, output_file)

def test_lagged_alignment_success_with_real_data(temp_data_dir):
    """Test that run_lagged_alignment_pipeline succeeds with real data."""
    # Create real MMN data
    mmn_file = os.path.join(temp_data_dir, "mmn_epochs.csv")
    real_mmn = pd.DataFrame({
        'subject_id': ['S1'],
        'block_id': [1],
        'mmn_amplitude': [1.5],
        'source_window_start_trial': [10],
        'source_type': ['real_stream']
    })
    real_mmn.to_csv(mmn_file, index=False)
    
    # Create real accuracy data
    accuracy_file = os.path.join(temp_data_dir, "accuracy_blocks.csv")
    real_accuracy = pd.DataFrame({
        'subject_id': ['S1'],
        'block_id': [1],
        'trial_start': [50],
        'trial_end': [100],
        'accuracy': [0.85],
        'source_type': ['verified_source']
    })
    real_accuracy.to_csv(accuracy_file, index=False)
    
    output_file = os.path.join(temp_data_dir, "interim_lagged_mmns.csv")
    
    # Should succeed
    try:
        result_df = run_lagged_alignment_pipeline(mmn_file, accuracy_file, output_file)
        assert not result_df.empty
        assert os.path.exists(output_file)
    except DataIntegrityError:
        pytest.fail("DataIntegrityError raised for valid real data")

def test_pipeline_continues_with_valid_data_after_synthetic_skip(temp_data_dir):
    """
    Test that the pipeline can continue with valid data after rejecting synthetic data.
    This simulates a scenario where multiple datasets are processed, and some are synthetic.
    """
    # Create a mix of synthetic and real data files
    mmn_file_1 = os.path.join(temp_data_dir, "mmn_epochs_synthetic.csv")
    synthetic_mmn = pd.DataFrame({
        'subject_id': ['S1'],
        'block_id': [1],
        'mmn_amplitude': [1.5],
        'source_window_start_trial': [10],
        'source_type': ['synthetic']
    })
    synthetic_mmn.to_csv(mmn_file_1, index=False)
    
    mmn_file_2 = os.path.join(temp_data_dir, "mmn_epochs_real.csv")
    real_mmn = pd.DataFrame({
        'subject_id': ['S2'],
        'block_id': [1],
        'mmn_amplitude': [2.0],
        'source_window_start_trial': [20],
        'source_type': ['real_stream']
    })
    real_mmn.to_csv(mmn_file_2, index=False)
    
    accuracy_file = os.path.join(temp_data_dir, "accuracy_blocks.csv")
    real_accuracy = pd.DataFrame({
        'subject_id': ['S2'],
        'block_id': [1],
        'trial_start': [60],
        'trial_end': [110],
        'accuracy': [0.90],
        'source_type': ['verified_source']
    })
    real_accuracy.to_csv(accuracy_file, index=False)
    
    # Process synthetic data (should fail)
    output_file_1 = os.path.join(temp_data_dir, "output_1.csv")
    with pytest.raises(DataIntegrityError):
        run_lagged_alignment_pipeline(mmn_file_1, accuracy_file, output_file_1)
    
    # Process real data (should succeed)
    output_file_2 = os.path.join(temp_data_dir, "output_2.csv")
    try:
        result_df = run_lagged_alignment_pipeline(mmn_file_2, accuracy_file, output_file_2)
        assert not result_df.empty
        assert os.path.exists(output_file_2)
    except DataIntegrityError:
        pytest.fail("Real data processing failed unexpectedly")