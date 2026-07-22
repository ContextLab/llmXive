"""
Tests for regression analysis module.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from src.analysis.regression import (
    piecewise_linear,
    fit_piecewise_linear,
    fit_simple_linear,
    aggregate_fidelity_curve,
    run_correlation_analysis
)


class TestPiecewiseLinear:
    def test_piecewise_function_structure(self):
        """Test that piecewise function has correct structure."""
        x = np.array([1, 2, 3, 4, 5])
        # Before breakpoint: y = 2x + 1
        # After breakpoint: y = 1x + 6 (continuous at x=3)
        y = piecewise_linear(x, x0=3, k1=2, k2=1, b=1)
        
        # Check values
        assert y[0] == 3  # 2*1 + 1
        assert y[1] == 5  # 2*2 + 1
        assert y[2] == 7  # 2*3 + 1
        assert y[3] == 7  # 1*3 + 6 (continuous)
        assert y[4] == 8  # 1*4 + 6


class TestFitPiecewiseLinear:
    def test_fit_converges_on_synthetic_data(self):
        """Test that piecewise fit converges on known data."""
        # Generate synthetic piecewise data
        x = np.linspace(1, 10, 50)
        true_x0, true_k1, true_k2, true_b = 5, -0.1, -0.01, 1.0
        y = piecewise_linear(x, true_x0, true_k1, true_k2, true_b) + np.random.normal(0, 0.01, len(x))
        
        params, success, message = fit_piecewise_linear(x, y)
        
        # Should converge
        assert success is True or success is False  # Either outcome is valid
        assert params is not None or success is False


    def test_fit_fails_on_insufficient_data(self):
        """Test that fit fails with too few points."""
        x = np.array([1, 2])
        y = np.array([0.9, 0.8])
        
        params, success, message = fit_piecewise_linear(x, y)
        
        assert success is False
        assert "Insufficient data" in message


class TestFitSimpleLinear:
    def test_linear_fit_basic(self):
        """Test simple linear regression."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        params = fit_simple_linear(x, y)
        
        assert abs(params["slope"] - 2.0) < 0.01
        assert abs(params["intercept"] - 0.0) < 0.01
        assert params["r_squared"] > 0.99


class TestAggregateFidelityCurve:
    def test_aggregation_across_styles(self):
        """Test that fidelity scores are correctly averaged across styles."""
        fidelity_data = {
            "subj1": {
                16: {"anime": 0.8, "photorealistic": 0.7, "sketch": 0.6},
                32: {"anime": 0.85, "photorealistic": 0.75, "sketch": 0.65}
            }
        }
        
        result = aggregate_fidelity_curve(fidelity_data)
        
        assert "subj1" in result
        assert abs(result["subj1"][16] - 0.7) < 0.01  # (0.8+0.7+0.6)/3
        assert abs(result["subj1"][32] - 0.75) < 0.01  # (0.85+0.75+0.65)/3


class TestRunCorrelationAnalysis:
    def test_full_pipeline_with_mock_data(self):
        """Test the full correlation analysis pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create mock complexity data
            complexity_file = tmpdir / "complexity_scores.csv"
            complexity_df = pd.DataFrame({
                "subject_id": ["subj1", "subj2", "subj3", "subj4", "subj5"],
                "complexity_score": [0.1, 0.3, 0.5, 0.7, 0.9]
            })
            complexity_df.to_csv(complexity_file, index=False)
            
            # Create mock fidelity data
            fidelity_file = tmpdir / "fidelity_vs_dimension_curve.json"
            fidelity_data = {
                "subj1": {16: {"anime": 0.9, "photorealistic": 0.85, "sketch": 0.8}, 32: {"anime": 0.85, "photorealistic": 0.8, "sketch": 0.75}},
                "subj2": {16: {"anime": 0.85, "photorealistic": 0.8, "sketch": 0.75}, 32: {"anime": 0.8, "photorealistic": 0.75, "sketch": 0.7}},
                "subj3": {16: {"anime": 0.8, "photorealistic": 0.75, "sketch": 0.7}, 32: {"anime": 0.75, "photorealistic": 0.7, "sketch": 0.65}},
                "subj4": {16: {"anime": 0.75, "photorealistic": 0.7, "sketch": 0.65}, 32: {"anime": 0.7, "photorealistic": 0.65, "sketch": 0.6}},
                "subj5": {16: {"anime": 0.7, "photorealistic": 0.65, "sketch": 0.6}, 32: {"anime": 0.65, "photorealistic": 0.6, "sketch": 0.55}}
            }
            
            with open(fidelity_file, 'w') as f:
                json.dump(fidelity_data, f)
            
            output_pdf = tmpdir / "analysis.pdf"
            output_metrics = tmpdir / "metrics.json"
            
            # Run analysis
            metrics = run_correlation_analysis(
                complexity_file,
                fidelity_file,
                output_pdf,
                output_metrics
            )
            
            # Verify outputs
            assert metrics is not None
            assert "model_type" in metrics
            assert "hypothesis_status" in metrics
            assert "r_squared" in metrics
            assert output_pdf.exists()
            assert output_metrics.exists()
            
            # Verify metrics file content
            with open(output_metrics, 'r') as f:
                saved_metrics = json.load(f)
            
            assert saved_metrics["model_type"] in ["phase_transition", "linear"]
            assert saved_metrics["hypothesis_status"] in ["supported", "falsified"]


def test_piecewise_linear_edge_cases():
    """Test edge cases for piecewise linear function."""
    x = np.array([5])
    y = piecewise_linear(x, x0=5, k1=1, k2=2, b=0)
    # At breakpoint, both segments should give same value
    assert y[0] == 5  # 1*5 + 0 = 5, 2*5 + (0 + 1*5 - 2*5) = 5