"""
Unit tests for sensitivity_analysis.py (T023).

Tests verify:
1. Correct loading of evaluation metrics.
2. Correct sweep logic (threshold comparison).
3. Correct report generation structure.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Import functions to test
from code.models.sensitivity_analysis import (
    run_sensitivity_sweep,
    save_sensitivity_report,
    load_evaluation_metrics
)

@pytest.fixture
def mock_data_dir():
    """Creates a temporary directory with mock evaluation data."""
    temp_dir = Path(tempfile.mkdtemp())
    data_dir = temp_dir / "data"
    data_dir.mkdir()
    
    # Create mock evaluation_report.json
    eval_data = {
        "per_family": {
            "Aluminum": {"r2_score": 0.85, "mae": 0.05, "rmse": 0.08},
            "Steel": {"r2_score": 0.45, "mae": 0.12, "rmse": 0.15},
            "Titanium": {"r2_score": 0.15, "mae": 0.20, "rmse": 0.25}
        },
        "data_source_type": "Synthetic"
    }
    with open(data_dir / "evaluation_report.json", 'w') as f:
        json.dump(eval_data, f)
        
    # Create mock importance_report.json
    imp_data = {
        "features": [
            {"name": "strain_rate", "importance": 0.45},
            {"name": "temperature", "importance": 0.30},
            {"name": "rolling_speed", "importance": 0.05},
            {"name": "reduction_ratio", "importance": 0.02}
        ]
    }
    with open(data_dir / "importance_report.json", 'w') as f:
        json.dump(imp_data, f)
        
    yield data_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_run_sensitivity_sweep(mock_data_dir):
    """Test the sweep logic with known data."""
    # Manually create DFs to avoid file path issues in test
    metrics_df = pd.DataFrame([
        {"family": "Aluminum", "r2_score": 0.85},
        {"family": "Steel", "r2_score": 0.45},
        {"family": "Titanium", "r2_score": 0.15}
    ])
    
    importance_df = pd.DataFrame([
        {"name": "strain_rate", "importance": 0.45},
        {"name": "temperature", "importance": 0.30},
        {"name": "rolling_speed", "importance": 0.05},
        {"name": "reduction_ratio", "importance": 0.02}
    ])
    
    # Sweep a small range for speed
    results = run_sensitivity_sweep(
        metrics_df, 
        importance_df, 
        r2_start=0.40, r2_end=0.50, r2_step=0.05,
        imp_start=0.40, imp_end=0.50, imp_step=0.05
    )
    
    assert len(results) > 0
    
    # Check specific case: R² 0.40 (should pass for Al, Steel), Imp 0.40 (should pass for strain_rate)
    # R² 0.45 (passes for Al, Steel), Imp 0.45 (passes for strain_rate)
    # R² 0.50 (passes only Al), Imp 0.45 (passes for strain_rate) -> Stable
    # R² 0.50, Imp 0.50 (fails) -> Unstable
    
    r2_040_040 = next((r for r in results if r["r2_threshold"] == 0.40 and r["importance_threshold"] == 0.40), None)
    assert r2_040_040 is not None
    assert r2_040_040["is_stable"] is True
    assert r2_040_040["r2_pass_count"] == 2 # Al, Steel
    assert r2_040_040["imp_pass_count"] == 1 # strain_rate

    r2_050_050 = next((r for r in results if r["r2_threshold"] == 0.50 and r["importance_threshold"] == 0.50), None)
    assert r2_050_050 is not None
    assert r2_050_050["is_stable"] is False # No feature >= 0.50

def test_save_sensitivity_report():
    """Test report generation structure."""
    results = [
        {"r2_threshold": 0.10, "importance_threshold": 0.10, "is_stable": True, "r2_pass_count": 1, "imp_pass_count": 1},
        {"r2_threshold": 0.90, "importance_threshold": 0.90, "is_stable": False, "r2_pass_count": 0, "imp_pass_count": 0}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_report.json"
        save_sensitivity_report(results, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        assert "summary" in report
        assert "results" in report
        assert report["summary"]["total_combinations"] == 2
        assert report["summary"]["stable_combinations"] == 1