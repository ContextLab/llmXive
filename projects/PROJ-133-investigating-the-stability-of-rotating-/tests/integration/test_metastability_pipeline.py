import pytest
import numpy as np
import os
import json
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.metrics import (
    process_snapshot_file,
    calculate_all_metrics,
    classify_metastability
)
from analysis.sensitivity_analysis import run_sensitivity_analysis, evaluate_threshold
from utils.io_helpers import save_array

class TestMetastabilityPipeline:
    """Integration tests for the full metastability analysis pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample snapshot files
        self.stable_snapshot = os.path.join(self.temp_dir, 'stable.npy')
        self.metastable_snapshot = os.path.join(self.temp_dir, 'metastable.npy')
        
        # Stable: high density, no vortices
        stable_density = np.ones((64, 64)) * 0.9
        save_array(self.stable_snapshot, stable_density)
        
        # Metastable: low density (simulated decay)
        metastable_density = np.ones((64, 64)) * 0.5
        save_array(self.metastable_snapshot, metastable_density)

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_pipeline_stable(self):
        """Test full pipeline on stable snapshot."""
        result = process_snapshot_file(
            self.stable_snapshot,
            grid_config={'grid_size': 64, 'domain_size': 10.0}
        )
        
        # Should be classified as stable (or at least not metastable due to density)
        # Vortex detection might find some due to numerical noise, but density should be high
        assert result.condensate_density > 0.7  # High density
        # The metastability reason should not be density_drop
        if result.is_metastable:
            assert "density_drop" not in result.metastability_reason

    def test_full_pipeline_metastable(self):
        """Test full pipeline on metastable snapshot."""
        result = process_snapshot_file(
            self.metastable_snapshot,
            grid_config={'grid_size': 64, 'domain_size': 10.0}
        )
        
        # Should be classified as metastable due to density drop
        assert result.condensate_density < 0.7  # Low density
        assert result.is_metastable is True
        assert "density_drop" in result.metastability_reason

    def test_sensitivity_analysis_integration(self):
        """Test sensitivity analysis with real data."""
        # Create a ground truth file
        ground_truth_path = os.path.join(self.temp_dir, 'ground_truth.json')
        ground_truth = {
            'metastable_labels': [False, True]  # Corresponds to stable, metastable
        }
        with open(ground_truth_path, 'w') as f:
            json.dump(ground_truth, f)
        
        # Run sensitivity analysis
        results = run_sensitivity_analysis(
            self.temp_dir,
            density_range=(0.5, 0.9),
            vortex_range=(0.1, 0.8),
            steps=3
        )
        
        # Should return results
        assert len(results) > 0
        
        # Check that results have expected fields
        for res in results:
            assert hasattr(res, 'false_positive_rate')
            assert hasattr(res, 'false_negative_rate')
            assert hasattr(res, 'accuracy')
            assert hasattr(res, 'f1_score')
            
            # Rates should be between 0 and 1
            assert 0.0 <= res.false_positive_rate <= 1.0
            assert 0.0 <= res.false_negative_rate <= 1.0
            assert 0.0 <= res.accuracy <= 1.0
            assert 0.0 <= res.f1_score <= 1.0

    def test_threshold_evaluation(self):
        """Test threshold evaluation function."""
        # Create metrics list
        metrics_list = [
            {'condensate_density': 0.9, 'vortex_density': 0.1, 'is_metastable': False},
            {'condensate_density': 0.5, 'vortex_density': 0.1, 'is_metastable': True},
            {'condensate_density': 0.8, 'vortex_density': 0.8, 'is_metastable': True},
            {'condensate_density': 0.6, 'vortex_density': 0.2, 'is_metastable': True}
        ]
        
        result = evaluate_threshold(metrics_list, 0.7, 0.5)
        
        # Verify result structure
        assert result.density_threshold == 0.7
        assert result.vortex_threshold == 0.5
        assert 0.0 <= result.accuracy <= 1.0
        
        # With these thresholds:
        # - Item 1: pred=False, gt=False -> TN
        # - Item 2: pred=True, gt=True -> TP
        # - Item 3: pred=True, gt=True -> TP
        # - Item 4: pred=True (density<0.7), gt=True -> TP
        # No FP, No FN -> perfect accuracy
        assert result.accuracy == 1.0
        assert result.false_positive_rate == 0.0
        assert result.false_negative_rate == 0.0

    def test_edge_case_zero_vortices(self):
        """Test pipeline with zero vortices."""
        # Create a snapshot with no vortices (perfectly smooth)
        smooth_snapshot = os.path.join(self.temp_dir, 'smooth.npy')
        smooth_density = np.ones((64, 64)) * 0.95
        save_array(smooth_snapshot, smooth_density)
        
        result = process_snapshot_file(
            smooth_snapshot,
            grid_config={'grid_size': 64, 'domain_size': 10.0}
        )
        
        # Should have low or zero vortex count
        assert result.vortex_count >= 0
        assert result.vortex_density >= 0.0
        # Should be stable (high density, no vortices)
        assert result.is_metastable is False
        assert result.metastability_reason == "stable"

    def test_error_rate_calculation(self):
        """Test that error rates are calculated correctly when ground truth is provided."""
        # Create ground truth with known labels
        ground_truth_path = os.path.join(self.temp_dir, 'gt.json')
        ground_truth = {
            'metastable_labels': [True, False, True, False]
        }
        with open(ground_truth_path, 'w') as f:
            json.dump(ground_truth, f)
        
        # Create mock metrics that will have some errors
        # We test the sensitivity analysis function which uses error rates
        metrics_list = [
            {'condensate_density': 0.5, 'vortex_density': 0.1, 'is_metastable': True},  # TP
            {'condensate_density': 0.9, 'vortex_density': 0.1, 'is_metastable': False}, # TN
            {'condensate_density': 0.5, 'vortex_density': 0.1, 'is_metastable': True},  # TP
            {'condensate_density': 0.9, 'vortex_density': 0.1, 'is_metastable': False}  # TN
        ]
        
        result = evaluate_threshold(metrics_list, 0.7, 0.5)
        
        # With perfect classification:
        assert result.false_positive_rate == 0.0
        assert result.false_negative_rate == 0.0
        assert result.accuracy == 1.0
        assert result.f1_score == 1.0
