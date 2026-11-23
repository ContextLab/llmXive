"""
Integration tests for Task T031: K-fold Cross-Validation.

Verifies that the decoder_cv module correctly loads data, runs 5-fold CV,
calculates chance baselines, and writes valid output.
"""
import pytest
import numpy as np
import json
import os
from pathlib import Path
import tempfile
import h5py
import pandas as pd
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.models.decoder_cv import run_kfold_cross_validation, load_roi_features_and_labels, main
import code.config as config

@pytest.fixture
def mock_data_dir(tmp_path):
    """Create a temporary directory structure with mock data for testing."""
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir(parents=True)
    
    # Create mock events_aligned.csv
    events_data = {
        'subject_id': ['sub-01'] * 20,
        'event_index': list(range(20)),
        'phase': ['early'] * 10 + ['late'] * 10,
        'narrative_label': (['plot'] * 3 + ['character'] * 3 + ['theme'] * 4) * 2
    }
    events_df = pd.DataFrame(events_data)
    events_path = processed_dir / "events_aligned.csv"
    events_df.to_csv(events_path, index=False)
    
    # Create mock roi_timecourses.h5
    h5_path = processed_dir / "roi_timecourses.h5"
    with h5py.File(h5_path, 'w') as f:
        roi_grp = f.create_group("hippocampus")
        phase_grp = roi_grp.create_group("early")
        # Create dummy data: 10 samples, 50 features
        phase_grp.create_dataset("data", data=np.random.randn(10, 50).astype(np.float32))
        # Create dummy labels matching the CSV subset for 'early'
        phase_grp.create_dataset("labels", data=np.array(['plot', 'plot', 'plot', 'character', 'character', 'character', 'theme', 'theme', 'theme', 'theme']))
        
        # Late phase
        phase_grp_late = roi_grp.create_group("late")
        phase_grp_late.create_dataset("data", data=np.random.randn(10, 50).astype(np.float32))
        phase_grp_late.create_dataset("labels", data=np.array(['plot', 'plot', 'plot', 'character', 'character', 'character', 'theme', 'theme', 'theme', 'theme']))
        
    return tmp_path

@pytest.fixture
def mock_config(monkeypatch, tmp_path):
    """Mock config functions to use temporary directory."""
    def mock_get_data_path():
        return tmp_path / "data"
    
    def mock_get_output_path():
        return tmp_path / "results"
        
    # Ensure directories exist
    (tmp_path / "data").mkdir(parents=True)
    (tmp_path / "results").mkdir(parents=True)
    
    monkeypatch.setattr(config, "get_data_path", mock_get_data_path)
    monkeypatch.setattr(config, "get_output_path", mock_get_output_path)
    
    return tmp_path

def test_kfold_accuracy_vs_chance(mock_data_dir, mock_config):
    """
    Test that run_kfold_cross_validation correctly calculates accuracy
    and chance baseline.
    """
    # Load mock data
    X, y = load_roi_features_and_labels("hippocampus", "early")
    
    # Run CV
    mean_acc, std_acc, scores, chance, classes = run_kfold_cross_validation(X, y, n_splits=5)
    
    # Assertions
    assert isinstance(mean_acc, float)
    assert 0.0 <= mean_acc <= 1.0
    assert isinstance(chance, float)
    
    # With 3 classes (plot, character, theme), chance should be 1/3
    assert np.isclose(chance, 1.0/3.0), f"Chance baseline {chance} != 1/3"
    
    # Accuracy should be a valid probability
    assert 0.0 <= mean_acc <= 1.0
    
    # Scores should have 5 elements
    assert len(scores) == 5

def test_main_writes_output(mock_data_dir, mock_config):
    """
    Test that the main() function writes the expected JSON output file.
    """
    # Run main
    main()
    
    output_path = mock_config / "results" / "decoder_cv_metrics.json"
    
    # Check file exists
    assert output_path.exists(), f"Output file {output_path} not created"
    
    # Check content
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert "task_id" in data
    assert data["task_id"] == "T031"
    assert "results" in data
    assert len(data["results"]) > 0
    
    # Check structure of a result entry
    result = data["results"][0]
    assert "roi" in result
    assert "phase" in result
    assert "accuracy" in result
    assert "chance_baseline" in result
    assert "deviation_from_chance" in result

def test_kfold_consistency(mock_data_dir, mock_config):
    """
    Test that running CV twice with the same seed yields same results.
    """
    X, y = load_roi_features_and_labels("hippocampus", "early")
    
    acc1, _, scores1, _, _ = run_kfold_cross_validation(X, y, n_splits=5, random_state=42)
    acc2, _, scores2, _, _ = run_kfold_cross_validation(X, y, n_splits=5, random_state=42)
    
    assert acc1 == acc2
    assert np.allclose(scores1, scores2)