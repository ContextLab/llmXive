import pytest
import json
import tempfile
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.models.generate_report import generate_model_report, load_json_file

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_generate_model_report_valid_input(temp_dir):
    """Test generation with valid input data."""
    metrics = {
        "R2": 0.85,
        "MAE": 2.3,
        "RMSE": 3.1
    }
    hyperparameters = {
        "model": "RandomForest",
        "n_estimators": 100,
        "max_depth": 10
    }
    statistical_test = {
        "method": "Corrected Resampled t-test",
        "p_value": 0.032,
        "confidence_interval": [0.01, 0.05]
    }
    
    output_path = temp_dir / "model_report.json"
    
    generate_model_report(metrics, hyperparameters, statistical_test, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    assert "metrics" in report
    assert report["metrics"]["R2"] == 0.85
    assert report["metrics"]["MAE"] == 2.3
    assert report["metrics"]["RMSE"] == 3.1
    
    assert "hyperparameters" in report
    assert report["hyperparameters"]["model"] == "RandomForest"
    
    assert "statistical_test" in report
    assert report["statistical_test"]["method"] == "Corrected Resampled t-test"
    assert report["statistical_test"]["p_value"] == 0.032
    assert report["statistical_test"]["confidence_interval"] == [0.01, 0.05]

def test_generate_model_report_invalid_metric_missing(temp_dir):
    """Test that missing required metric raises ValueError."""
    metrics = {
        "R2": 0.85,
        "MAE": 2.3
        # RMSE missing
    }
    hyperparameters = {"model": "LinearRegression"}
    statistical_test = {
        "method": "Test",
        "p_value": 0.05,
        "confidence_interval": [0.0, 0.1]
    }
    
    output_path = temp_dir / "model_report.json"
    
    with pytest.raises(ValueError, match="Missing required metric: RMSE"):
        generate_model_report(metrics, hyperparameters, statistical_test, output_path)

def test_generate_model_report_invalid_statistical_test(temp_dir):
    """Test that missing statistical test fields raises ValueError."""
    metrics = {
        "R2": 0.85,
        "MAE": 2.3,
        "RMSE": 3.1
    }
    hyperparameters = {"model": "LinearRegression"}
    statistical_test = {
        "method": "Test",
        # p_value missing
        "confidence_interval": [0.0, 0.1]
    }
    
    output_path = temp_dir / "model_report.json"
    
    with pytest.raises(ValueError, match="statistical_test must contain"):
        generate_model_report(metrics, hyperparameters, statistical_test, output_path)

def test_generate_model_report_invalid_ci_format(temp_dir):
    """Test that invalid confidence interval format raises ValueError."""
    metrics = {
        "R2": 0.85,
        "MAE": 2.3,
        "RMSE": 3.1
    }
    hyperparameters = {"model": "LinearRegression"}
    statistical_test = {
        "method": "Test",
        "p_value": 0.05,
        "confidence_interval": [0.0, 0.1, 0.2]  # Should be exactly 2 elements
    }
    
    output_path = temp_dir / "model_report.json"
    
    with pytest.raises(ValueError, match="confidence_interval must be a list of two floats"):
        generate_model_report(metrics, hyperparameters, statistical_test, output_path)

def test_load_json_file_not_found(temp_dir):
    """Test that load_json_file raises FileNotFoundError for missing file."""
    non_existent = temp_dir / "does_not_exist.json"
    
    with pytest.raises(FileNotFoundError):
        load_json_file(non_existent)

def test_load_json_file_valid(temp_dir):
    """Test loading a valid JSON file."""
    test_data = {"key": "value", "number": 42}
    file_path = temp_dir / "test.json"
    
    with open(file_path, 'w') as f:
        json.dump(test_data, f)
    
    loaded = load_json_file(file_path)
    assert loaded == test_data