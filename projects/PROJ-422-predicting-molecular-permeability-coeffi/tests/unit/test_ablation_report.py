import json
import os
import tempfile
from pathlib import Path
import pytest

from analysis.ablation_report import (
    load_metrics,
    calculate_ablation_improvement,
    generate_ablation_report
)


@pytest.fixture
def temp_metrics_file():
    """Create a temporary metrics file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = {
            "gnn": {
                "rmse": 0.45,
                "mae": 0.32,
                "r2": 0.78,
                "training_time": 120.5
            },
            "ablation": {
                "rmse": 0.52,
                "mae": 0.38,
                "r2": 0.65,
                "training_time": 45.2
            }
        }
        json.dump(data, f)
        f.flush()
        yield Path(f.name)
    os.unlink(f.name)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_load_metrics(temp_metrics_file):
    """Test loading metrics from a JSON file."""
    metrics = load_metrics(temp_metrics_file)
    assert "gnn" in metrics
    assert metrics["gnn"]["rmse"] == 0.45
    assert metrics["ablation"]["r2"] == 0.65


def test_calculate_ablation_improvement():
    """Test the improvement calculation logic."""
    gnn = {"rmse": 0.40, "mae": 0.30, "r2": 0.80}
    ablation = {"rmse": 0.50, "mae": 0.40, "r2": 0.60}
    
    improvements = calculate_ablation_improvement(gnn, ablation)
    
    # RMSE: (0.50 - 0.40) / 0.50 = 0.20 -> 20%
    assert abs(improvements["rmse_improvement_pct"] - 20.0) < 0.01
    
    # MAE: (0.40 - 0.30) / 0.40 = 0.25 -> 25%
    assert abs(improvements["mae_improvement_pct"] - 25.0) < 0.01
    
    # R2: 0.80 - 0.60 = 0.20
    assert abs(improvements["r2_delta"] - 0.20) < 0.01


def test_generate_ablation_report(temp_metrics_file, temp_output_dir):
    """Test the full report generation pipeline."""
    output_path = temp_output_dir / "test_ablation_report.md"
    
    result_path = generate_ablation_report(
        metrics_path=temp_metrics_file,
        output_path=output_path,
        ablation_metrics_path=None
    )
    
    assert result_path.exists()
    assert result_path == output_path
    
    with open(result_path, 'r') as f:
        content = f.read()
    
    # Verify key sections exist
    assert "# Ablation Study Report" in content
    assert "## Objective (FR-012)" in content
    assert "## Model Performance Comparison" in content
    assert "RMSE Improvement" in content
    assert "## Conclusion" in content
    
    # Verify numeric values are present (basic check)
    assert "0.45" in content or "0.4500" in content
    assert "20.00" in content or "20%" in content  # Approximate check
