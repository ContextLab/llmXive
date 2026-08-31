import os
import json
import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.reporter import generate_baseline_report, generate_comparative_report, generate_analysis_report
from config import ensure_directories

@pytest.fixture
def temp_metrics_dir(tmp_path):
    # Create a temporary directory structure mimicking the project
    metrics_dir = tmp_path / "data" / "metrics"
    metrics_dir.mkdir(parents=True)
    os.chdir(tmp_path)
    return metrics_dir

def test_generate_baseline_report(temp_metrics_dir):
    """Test that generate_baseline_report creates a valid JSON file with required keys."""
    test_data = [
        {
            "clip_id": "clip_001", 
            "peak_memory": 1024.5, 
            "inference_time": 1.5,
            "consecutive_ssim": 0.95, 
            "temporal_gradient_variance": 0.01,
            "flow_magnitude": 2.5,
            "invalid_flow": False
        },
        {
            "clip_id": "clip_002", 
            "peak_memory": 2048.0, 
            "inference_time": 2.0,
            "consecutive_ssim": 0.92, 
            "temporal_gradient_variance": 0.02,
            "flow_magnitude": 5.1,
            "invalid_flow": True
        }
    ]
    
    output_path = "data/metrics/baseline_results.json"
    result = generate_baseline_report(test_data, output_path)
    
    assert os.path.exists(result)
    with open(result, 'r') as f:
        data = json.load(f)
    
    assert data["model"] == "baseline"
    assert data["count"] == 2
    assert "avg_peak_memory" in data
    assert "avg_inference_time" in data
    assert "avg_consecutive_ssim" in data
    assert "avg_temporal_gradient_variance" in data
    assert "individual_records" in data
    assert len(data["individual_records"]) == 2
    
    # Verify specific keys in individual records match task requirements
    rec = data["individual_records"][0]
    assert "clip_id" in rec
    assert "peak_memory" in rec
    assert "inference_time" in rec
    assert "consecutive_ssim" in rec
    assert "temporal_gradient_variance" in rec

def test_generate_comparative_report(temp_metrics_dir):
    """Test that generate_comparative_report creates a valid comparison JSON."""
    baseline_data = [
        {"clip_id": "c1", "peak_memory": 100.0, "inference_time": 1.0, "consecutive_ssim": 0.9}
    ]
    flow_data = [
        {"clip_id": "c1", "peak_memory": 80.0, "inference_time": 1.2, "consecutive_ssim": 0.88}
    ]
    
    output_path = "data/metrics/flow_results.json"
    result = generate_comparative_report(baseline_data, flow_data, output_path)
    
    assert os.path.exists(result)
    with open(result, 'r') as f:
        data = json.load(f)
    
    assert "comparison" in data
    assert data["comparison"]["memory_reduction"] == 20.0
    assert data["comparison"]["ssim_change"] == -0.02

def test_generate_analysis_report(temp_metrics_dir):
    """Test that generate_analysis_report creates a valid analysis JSON."""
    ks_result = {"statistic": 0.1, "pvalue": 0.01}
    reg_result = {"threshold": 4.5, "regression_coeff": -0.2}
    sens_result = {"cutoffs": [0.01, 0.05], "inconsistency_rates": [0.0, 0.1]}
    
    output_path = "data/metrics/analysis_results.json"
    result = generate_analysis_report(ks_result, reg_result, sens_result, output_path)
    
    assert os.path.exists(result)
    with open(result, 'r') as f:
        data = json.load(f)
    
    assert "kolmogorov_smirnov_test" in data
    assert "piecewise_regression" in data
    assert "conclusion" in data
    assert data["conclusion"]["significant_difference"] == True

def test_baseline_report_generation(temp_metrics_dir):
    """
    Specific test for T017 verification: 
    Verify the report contains the exact keys required by the task.
    """
    # Simulate data that would come from T016a metrics
    metrics = [
        {
            "clip_id": "davis_01",
            "peak_memory": 1500.5,
            "inference_time": 3.2,
            "consecutive_ssim": 0.98,
            "temporal_gradient_variance": 0.005
        }
    ]
    
    output_path = "data/metrics/baseline_results.json"
    generate_baseline_report(metrics, output_path)
    
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    # Check top level
    assert report["model"] == "baseline"
    
    # Check individual record structure matches T017 spec
    assert len(report["individual_records"]) == 1
    rec = report["individual_records"][0]
    
    required_keys = ["clip_id", "peak_memory", "inference_time", "consecutive_ssim", "temporal_gradient_variance"]
    for key in required_keys:
        assert key in rec, f"Missing required key: {key}"