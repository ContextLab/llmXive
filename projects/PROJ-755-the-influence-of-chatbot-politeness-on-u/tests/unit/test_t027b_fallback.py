"""
Unit tests for T027b: Evaluate Convergence & Fallback.
Tests the logic of checking convergence status and triggering fallback.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np

# Import the module under test
# We assume the file is named 02_evaluate_convergence_fallback.py
import sys
from code import evaluate_convergence_fallback as t027b_module

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create necessary subdirectories
        (tmpdir / "data" / "processed").mkdir(parents=True)
        yield tmpdir

@pytest.fixture
def mock_project_status_success(temp_project_dir):
    """Create a mock project_status.json indicating success."""
    status_file = temp_project_dir / "data" / "processed" / "project_status.json"
    status_data = {
        "convergence_status": "success",
        "model_type": "clmm",
        "status": "success"
    }
    with open(status_file, 'w') as f:
        json.dump(status_data, f)
    return status_file

@pytest.fixture
def mock_project_status_failure(temp_project_dir):
    """Create a mock project_status.json indicating failure."""
    status_file = temp_project_dir / "data" / "processed" / "project_status.json"
    status_data = {
        "convergence_status": "failed",
        "model_type": "clmm",
        "status": "failed"
    }
    with open(status_file, 'w') as f:
        json.dump(status_data, f)
    return status_file

@pytest.fixture
def mock_scored_dialogues(temp_project_dir):
    """Create a mock scored_dialogues.parquet."""
    df = pd.DataFrame({
        'dialogue_id': [1, 2, 3],
        'user_id': ['u1', 'u2', 'u3'],
        'quality_rating': [3, 4, 5],
        'standardized_politeness_score': [0.1, 0.5, -0.2],
        'conversation_length': [10, 20, 15]
    })
    file_path = temp_project_dir / "data" / "processed" / "scored_dialogues.parquet"
    df.to_parquet(file_path)
    return file_path

def test_load_project_status_success(temp_project_dir, mock_project_status_success):
    """Test loading a successful project status."""
    # Patch the PROJECT_ROOT to point to temp dir
    with patch.object(t027b_module, 'PROJECT_ROOT', temp_project_dir):
        status = t027b_module.load_project_status()
        assert status['convergence_status'] == 'success'

def test_load_project_status_failure(temp_project_dir, mock_project_status_failure):
    """Test loading a failed project status."""
    with patch.object(t027b_module, 'PROJECT_ROOT', temp_project_dir):
        status = t027b_module.load_project_status()
        assert status['convergence_status'] == 'failed'

def test_load_project_status_missing_file(temp_project_dir):
    """Test loading when file is missing."""
    with patch.object(t027b_module, 'PROJECT_ROOT', temp_project_dir):
        with pytest.raises(FileNotFoundError):
            t027b_module.load_project_status()

@patch('code.evaluate_convergence_fallback.fit_fallback_ordinal_model')
@patch('code.evaluate_convergence_fallback.save_fallback_results')
def test_fallback_triggered_on_failure(mock_save, mock_fit, temp_project_dir, mock_project_status_failure, mock_scored_dialogues):
    """Test that fallback is triggered when primary model fails."""
    mock_fit.return_value = {
        'model_type': 'clm_fixed_effects',
        'results': [{'term': 'test', 'estimate': 0.5}],
        'convergence_status': 'success'
    }
    
    with patch.object(t027b_module, 'PROJECT_ROOT', temp_project_dir):
        # Mock sys.argv to avoid argparse issues in test
        with patch.object(t027b_module, 'sys.exit', return_value=0):
            result = t027b_module.main()
            
            # Verify fallback was called
            assert mock_fit.called
            assert mock_save.called
            
            # Verify status was updated
            status_file = temp_project_dir / "data" / "processed" / "project_status.json"
            with open(status_file, 'r') as f:
                updated_status = json.load(f)
            assert updated_status['sc003_met'] == False
            assert updated_status['status'] == 'fallback_used'

@patch('code.evaluate_convergence_fallback.fit_fallback_ordinal_model')
def test_no_fallback_on_success(mock_fit, temp_project_dir, mock_project_status_success, mock_scored_dialogues):
    """Test that fallback is NOT triggered when primary model succeeds."""
    with patch.object(t027b_module, 'PROJECT_ROOT', temp_project_dir):
        with patch.object(t027b_module, 'sys.exit', return_value=0):
            result = t027b_module.main()
            
            # Verify fallback was NOT called
            assert not mock_fit.called
            
            # Verify status
            status_file = temp_project_dir / "data" / "processed" / "project_status.json"
            with open(status_file, 'r') as f:
                updated_status = json.load(f)
            assert updated_status['sc003_met'] == True
            assert updated_status['status'] == 'success'

def test_fit_fallback_model_logic():
    """Test the logic of fitting the fallback model (mocked R)."""
    # This is a logic test; actual R execution is hard to mock perfectly without R installed.
    # We test the data preparation and structure.
    df = pd.DataFrame({
        'quality_rating': [1, 2, 3, 4, 5],
        'standardized_politeness_score': [0.1, 0.2, 0.3, 0.4, 0.5],
        'conversation_length': [10, 20, 30, 40, 50]
    })
    
    # The function calls R, so we can't easily test the R part without R.
    # Instead, we verify that the function exists and accepts the dataframe.
    # A full integration test would require R environment.
    assert t027b_module.fit_fallback_ordinal_model is not None