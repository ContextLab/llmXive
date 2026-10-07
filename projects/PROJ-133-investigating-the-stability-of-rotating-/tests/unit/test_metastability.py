import pytest
import numpy as np
import os
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.metrics import (
    classify_metastability,
    calculate_false_positive_rate,
    calculate_false_negative_rate,
    calculate_vortex_density,
    calculate_radial_variance,
    calculate_structure_factor_sharpness,
    process_snapshot_file,
    calculate_all_metrics
)
from analysis.sensitivity_analysis import evaluate_threshold, SensitivityResult

class TestClassifyMetastability:
    """Tests for metastability classification logic (FR-006)."""

    def test_stable_high_density_low_vortices(self):
        """Condensate with high density and low vortex count should be stable."""
        is_meta, reason = classify_metastability(
            condensate_density=0.9,
            vortex_density=0.1
        )
        assert is_meta is False
        assert reason == "stable"

    def test_metastable_low_density(self):
        """Condensate with density drop > 30% should be metastable."""
        is_meta, reason = classify_metastability(
            condensate_density=0.6,  # 40% drop
            vortex_density=0.1
        )
        assert is_meta is True
        assert "density_drop>30%" in reason

    def test_metastable_high_vortices(self):
        """Condensate with high vortex density should be metastable."""
        is_meta, reason = classify_metastability(
            condensate_density=0.9,
            vortex_density=0.8
        )
        assert is_meta is True
        assert "vortex_density>0.50" in reason

    def test_metastable_both_conditions(self):
        """Condensate violating both conditions should be metastable."""
        is_meta, reason = classify_metastability(
            condensate_density=0.5,
            vortex_density=0.9
        )
        assert is_meta is True
        # Both reasons should be present
        assert "density_drop>30%" in reason
        assert "vortex_density>0.50" in reason

    def test_boundary_density_threshold(self):
        """Test exact boundary at 70% density."""
        # Exactly at threshold (70%)
        is_meta, reason = classify_metastability(
            condensate_density=0.7,
            vortex_density=0.1
        )
        assert is_meta is False

        # Just below threshold (69.9%)
        is_meta, reason = classify_metastability(
            condensate_density=0.699,
            vortex_density=0.1
        )
        assert is_meta is True

    def test_boundary_vortex_threshold(self):
        """Test exact boundary at vortex threshold 0.5."""
        # Exactly at threshold
        is_meta, reason = classify_metastability(
            condensate_density=0.9,
            vortex_density=0.5
        )
        assert is_meta is False

        # Just above threshold
        is_meta, reason = classify_metastability(
            condensate_density=0.9,
            vortex_density=0.501
        )
        assert is_meta is True

    def test_custom_thresholds(self):
        """Test with custom thresholds."""
        is_meta, reason = classify_metastability(
            condensate_density=0.6,
            vortex_density=0.3,
            density_threshold=0.5,  # 50% drop required
            vortex_threshold=0.2    # 0.2 max vortex density
        )
        assert is_meta is True
        assert "vortex_density>0.20" in reason

class TestErrorRates:
    """Tests for false positive/negative rate calculations."""

    def test_calculate_false_positive_rate(self):
        """Test FP rate calculation."""
        predictions = [True, True, False, False]
        ground_truth = [False, False, False, False]
        
        # 2 false positives out of 4 actual negatives
        fp_rate = calculate_false_positive_rate(predictions, ground_truth)
        assert fp_rate == 0.5

    def test_calculate_false_negative_rate(self):
        """Test FN rate calculation."""
        predictions = [False, False, True, True]
        ground_truth = [True, True, True, True]
        
        # 2 false negatives out of 4 actual positives
        fn_rate = calculate_false_negative_rate(predictions, ground_truth)
        assert fn_rate == 0.5

    def test_no_actual_negatives(self):
        """FP rate should be 0 if no actual negatives."""
        predictions = [True, True, True]
        ground_truth = [True, True, True]
        
        fp_rate = calculate_false_positive_rate(predictions, ground_truth)
        assert fp_rate == 0.0

    def test_no_actual_positives(self):
        """FN rate should be 0 if no actual positives."""
        predictions = [False, False, False]
        ground_truth = [False, False, False]
        
        fn_rate = calculate_false_negative_rate(predictions, ground_truth)
        assert fn_rate == 0.0

    def test_empty_lists(self):
        """Error rates should be 0 for empty lists."""
        fp_rate = calculate_false_positive_rate([], [])
        fn_rate = calculate_false_negative_rate([], [])
        assert fp_rate == 0.0
        assert fn_rate == 0.0

