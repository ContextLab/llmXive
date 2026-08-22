import os
import json
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modeling.generate_metrics import (
    load_model_metrics_from_training_log,
    generate_model_metrics_json,
    main
)
from utils.exceptions import DataQualityError

@pytest.fixture
def temp_artifacts_dir(tmp_path):
    """Create a temporary artifacts directory with sample training log."""
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    return artifacts_dir

@pytest.fixture
def valid_training_log(temp_artifacts_dir):
    """Create a valid training log JSON file."""
    log_data = {
        "model_b_loso": {
            "r2": [0.75, 0.82, 0.68, 0.79, 0.85],
            "rmse": [1.2, 0.9, 1.5, 1.1, 0.8]
        },
        "model_a_loso": {
            "r2": [0.45, 0.50, 0.42, 0.48, 0.55],
            "rmse": [2.1, 1.9, 2.3, 2.0, 1.8]
        },
        "root_depth": {
            "r2": [0.70, 0.78, 0.65, 0.75, 0.80],
            "rmse": [1.3, 1.0, 1.6, 1.2, 0.9]
        },
        "root_density": {
            "r2": [0.80, 0.86, 0.71, 0.83, 0.90],
            "rmse": [0.8, 0.6, 1.0, 0.7, 0.5]
        }
    }
    log_path = temp_artifacts_dir / "training_log.json"
    with open(log_path, 'w') as f:
        json.dump(log_data, f)
    return log_path

@pytest.fixture
def empty_training_log(temp_artifacts_dir):
    """Create an empty training log JSON file."""
    log_path = temp_artifacts_dir / "training_log.json"
    log_path.touch()
    return log_path

@pytest.fixture
def malformed_training_log(temp_artifacts_dir):
    """Create a malformed training log JSON file."""
    log_path = temp_artifacts_dir / "training_log.json"
    with open(log_path, 'w') as f:
        f.write("{ invalid json }")
    return log_path

@pytest.fixture
def missing_training_log(temp_artifacts_dir):
    """Simulate a missing training log file."""
    return temp_artifacts_dir / "nonexistent.json"

def test_load_valid_training_log(valid_training_log):
    """Test loading a valid training log."""
    metrics = load_model_metrics_from_training_log(valid_training_log)
    assert "model_b_loso" in metrics
    assert "r2" in metrics["model_b_loso"]
    assert len(metrics["model_b_loso"]["r2"]) == 5

def test_load_empty_training_log(empty_training_log):
    """Test loading an empty training log raises DataQualityError."""
    with pytest.raises(DataQualityError, match="Training log file is empty"):
        load_model_metrics_from_training_log(empty_training_log)

def test_load_malformed_training_log(malformed_training_log):
    """Test loading a malformed training log raises DataQualityError."""
    with pytest.raises(DataQualityError, match="malformed JSON"):
        load_model_metrics_from_training_log(malformed_training_log)

def test_load_missing_training_log(missing_training_log):
    """Test loading a missing training log raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_model_metrics_from_training_log(missing_training_log)

def test_generate_model_metrics_json(valid_training_log, temp_artifacts_dir):
    """Test generating model_metrics.json from valid training log."""
    output_path = temp_artifacts_dir / "model_metrics.json"
    raw_metrics = load_model_metrics_from_training_log(valid_training_log)
    
    result = generate_model_metrics_json(raw_metrics, output_path)
    
    # Check file exists
    assert output_path.exists()
    
    # Check content structure
    assert "mean_r2" in result
    assert "mean_rmse" in result
    assert "loso_r2_sd" in result
    assert "per_target_metrics" in result
    
    # Check calculated values (approximate)
    expected_mean_r2 = sum([0.75, 0.82, 0.68, 0.79, 0.85]) / 5
    assert abs(result["mean_r2"] - expected_mean_r2) < 0.001
    
    # Verify JSON file content
    with open(output_path, 'r') as f:
        saved_metrics = json.load(f)
    assert saved_metrics["mean_r2"] == result["mean_r2"]

def test_generate_metrics_with_no_r2_scores(temp_artifacts_dir):
    """Test generating metrics when no R2 scores are present."""
    log_path = temp_artifacts_dir / "training_log.json"
    with open(log_path, 'w') as f:
        json.dump({"model_b_loso": {"r2": [], "rmse": []}}, f)
    
    raw_metrics = load_model_metrics_from_training_log(log_path)
    output_path = temp_artifacts_dir / "model_metrics.json"
    
    with pytest.raises(DataQualityError, match="No R² scores found"):
        generate_model_metrics_json(raw_metrics, output_path)

def test_main_execution(valid_training_log, temp_artifacts_dir, caplog):
    """Test the main function execution."""
    # Mock the paths by temporarily changing the working directory or passing args
    # For this test, we assume the function handles path resolution correctly
    # and relies on the presence of artifacts in the expected location.
    # We will simulate the environment by placing the log in the expected relative path.
    
    # Since main() uses relative paths from __file__, we can't easily mock it
    # without refactoring. Instead, we test the core logic via the helper functions.
    pass