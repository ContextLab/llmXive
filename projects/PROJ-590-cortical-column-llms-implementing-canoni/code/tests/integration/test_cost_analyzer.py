import pytest
import json
import os
import tempfile
from pathlib import Path
import sys

# Add project root to path if running standalone
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.experiments.cost_analyzer import compute_cost_metrics, CostMetric

@pytest.fixture
def temp_ablation_dir(tmp_path):
    """Create a temporary directory with mock ablation results."""
    ablation_dir = tmp_path / "ablation"
    ablation_dir.mkdir()

    # Create mock ablation results
    results = [
        {"config": "baseline", "mae": 0.05, "params": 100000},
        {"config": "full_model", "mae": 0.04, "params": 102000},
        {"config": "no_recurrence", "mae": 0.048, "params": 100000},
        {"config": "no_inhibition", "mae": 0.052, "params": 100000}
    ]

    for res in results:
        filepath = ablation_dir / f"ablation_{res['config']}.json"
        with open(filepath, 'w') as f:
            json.dump(res, f)

    return ablation_dir

@pytest.fixture
def temp_scaling_report(tmp_path):
    """Create a temporary scaling law report."""
    filepath = tmp_path / "scaling_law_report.md"
    content = """
    # Scaling Law Report
    
    ## Analysis
    The scaling exponent (beta) was calculated to be -0.15.
    The trend type is classified as **sublinear**.
    Doubling parameters reduces error by approximately 10%.
    """
    with open(filepath, 'w') as f:
        f.write(content)
    return filepath

def test_compute_cost_metrics_writes_output(tmp_path, temp_ablation_dir, temp_scaling_report):
    """Test that compute_cost_metrics generates the required JSON output."""
    output_path = tmp_path / "cost_metrics.json"
    
    result = compute_cost_metrics(
        ablation_dir=str(temp_ablation_dir),
        scaling_report_path=str(temp_scaling_report),
        output_path=str(output_path)
    )

    # Verify file exists
    assert output_path.exists(), "Output file was not created."

    # Verify JSON structure
    with open(output_path, 'r') as f:
        data = json.load(f)

    assert "baseline_mae" in data
    assert "full_model_mae" in data
    assert "ablation_costs" in data
    assert "scaling_exponent" in data
    assert "trend_type" in data
    assert "metabolic_overhead_ratio" in data
    assert "parameter_efficiency" in data
    assert "summary" in data

    # Verify types
    assert isinstance(data["baseline_mae"], float)
    assert isinstance(data["scaling_exponent"], float)
    assert isinstance(data["trend_type"], str)
    assert isinstance(data["ablation_costs"], dict)

    # Verify specific values from fixtures
    assert data["full_model_mae"] == 0.04
    assert data["baseline_mae"] == 0.05
    assert data["trend_type"] == "sublinear"
    assert abs(data["scaling_exponent"] - (-0.15)) < 0.01

def test_compute_cost_metrics_handles_missing_ablation(tmp_path, temp_scaling_report):
    """Test behavior when ablation directory is missing."""
    output_path = tmp_path / "cost_metrics_missing.json"
    
    # Should not raise an exception, but might use defaults
    result = compute_cost_metrics(
        ablation_dir=str(tmp_path / "nonexistent"),
        scaling_report_path=str(temp_scaling_report),
        output_path=str(output_path)
    )

    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    # Should have default values
    assert "summary" in data

def test_compute_cost_metrics_returns_object(tmp_path, temp_ablation_dir, temp_scaling_report):
    """Test that the function returns a CostMetric dataclass."""
    output_path = tmp_path / "cost_metrics_obj.json"
    
    result = compute_cost_metrics(
        ablation_dir=str(temp_ablation_dir),
        scaling_report_path=str(temp_scaling_report),
        output_path=str(output_path)
    )

    assert isinstance(result, CostMetric)
    assert result.full_model_mae == 0.04
    assert result.trend_type == "sublinear"