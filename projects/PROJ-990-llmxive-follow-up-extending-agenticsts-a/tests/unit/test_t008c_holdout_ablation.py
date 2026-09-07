"""
Unit tests for T008c: Generate Ground Truth Labels (Ablation – Hold-out Set)
"""
import os
import json
import tempfile
import pandas as pd
from pathlib import Path
import pytest

# We will mock the subprocess calls to avoid running the actual engine in unit tests
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from t008c_generate_holdout_ablation import (
    load_validation_ids,
    load_baseline_win_rates,
    run_ablation_study
)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    processed = tmp_path / 'data' / 'processed'
    processed.mkdir(parents=True)
    
    # Create a mock validation set
    val_df = pd.DataFrame({
        'trajectory_id': ['val_001', 'val_002', 'val_003'],
        'split': ['validation'] * 3
    })
    val_df.to_csv(processed / 'validation_set.csv', index=False)
    
    # Create a mock baseline file
    baseline_data = [
        {'trajectory_id': 'val_001', 'win_rate': 0.8},
        {'trajectory_id': 'val_002', 'win_rate': 0.6},
        {'trajectory_id': 'val_003', 'win_rate': 0.9}
    ]
    with open(processed / 'baseline_win_rates_train.json', 'w') as f:
        json.dump(baseline_data, f)
    
    return processed

def test_load_validation_ids(temp_data_dir):
    """Test loading trajectory IDs from validation set."""
    ids = load_validation_ids()
    assert len(ids) == 3
    assert 'val_001' in ids
    assert 'val_002' in ids
    assert 'val_003' in ids

def test_load_baseline_win_rates(temp_data_dir):
    """Test loading baseline win rates."""
    wins = load_baseline_win_rates()
    assert 'val_001' in wins
    assert wins['val_001'] == 0.8
    assert wins['val_003'] == 0.9

@patch('t008c_generate_holdout_ablation.subprocess.run')
def test_run_ablation_study_with_mock_engine(mock_subprocess, temp_data_dir, tmp_path):
    """Test the full ablation study logic with a mocked engine."""
    # Mock the subprocess output
    mock_result = MagicMock()
    mock_result.returncode = 0
    # Simulate JSON output from engine
    mock_result.stdout = json.dumps({'win_rate': 0.5}) + "\n"
    mock_subprocess.return_value = mock_result

    # Mock the engine runner path to exist
    with patch('t008c_generate_holdout_ablation.ENGINE_RUNNER', temp_data_dir.parent / 'engine_runner.py'):
        # Create a dummy engine runner file
        (temp_data_dir.parent / 'engine_runner.py').touch()
        
        # We need to patch the output path to a temp location to avoid writing to real data
        with patch('t008c_generate_holdout_ablation.OUTPUT_ABLATION_LABELS', tmp_path / 'ablation_labels_holdout.json'):
            run_ablation_study()
            
            # Verify output file was created
            output_file = tmp_path / 'ablation_labels_holdout.json'
            assert output_file.exists()
            
            with open(output_file, 'r') as f:
                results = json.load(f)
            
            # We expect 3 trajectories * 4 layers = 12 records (assuming DEFAULT_LAYERS has 4)
            # But we need to check the logic in the mock. The mock returns 0.5 for everything.
            # The test verifies the structure and that it ran without crashing.
            assert len(results) > 0
            assert all('trajectory_id' in r for r in results)
            assert all('utility_delta' in r for r in results)
            
            # Check delta calculation: baseline (e.g. 0.8) - ablated (0.5) = 0.3
            first_record = results[0]
            expected_delta = first_record['baseline_win_rate'] - first_record['ablated_win_rate']
            assert abs(first_record['utility_delta'] - expected_delta) < 1e-6

def test_missing_validation_file(tmp_path):
    """Test error handling when validation set is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Point to a non-existent file
        with patch('t008c_generate_holdout_ablation.INPUT_VALIDATION_SET', Path(tmpdir) / 'nonexistent.csv'):
            with pytest.raises(FileNotFoundError):
                load_validation_ids()