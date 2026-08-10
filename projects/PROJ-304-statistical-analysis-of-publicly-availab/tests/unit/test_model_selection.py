"""
Unit tests for model selection logic in code/model_selection.py.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Import the module under test
# We need to adjust the import path based on the project structure
# Assuming tests are run from the root, and code is in 'code' directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from model_selection import (
    load_model_results,
    calculate_rmse_reduction,
    is_rmse_significant,
    select_best_model,
    main
)


@pytest.fixture
def sample_model_results():
    """Fixture providing sample model results data."""
    return [
        {
            "model_type": "OLS",
            "converged": True,
            "metrics": {
                "rmse": 10.0,
                "aic": 100.0,
                "r2": 0.5
            }
        },
        {
            "model_type": "Spatial Lag",
            "converged": True,
            "metrics": {
                "rmse": 8.5, # 15% reduction
                "aic": 90.0,
                "r2": 0.65
            }
        },
        {
            "model_type": "Spatial Error",
            "converged": True,
            "metrics": {
                "rmse": 9.0, # 10% reduction
                "aic": 85.0, # Lowest AIC
                "r2": 0.60
            }
        },
        {
            "model_type": "OLS_Failed",
            "converged": False,
            "metrics": {
                "rmse": 12.0,
                "aic": 110.0
            }
        }
    ]


def test_calculate_rmse_reduction():
    """Test RMSE reduction calculation."""
    # 10% reduction
    assert calculate_rmse_reduction(10.0, 9.0) == 10.0
    # 0% reduction
    assert calculate_rmse_reduction(10.0, 10.0) == 0.0
    # Negative reduction (worse)
    assert calculate_rmse_reduction(10.0, 11.0) == -10.0
    # Edge case: baseline 0
    assert calculate_rmse_reduction(0.0, 5.0) == 0.0


def test_is_rmse_significant():
    """Test RMSE significance check."""
    # Significant
    assert is_rmse_significant(10.0, 8.0, threshold=15.0) is True # 20%
    # Not significant
    assert is_rmse_significant(10.0, 9.0, threshold=15.0) is False # 10%
    # Boundary
    assert is_rmse_significant(10.0, 8.5, threshold=15.0) is True # 15%


def test_select_best_model_basic(sample_model_results):
    """Test basic model selection logic."""
    best, summary = select_best_model(sample_model_results, baseline_model_name="OLS", rmse_threshold=10.0)

    assert best is not None
    # Spatial Error has lowest AIC (85.0) and 10% reduction (>= 10% threshold)
    assert best['model_type'] == "Spatial Error"
    assert summary['best_model_type'] == "Spatial Error"
    assert summary['status'] == "success"


def test_select_best_model_no_significant_reduction(sample_model_results):
    """Test selection when no model meets RMSE threshold."""
    # Set threshold higher than any reduction
    best, summary = select_best_model(sample_model_results, baseline_model_name="OLS", rmse_threshold=20.0)

    assert best is not None
    # Should fall back to lowest AIC (Spatial Error) but mark as not significant
    assert best['model_type'] == "Spatial Error"
    assert "below threshold" in summary['selection_reason']


def test_select_best_model_no_baseline(sample_model_results):
    """Test selection when baseline model is missing."""
    # Remove OLS from results
    results_no_ols = [r for r in sample_model_results if r['model_type'] != "OLS"]
    best, summary = select_best_model(results_no_ols, baseline_model_name="OLS", rmse_threshold=10.0)

    assert best is not None
    # Should use first valid model as baseline (Spatial Lag)
    # Spatial Lag RMSE: 8.5. Spatial Error RMSE: 9.0.
    # Spatial Lag is baseline. Spatial Error vs Spatial Lag: (8.5 - 9.0)/8.5 = -5.8%
    # Spatial Error AIC is lower.
    # Logic picks lowest AIC.
    assert best['model_type'] == "Spatial Error"


def test_select_best_model_empty():
    """Test selection with empty results."""
    best, summary = select_best_model([])
    assert best is None
    assert summary['status'] == "no_data"


def test_select_best_model_no_converged():
    """Test selection when no models converged."""
    results = [
        {"model_type": "OLS", "converged": False, "metrics": {"rmse": 10.0, "aic": 100.0}}
    ]
    best, summary = select_best_model(results)
    assert best is None
    assert summary['status'] == "no_valid_models"


def test_load_model_results_invalid_path():
    """Test loading results from non-existent path."""
    with pytest.raises(FileNotFoundError):
        load_model_results(Path("/nonexistent/path.json"))


def test_main_integration(sample_model_results):
    """Test the main function integration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        results_file = tmp_path / "model_results.json"
        output_file = tmp_path / "model_selection_report.json"

        # Write sample results
        with open(results_file, 'w') as f:
            json.dump(sample_model_results, f)

        # Mock get_project_root and paths
        with patch('model_selection.get_project_root', return_value=tmp_path):
            with patch('model_selection.get_logger'): # Mock logger to avoid noise
                main()

        assert output_file.exists()
        with open(output_file, 'r') as f:
            report = json.load(f)

        assert "selection_summary" in report
        assert "best_model_details" in report
        assert report["selection_summary"]["status"] == "success"