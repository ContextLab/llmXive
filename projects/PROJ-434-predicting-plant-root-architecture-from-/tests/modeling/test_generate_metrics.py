import json
import os
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.insert(0, str(project_root))

from modeling.generate_metrics import generate_model_metrics_json

@pytest.fixture
def sample_metrics():
    """Sample metrics dictionary matching the expected structure from training."""
    return {
        "mean_r2": 0.75,
        "mean_rmse": 0.12,
        "loso_r2_sd": 0.05,
        "spatial_cv_r2_sd": 0.03,
        "per_target_metrics": {
            "root_depth": {
                "mean_r2": 0.78,
                "mean_rmse": 0.10,
                "std_r2": 0.04,
                "std_rmse": 0.02
            },
            "root_mass": {
                "mean_r2": 0.72,
                "mean_rmse": 0.14,
                "std_r2": 0.06,
                "std_rmse": 0.03
            }
        }
    }

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_generate_model_metrics_json_structure(sample_metrics, temp_output_dir):
    """Test that the generated JSON has the correct structure."""
    output_path = temp_output_dir / "model_metrics.json"
    
    generate_model_metrics_json(sample_metrics, output_path)
    
    assert output_path.exists(), "Output file was not created"
    
    with open(output_path, 'r') as f:
        result = json.load(f)
    
    # Check top-level keys
    required_keys = ["mean_r2", "mean_rmse", "loso_r2_sd", "spatial_cv_r2_sd", "per_target_metrics"]
    for key in required_keys:
        assert key in result, f"Missing required key: {key}"
    
    # Check types
    assert isinstance(result["mean_r2"], float)
    assert isinstance(result["mean_rmse"], float)
    assert isinstance(result["loso_r2_sd"], float)
    assert isinstance(result["spatial_cv_r2_sd"], float)
    assert isinstance(result["per_target_metrics"], dict)
    
    # Check per-target metrics structure
    for target, metrics in result["per_target_metrics"].items():
        assert "mean_r2" in metrics
        assert "mean_rmse" in metrics
        assert "std_r2" in metrics
        assert "std_rmse" in metrics
        assert isinstance(metrics["mean_r2"], float)
        assert isinstance(metrics["mean_rmse"], float)

def test_generate_model_metrics_json_values(sample_metrics, temp_output_dir):
    """Test that the generated JSON contains correct values."""
    output_path = temp_output_dir / "model_metrics.json"
    
    generate_model_metrics_json(sample_metrics, output_path)
    
    with open(output_path, 'r') as f:
        result = json.load(f)
    
    # Check that values match the input
    assert result["mean_r2"] == sample_metrics["mean_r2"]
    assert result["mean_rmse"] == sample_metrics["mean_rmse"]
    assert result["loso_r2_sd"] == sample_metrics["loso_r2_sd"]
    assert result["spatial_cv_r2_sd"] == sample_metrics["spatial_cv_r2_sd"]
    
    # Check per-target metrics
    for target in sample_metrics["per_target_metrics"]:
        for key in ["mean_r2", "mean_rmse", "std_r2", "std_rmse"]:
            assert result["per_target_metrics"][target][key] == sample_metrics["per_target_metrics"][target][key]

def test_generate_model_metrics_json_creates_directory(temp_output_dir):
    """Test that the function creates the output directory if it doesn't exist."""
    output_path = temp_output_dir / "subdir" / "model_metrics.json"
    
    generate_model_metrics_json({
        "mean_r2": 0.5,
        "mean_rmse": 0.1,
        "loso_r2_sd": 0.01,
        "spatial_cv_r2_sd": 0.01,
        "per_target_metrics": {}
    }, output_path)
    
    assert output_path.exists()
    assert output_path.parent.exists()

def test_generate_model_metrics_json_empty_per_target(sample_metrics, temp_output_dir):
    """Test handling of empty per_target_metrics."""
    sample_metrics["per_target_metrics"] = {}
    output_path = temp_output_dir / "model_metrics.json"
    
    generate_model_metrics_json(sample_metrics, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        result = json.load(f)
    
    assert result["per_target_metrics"] == {}