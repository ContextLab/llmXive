import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np
import pandas as pd

# Mock config to avoid dependency on real paths during unit test
@pytest.fixture
def mock_config():
    class MockPaths:
        models = Path("/tmp/models")
        processed = Path("/tmp/processed")
        reports = Path("/tmp/reports")
    
    class MockCfg:
        paths = MockPaths()
    
    return MockCfg()

@pytest.fixture
def mock_metrics():
    return {
        "regression": {
            "rmse": 12.5
        },
        "classification": {
            "roc_auc": 0.85
        },
        "cv_scores": {
            "regression": [12.1, 12.8, 13.0, 11.9, 12.2],
            "classification": [0.82, 0.88, 0.84, 0.86, 0.83]
        }
    }

def test_generate_metrics_report(mock_metrics):
    from models.metrics_reporter import generate_metrics_report

    report = generate_metrics_report(mock_metrics)

    assert "regression" in report
    assert "classification" in report
    assert "cross_validation" in report

    # Check regression
    assert report["regression"]["rmse"] == 12.5
    assert report["regression"]["target_met"] is True  # 12.5 <= 15

    # Check classification
    assert report["classification"]["roc_auc"] == 0.85
    assert report["classification"]["target_met"] is True  # 0.85 > 0.7

    # Check CV stats
    assert report["cross_validation"]["regression"]["mean"] > 0
    assert report["cross_validation"]["regression"]["std"] > 0
    assert report["cross_validation"]["regression"]["n_folds"] == 5

def test_save_metrics_report(mock_metrics, mock_config):
    from models.metrics_reporter import generate_metrics_report, save_metrics_report

    report = generate_metrics_report(mock_metrics)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_metrics.json"
        result_path = save_metrics_report(report, output_path)

        assert result_path.exists()
        
        with open(result_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["regression"]["rmse"] == 12.5
        assert saved_data["classification"]["roc_auc"] == 0.85

def test_calculate_cv_statistics(mock_metrics):
    from models.metrics_reporter import calculate_cv_statistics

    stats = calculate_cv_statistics(mock_metrics)

    assert "regression" in stats
    assert "classification" in stats

    # Verify regression stats
    reg_scores = np.array(mock_metrics["cv_scores"]["regression"])
    assert abs(stats["regression"]["mean"] - np.mean(reg_scores)) < 1e-5
    assert abs(stats["regression"]["std"] - np.std(reg_scores)) < 1e-5

def test_load_model_metrics_missing_file(mock_config):
    from models.metrics_reporter import load_model_metrics
    
    with patch('models.metrics_reporter.get_config', return_value=mock_config):
        with patch('pathlib.Path.exists', return_value=False):
            metrics = load_model_metrics()
            
            assert metrics["regression"] == {}
            assert metrics["classification"] == {}

def test_generate_metrics_report_missing_data(mock_config):
    from models.metrics_reporter import generate_metrics_report

    empty_metrics = {
        "regression": {},
        "classification": {},
        "cv_scores": {}
    }

    report = generate_metrics_report(empty_metrics)

    assert report["regression"]["rmse"] is None
    assert report["classification"]["roc_auc"] is None
    assert report["regression"]["target_met"] is None
    assert report["classification"]["target_met"] is None
    assert report["cross_validation"]["regression"]["error"] == "No CV scores found"