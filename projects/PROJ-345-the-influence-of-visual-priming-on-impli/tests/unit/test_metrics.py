import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.metrics import (
    calculate_vif,
    check_collinearity,
    run_vif_analysis,
    calculate_model_convergence_metrics,
    save_convergence_metrics
)

class TestModelConvergenceMetrics:
    """Tests for model convergence success rate measurement."""

    def test_calculate_convergence_rate_pass(self):
        """Test that a convergence rate above threshold returns PASS status."""
        metrics = calculate_model_convergence_metrics(total_attempts=100, successful_convergences=90, threshold=0.80)
        
        assert metrics["convergence_rate"] == 0.90
        assert metrics["total_attempts"] == 100
        assert metrics["successful_convergences"] == 90
        assert metrics["failed_convergences"] == 10
        assert metrics["threshold"] == 0.80
        assert metrics["status"] == "PASS"
        assert metrics["message"].startswith("Convergence rate: 90.00%")

    def test_calculate_convergence_rate_fail(self):
        """Test that a convergence rate below threshold returns FAIL status."""
        metrics = calculate_model_convergence_metrics(total_attempts=100, successful_convergences=70, threshold=0.80)
        
        assert metrics["convergence_rate"] == 0.70
        assert metrics["status"] == "FAIL"
        assert "below threshold" in metrics["message"].lower()

    def test_calculate_convergence_rate_zero_attempts(self):
        """Test handling of zero total attempts."""
        metrics = calculate_model_convergence_metrics(total_attempts=0, successful_convergences=0)
        
        assert metrics["convergence_rate"] == 0.0
        assert metrics["status"] == "FAIL"

    def test_save_convergence_metrics_creates_file(self, tmp_path):
        """Test that save_convergence_metrics creates the output file."""
        metrics = calculate_model_convergence_metrics(100, 85)
        output_path = save_convergence_metrics(metrics, str(tmp_path / "test_metrics.json"))
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["convergence_rate"] == 0.85
        assert saved_data["status"] == "PASS"

    def test_custom_threshold(self):
        """Test that custom threshold is respected."""
        metrics = calculate_model_convergence_metrics(100, 85, threshold=0.90)
        
        assert metrics["threshold"] == 0.90
        assert metrics["status"] == "FAIL"  # 0.85 < 0.90

class TestVIF:
    """Tests for VIF calculation."""

    def test_calculate_vif_basic(self):
        """Test basic VIF calculation."""
        df = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'x2': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],  # Perfectly correlated with x1
            'x3': [1, 3, 2, 4, 3, 5, 4, 6, 5, 7]
        })
        
        vif_values = calculate_vif(df, ['x1', 'x2', 'x3'])
        
        assert 'x1' in vif_values
        assert 'x2' in vif_values
        assert 'x3' in vif_values

    def test_check_collinearity_flagging(self):
        """Test that collinearity is flagged when VIF > threshold."""
        df = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'x2': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
            'x3': [1, 3, 2, 4, 3, 5, 4, 6, 5, 7]
        })
        
        result = check_collinearity(df, ['x1', 'x2', 'x3'], threshold=5.0)
        
        assert result["is_collinear"]
        assert len(result["flagged_features"]) > 0

    def test_run_vif_analysis_comprehensive(self):
        """Test comprehensive VIF analysis."""
        df = pd.DataFrame({
            'x1': np.random.randn(100),
            'x2': np.random.randn(100),
            'x3': np.random.randn(100)
        })
        
        result = run_vif_analysis(df, ['x1', 'x2', 'x3'])
        
        assert "vif_values" in result
        assert "flagged_features" in result
        assert "max_vif" in result
        assert "threshold" in result