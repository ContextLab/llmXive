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
    """Test that generate_baseline_report creates a valid JSON file."""
    test_data = [
        {"clip_id": "clip_001", "peak_memory": 1024.5, "fps": 25.0, "ssim": 0.95, "gradient_variance": 0.01, "flow_magnitude": 2.5, "invalid_flow": False},
        {"clip_id": "clip_002", "peak_memory": 2048.0, "fps": 24.0, "ssim": 0.92, "gradient_variance": 0.02, "flow_magnitude": 5.1, "invalid_flow": True}
    ]
    
    output_path = "data/metrics/baseline_results.json"
    result = generate_baseline_report(test_data, output_path)
    
    assert os.path.exists(result)
    with open(result, 'r') as f:
        data = json.load(f)
    
    assert data["model"] == "baseline"
    assert data["count"] == 2
    assert "avg_peak_memory" in data
    assert "individual_records" in data
    assert len(data["individual_records"]) == 2

def test_generate_comparative_report(temp_metrics_dir):
    """Test that generate_comparative_report creates a valid comparison JSON."""
    baseline_data = [
        {"clip_id": "c1", "peak_memory": 100.0, "ssim": 0.9, "fps": 30.0}
    ]
    flow_data = [
        {"clip_id": "c1", "peak_memory": 80.0, "ssim": 0.88, "fps": 32.0}
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
    reg_result = {"change_point": 4.5, "slope1": 0.1, "slope2": -0.2}
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