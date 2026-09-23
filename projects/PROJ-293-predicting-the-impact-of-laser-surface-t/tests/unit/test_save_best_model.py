import os
import sys
import json
import tempfile
import shutil
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import joblib

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from train import save_best_model, TrainingResult

@pytest.fixture
def temp_dirs():
    """Create temporary directories for model and reports."""
    temp_dir = tempfile.mkdtemp()
    model_dir = Path(temp_dir) / 'models'
    report_dir = Path(temp_dir) / 'reports'
    model_dir.mkdir()
    report_dir.mkdir()
    yield str(model_dir), str(report_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_model():
    """Create a mock sklearn pipeline."""
    mock_pipe = MagicMock()
    mock_pipe.named_steps = {'model': MagicMock()}
    mock_pipe.named_steps['model'].feature_importances_ = np.array([0.1, 0.2])
    return mock_pipe

def test_save_best_model_saves_files(temp_dirs, mock_model):
    """Test that save_best_model creates the model and report files."""
    model_path, report_path = temp_dirs
    output_model = os.path.join(model_path, 'test_model.joblib')
    output_report = os.path.join(report_path, 'test_report.json')

    best_result = TrainingResult(
        model_name='TestModel',
        r2=0.85,
        mae=0.12,
        rmse=0.15,
        params={'n_estimators': 100},
        feature_importance={'feature1': 0.5}
    )

    performance_metrics = {
        'best_model': 'TestModel',
        'metrics': {'r2': 0.85},
        'lomo_validation': {'mean_r2': 0.80}
    }

    save_best_model(best_result, mock_model, performance_metrics, output_model, output_report)

    # Check files exist
    assert os.path.exists(output_model), "Model file not created"
    assert os.path.exists(output_report), "Report file not created"

    # Verify model can be loaded
    loaded_model = joblib.load(output_model)
    assert loaded_model is not None

    # Verify report content
    with open(output_report, 'r') as f:
        report_data = json.load(f)
    
    assert report_data['best_model_name'] == 'TestModel'
    assert report_data['metrics']['r2'] == 0.85
    assert report_data['performance_details']['best_model'] == 'TestModel'

def test_save_best_model_creates_directories(temp_dirs, mock_model):
    """Test that save_best_model creates directories if they don't exist."""
    model_path, report_path = temp_dirs
    # Remove directories to test recreation
    shutil.rmtree(model_path)
    shutil.rmtree(report_path)
    
    output_model = os.path.join(model_path, 'subdir', 'model.joblib')
    output_report = os.path.join(report_path, 'subdir', 'report.json')

    best_result = TrainingResult(
        model_name='TestModel',
        r2=0.85,
        mae=0.12,
        rmse=0.15,
        params={},
        feature_importance=None
    )

    save_best_model(best_result, mock_model, {}, output_model, output_report)

    assert os.path.exists(output_model)
    assert os.path.exists(output_report)