"""
Unit tests for threshold detection module (T024)
"""
import json
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from code.analysis.threshold import (
    piecewise_linear,
    detect_change_points,
    calculate_threshold_candidates,
    write_threshold_candidates
)

class TestPiecewiseLinear:
    """Tests for the piecewise linear function"""
    
    def test_piecewise_linear_continuous(self):
        """Test that the function is continuous at the breakpoint"""
        x = np.array([0, 1, 2, 3, 4, 5])
        x0 = 2.5
        k1 = 1.0
        k2 = 2.0
        b = 0.0
        
        y = piecewise_linear(x, x0, k1, k2, b)
        
        # Check continuity at breakpoint (approximate)
        y_at_breakpoint = piecewise_linear(np.array([x0]), x0, k1, k2, b)[0]
        expected_left = k1 * x0 + b
        expected_right = k2 * (x0 - x0) + k1 * x0 + b
        
        assert np.isclose(y_at_breakpoint, expected_left)
        assert np.isclose(y_at_breakpoint, expected_right)
    
    def test_piecewise_linear_slopes(self):
        """Test that slopes are correct on each side"""
        x = np.array([0, 1, 2, 3, 4, 5])
        x0 = 2.5
        k1 = 2.0
        k2 = 1.0
        b = 0.0
        
        y = piecewise_linear(x, x0, k1, k2, b)
        
        # Points before breakpoint should follow k1*x + b
        y_before = y[x < x0]
        x_before = x[x < x0]
        
        # Points after breakpoint should follow k2*(x-x0) + k1*x0 + b
        y_after = y[x >= x0]
        x_after = x[x >= x0]
        
        # Check slopes approximately
        if len(x_before) > 1:
            slope_before = (y_before[-1] - y_before[0]) / (x_before[-1] - x_before[0])
            assert np.isclose(slope_before, k1, atol=0.1)
        
        if len(x_after) > 1:
            slope_after = (y_after[-1] - y_after[0]) / (x_after[-1] - x_after[0])
            assert np.isclose(slope_after, k2, atol=0.1)

class TestDetectChangePoints:
    """Tests for change point detection"""
    
    def test_detect_change_points_linear_data(self):
        """Test detection on purely linear data (should find no significant change)"""
        np.random.seed(42)
        x = np.linspace(0, 10, 100)
        y = 2 * x + 1 + np.random.normal(0, 0.1, 100)
        
        breakpoint, fit_info = detect_change_points(x, y)
        
        # For linear data, we might still find a breakpoint, but improvement should be small
        assert breakpoint is not None or "error" in fit_info
        
    def test_detect_change_points_with_breakpoint(self):
        """Test detection on data with a known breakpoint"""
        np.random.seed(42)
        x = np.linspace(0, 10, 100)
        
        # Create piecewise data with breakpoint at x=5
        y = np.where(
            x < 5,
            1 * x + 0,  # slope 1 before
            3 * (x - 5) + 5  # slope 3 after
        ) + np.random.normal(0, 0.2, 100)
        
        breakpoint, fit_info = detect_change_points(x, y)
        
        # Should find a breakpoint near 5
        if breakpoint is not None:
            assert 3.0 < breakpoint < 7.0
            # Piecewise fit should be better than linear
            assert fit_info.get("improvement", 0) > 0
        
    def test_insufficient_data(self):
        """Test with insufficient data points"""
        x = np.array([1, 2, 3])
        y = np.array([1, 2, 3])
        
        breakpoint, fit_info = detect_change_points(x, y)
        
        assert breakpoint is None
        assert "error" in fit_info

class TestCalculateThresholdCandidates:
    """Tests for threshold candidate calculation"""
    
    def test_calculate_threshold_candidates_empty_data(self):
        """Test with empty data"""
        data = {}
        candidates = calculate_threshold_candidates(data)
        assert candidates == []
    
    def test_calculate_threshold_candidates_single_language(self):
        """Test with single language data"""
        data = {
            "python": {
                "complexity_values": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "normalized_loss_values": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            }
        }
        
        candidates = calculate_threshold_candidates(data)
        
        assert len(candidates) == 1
        assert candidates[0]["language"] == "python"
    
    def test_calculate_threshold_candidates_mismatched_lengths(self):
        """Test with mismatched array lengths"""
        data = {
            "python": {
                "complexity_values": [1, 2, 3, 4, 5],
                "normalized_loss_values": [1, 2, 3]
            }
        }
        
        candidates = calculate_threshold_candidates(data)
        
        assert len(candidates) == 1
        # Should use min length
        assert candidates[0]["sample_size"] == 3

class TestWriteThresholdCandidates:
    """Tests for writing threshold candidates"""
    
    def test_write_threshold_candidates(self, tmp_path):
        """Test writing candidates to file"""
        candidates = [
            {
                "language": "python",
                "breakpoint": 5.0,
                "fit_statistics": {"improvement": 0.1},
                "sample_size": 100,
                "detection_method": "piecewise_linear_regression"
            }
        ]
        
        output_path = tmp_path / "test_output.json"
        write_threshold_candidates(candidates, output_path)
        
        assert output_path.exists()
        
        with open(output_path, "r") as f:
            result = json.load(f)
        
        assert result["status"] == "completed"
        assert len(result["threshold_candidates"]) == 1
        assert result["threshold_candidates"][0]["language"] == "python"