class TestEvaluateThreshold:
    """Tests for threshold evaluation in sensitivity analysis."""

    def test_evaluate_threshold_basic(self):
        """Test basic threshold evaluation."""
        metrics_list = [
            {'condensate_density': 0.8, 'vortex_density': 0.1, 'is_metastable': False},
            {'condensate_density': 0.5, 'vortex_density': 0.1, 'is_metastable': True},
            {'condensate_density': 0.9, 'vortex_density': 0.8, 'is_metastable': True},
        ]
        
        result = evaluate_threshold(metrics_list, 0.7, 0.5)
        
        assert isinstance(result, SensitivityResult)
        assert result.density_threshold == 0.7
        assert result.vortex_threshold == 0.5
        assert 0.0 <= result.false_positive_rate <= 1.0
        assert 0.0 <= result.false_negative_rate <= 1.0
        assert 0.0 <= result.accuracy <= 1.0
        assert 0.0 <= result.f1_score <= 1.0

    def test_perfect_classification(self):
        """Test with perfect classification."""
        metrics_list = [
            {'condensate_density': 0.8, 'vortex_density': 0.1, 'is_metastable': False},
            {'condensate_density': 0.5, 'vortex_density': 0.1, 'is_metastable': True},
        ]
        
        result = evaluate_threshold(metrics_list, 0.7, 0.5)
        
        # Should have perfect accuracy
        assert result.accuracy == 1.0
        assert result.false_positive_rate == 0.0
        assert result.false_negative_rate == 0.0

class TestVortexDensityCalculation:
    """Tests for vortex density calculations."""

    def test_empty_vortices(self):
        """Density should be 0 if no vortices."""
        density = calculate_vortex_density([], 64, 10.0)
        assert density == 0.0

    def test_single_vortex(self):
        """Test single vortex density calculation."""
        vortices = [(0.0, 0.0)]
        density = calculate_vortex_density(vortices, 64, 10.0)
        # Area = 100, count = 1 -> density = 0.01
        assert density == 0.01

    def test_multiple_vortices(self):
        """Test multiple vortices."""
        vortices = [(0.0, 0.0), (1.0, 1.0), (-1.0, -1.0)]
        density = calculate_vortex_density(vortices, 64, 10.0)
        # Area = 100, count = 3 -> density = 0.03
        assert density == 0.03

class TestRadialVariance:
    """Tests for radial variance calculations."""

    def test_zero_field(self):
        """Variance should be 0 for zero field."""
        field = np.zeros((64, 64))
        variance = calculate_radial_variance(field, 64, 10.0)
        assert variance == 0.0

    def test_uniform_field(self):
        """Uniform field should have low variance."""
        field = np.ones((64, 64))
        variance = calculate_radial_variance(field, 64, 10.0)
        # Should be close to 0 (perfectly symmetric)
        assert variance < 1.0  # Allow some numerical error

class TestStructureFactorSharpness:
    """Tests for structure factor sharpness."""

    def test_zero_field(self):
        """Sharpness should be 0 for zero field."""
        field = np.zeros((64, 64))
        sharpness = calculate_structure_factor_sharpness(field)
        assert sharpness == 0.0

    def test_constant_field(self):
        """Constant field should have low sharpness (mostly DC)."""
        field = np.ones((64, 64))
        sharpness = calculate_structure_factor_sharpness(field)
        # Should be relatively low
        assert sharpness < 10.0

class TestProcessSnapshot:
    """Integration tests for snapshot processing."""

    @patch('analysis.metrics.load_array')
    @patch('analysis.metrics.detect_vortices_phase_winding')
    def test_process_snapshot_success(self, mock_detect, mock_load):
        """Test successful snapshot processing."""
        # Setup mocks
        mock_load.return_value = np.ones((64, 64))
        mock_detect.return_value = [(0.0, 0.0), (1.0, 1.0)]
        
        result = process_snapshot_file(
            'test_snapshot.npy',
            grid_config={'grid_size': 64, 'domain_size': 10.0}
        )
        
        assert result.vortex_count == 2
        assert result.vortex_density > 0.0
        assert result.condensate_density > 0.0
        assert result.radial_variance >= 0.0
        assert result.structure_factor_sharpness >= 0.0
        assert result.metastability_reason != "load_failure"

    @patch('analysis.metrics.load_array')
    def test_process_snapshot_failure(self, mock_load):
        """Test handling of load failure."""
        mock_load.return_value = None
        
        result = process_snapshot_file('test_snapshot.npy')
        
        assert result.vortex_count == 0
        assert result.condensate_density == 0.0
        assert result.is_metastable is True
        assert result.metastability_reason == "load_failure"
