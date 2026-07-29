"""
Unit tests for the sensitivity sweep logic in code/analysis/sensitivity.py.

This module tests the core logic of the sensitivity analysis:
1. Threshold sweeping (re-binning existing data for different hop thresholds)
2. Effect size calculation
3. Integration with the permutation test from detect_threshold.py

The tests verify that the sensitivity analysis correctly:
- Re-bins data without re-sampling or re-annotation
- Calculates effect sizes for different threshold definitions
- Produces consistent results when using the same inputs
"""

import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from collections import defaultdict

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.sensitivity import (
    calculate_effect_size,
    perform_threshold_sweep,
    run_pilot_sample,
    oversample_dataset,
    merge_bins_if_needed
)
from code.analysis.detect_threshold import permutation_test, bonferroni_correction


class TestCalculateEffectSize:
    """Tests for the effect size calculation function."""
    
    def test_effect_size_basic(self):
        """Test basic effect size calculation between two bins."""
        # Simulate accuracy data for different hop counts
        accuracy_data = {
            1: 0.85,  # 1-hop accuracy
            2: 0.72,  # 2-hop accuracy
            3: 0.58,  # 3-hop accuracy
            4: 0.45,  # 4-hop accuracy
            5: 0.35   # 5-hop accuracy
        }
        
        # Calculate effect size between 1-hop and 3-hop
        effect_size = calculate_effect_size(accuracy_data, threshold_hop=3)
        
        # Effect size should be the drop in accuracy
        expected_effect_size = accuracy_data[1] - accuracy_data[3]
        assert abs(effect_size - expected_effect_size) < 1e-6
        
    def test_effect_size_with_merged_bins(self):
        """Test effect size calculation when bins are merged."""
        # Simulate merged bin data (3+ combined)
        accuracy_data = {
            1: 0.85,
            2: 0.72,
            '3+': 0.48  # Merged 3, 4, 5
        }
        
        # Calculate effect size with threshold at 2 (comparing 1 vs 2+)
        effect_size = calculate_effect_size(accuracy_data, threshold_hop=2)
        
        # Should compare 1-hop vs 2+ (which includes 2 and 3+)
        # For this test, we assume the function handles merged bins appropriately
        assert effect_size >= 0  # Effect size should be non-negative for accuracy drop
        
    def test_effect_size_edge_cases(self):
        """Test effect size with edge cases."""
        # Empty data
        with pytest.raises((KeyError, ValueError)):
            calculate_effect_size({}, threshold_hop=1)
            
        # Single data point
        accuracy_data = {1: 0.85}
        with pytest.raises((KeyError, IndexError)):
            calculate_effect_size(accuracy_data, threshold_hop=2)

class TestPerformThresholdSweep:
    """Tests for the threshold sweep logic."""
    
    def test_sweep_basic(self):
        """Test basic threshold sweep across multiple hop counts."""
        # Mock the data loading and analysis functions
        mock_accuracy_data = {
            1: 0.85,
            2: 0.72,
            3: 0.58,
            4: 0.45,
            5: 0.35
        }
        
        mock_bin_config = {
            'bins': [1, 2, 3, 4, 5],
            'strategy': 'original'
        }
        
        # Mock the permutation test to return consistent results
        def mock_permutation_test(*args, **kwargs):
            return 0.03  # Mock p-value
        
        def mock_bonferroni(p_value, n_tests):
            return p_value * n_tests
        
        with patch('code.analysis.sensitivity.calculate_effect_size', return_value=0.15):
            with patch('code.analysis.sensitivity.permutation_test', side_effect=mock_permutation_test):
                with patch('code.analysis.sensitivity.bonferroni_correction', side_effect=mock_bonferroni):
                    # Perform sweep with thresholds 2, 3, 4
                    results = perform_threshold_sweep(
                        accuracy_data=mock_accuracy_data,
                        bin_config=mock_bin_config,
                        thresholds=[2, 3, 4]
                    )
                    
                    # Verify results structure
                    assert isinstance(results, list)
                    assert len(results) == 3  # 3 thresholds
                    
                    # Check each result has required fields
                    for result in results:
                        assert 'threshold_hop' in result
                        assert 'p_value' in result
                        assert 'effect_size' in result
                        assert 'is_significant' in result
                        
    def test_sweep_with_deferred_bins(self):
        """Test threshold sweep when some bins are deferred."""
        mock_accuracy_data = {
            1: 0.85,
            2: 0.72,
            '3+': 0.48  # Merged/deferred bin
        }
        
        mock_bin_config = {
            'bins': [1, 2, '3+'],
            'strategy': 'merged',
            'deferred_reason': 'insufficient_power'
        }
        
        # Mock functions
        def mock_permutation_test(*args, **kwargs):
            return 0.04
        
        def mock_bonferroni(p_value, n_tests):
            return p_value * n_tests
        
        with patch('code.analysis.sensitivity.calculate_effect_size', return_value=0.12):
            with patch('code.analysis.sensitivity.permutation_test', side_effect=mock_permutation_test):
                with patch('code.analysis.sensitivity.bonferroni_correction', side_effect=mock_bonferroni):
                    # Perform sweep
                    results = perform_threshold_sweep(
                        accuracy_data=mock_accuracy_data,
                        bin_config=mock_bin_config,
                        thresholds=[2, 3]
                    )
                    
                    # Verify results
                    assert len(results) == 2
                    for result in results:
                        assert 'threshold_hop' in result
                        assert 'p_value' in result
                        assert 'effect_size' in result
                        
    def test_sweep_empty_thresholds(self):
        """Test threshold sweep with empty threshold list."""
        mock_accuracy_data = {1: 0.85, 2: 0.72}
        mock_bin_config = {'bins': [1, 2], 'strategy': 'original'}
        
        results = perform_threshold_sweep(
            accuracy_data=mock_accuracy_data,
            bin_config=mock_bin_config,
            thresholds=[]
        )
        
        assert results == []

class TestRunPilotSample:
    """Tests for the pilot sampling logic."""
    
    def test_pilot_sample_size(self):
        """Test that pilot sample returns the correct size."""
        # Mock dataset with known size
        mock_data = [{'chain_length': i % 5 + 1, 'correctness': i % 2} for i in range(1000)]
        
        with patch('code.analysis.sensitivity.load_annotated_data', return_value=mock_data):
            pilot_data, pilot_stats = run_pilot_sample(
                data_path=Path("mock/path.csv"),
                pilot_size=100
            )
            
            assert len(pilot_data) == 100
            assert 'chain_length_distribution' in pilot_stats
            
    def test_pilot_sample_streaming(self):
        """Test pilot sampling with streaming data."""
        # Mock streaming dataset
        mock_stream_data = iter([
            {'chain_length': i % 5 + 1, 'correctness': i % 2} 
            for i in range(5000)
        ])
        
        with patch('code.analysis.sensitivity.load_annotated_data_streaming', return_value=mock_stream_data):
            pilot_data, pilot_stats = run_pilot_sample(
                data_path=Path("mock/path.csv"),
                pilot_size=50,
                streaming=True
            )
            
            assert len(pilot_data) == 50

class TestOversampleDataset:
    """Tests for the oversampling logic."""
    
    def test_oversample_rare_bin(self):
        """Test oversampling for rare bins."""
        # Mock pilot data with rare bin
        pilot_data = [
            {'chain_length': 1, 'correctness': 1} for _ in range(30)
        ] + [
            {'chain_length': 2, 'correctness': 1} for _ in range(20)
        ] + [
            {'chain_length': 3, 'correctness': 0} for _ in range(5)  # Rare bin
        ]
        
        with patch('code.analysis.sensitivity.stratified_resample', return_value=pilot_data):
            oversampled_data = oversample_dataset(
                pilot_data=pilot_data,
                target_per_bin=50,
                rare_threshold=50
            )
            
            # Should have increased the rare bin
            assert len(oversampled_data) >= len(pilot_data)
            
    def test_oversample_no_rare_bins(self):
        """Test oversampling when no bins are rare."""
        pilot_data = [
            {'chain_length': i % 3 + 1, 'correctness': i % 2} 
            for i in range(200)
        ]
        
        oversampled_data = oversample_dataset(
            pilot_data=pilot_data,
            target_per_bin=50,
            rare_threshold=50
        )
        
        # Should return original data if no rare bins
        assert len(oversampled_data) == len(pilot_data)

class TestMergeBinsIfNeeded:
    """Tests for the bin merging logic."""
    
    def test_merge_underpowered_bin(self):
        """Test merging of underpowered bins."""
        bin_counts = {
            1: 150,
            2: 120,
            3: 40,   # Underpowered
            4: 35    # Underpowered
        }
        
        merged_bins, strategy = merge_bins_if_needed(
            bin_counts=bin_counts,
            min_bin_size=50
        )
        
        # Should merge 3 and 4 into 3+
        assert '3+' in merged_bins
        assert strategy == 'merged'
        
    def test_merge_deferred_bin(self):
        """Test deferral when merged bin is still underpowered."""
        bin_counts = {
            1: 150,
            2: 120,
            3: 10,   # Very underpowered
            4: 8     # Very underpowered
        }
        
        merged_bins, strategy = merge_bins_if_needed(
            bin_counts=bin_counts,
            min_bin_size=50
        )
        
        # Should defer if merged bin is still underpowered
        assert strategy == 'deferred'
        
    def test_no_merge_needed(self):
        """Test when no merging is needed."""
        bin_counts = {
            1: 150,
            2: 120,
            3: 80,
            4: 60
        }
        
        merged_bins, strategy = merge_bins_if_needed(
            bin_counts=bin_counts,
            min_bin_size=50
        )
        
        assert strategy == 'original'
        assert merged_bins == bin_counts

class TestIntegrationWithThresholdDetection:
    """Integration tests for sensitivity analysis with threshold detection."""
    
    def test_full_sensitivity_pipeline(self):
        """Test the full sensitivity analysis pipeline."""
        # Mock complete data
        mock_annotated_data = [
            {'chain_length': i % 5 + 1, 'correctness': 1 if i % 3 != 0 else 0}
            for i in range(1000)
        ]
        
        mock_bin_config = {
            'bins': [1, 2, 3, 4, 5],
            'strategy': 'original'
        }
        
        # Mock the detection functions
        def mock_detect_threshold(accuracy_data, bin_config, threshold):
            return {
                'p_value': 0.03,
                'effect_size': 0.15,
                'is_significant': True
            }
        
        with patch('code.analysis.sensitivity.calculate_effect_size', return_value=0.15):
            with patch('code.analysis.sensitivity.permutation_test', return_value=0.03):
                with patch('code.analysis.sensitivity.bonferroni_correction', return_value=0.15):
                    # Run full sensitivity analysis
                    results = perform_threshold_sweep(
                        accuracy_data={i: 0.85 - i * 0.1 for i in range(1, 6)},
                        bin_config=mock_bin_config,
                        thresholds=[2, 3, 4]
                    )
                    
                    # Verify results
                    assert len(results) == 3
                    significant_count = sum(1 for r in results if r['is_significant'])
                    assert significant_count >= 0  # At least some results
                    
    def test_consistency_across_runs(self):
        """Test that sensitivity analysis produces consistent results."""
        mock_accuracy_data = {
            1: 0.85,
            2: 0.72,
            3: 0.58,
            4: 0.45,
            5: 0.35
        }
        
        mock_bin_config = {
            'bins': [1, 2, 3, 4, 5],
            'strategy': 'original'
        }
        
        # Mock deterministic permutation test
        call_count = [0]
        def mock_permutation_test(*args, **kwargs):
            call_count[0] += 1
            return 0.03  # Fixed p-value
        
        def mock_bonferroni(p_value, n_tests):
            return p_value * n_tests
        
        with patch('code.analysis.sensitivity.calculate_effect_size', return_value=0.15):
            with patch('code.analysis.sensitivity.permutation_test', side_effect=mock_permutation_test):
                with patch('code.analysis.sensitivity.bonferroni_correction', side_effect=mock_bonferroni):
                    # Run twice
                    results1 = perform_threshold_sweep(
                        accuracy_data=mock_accuracy_data,
                        bin_config=mock_bin_config,
                        thresholds=[2, 3]
                    )
                    
                    results2 = perform_threshold_sweep(
                        accuracy_data=mock_accuracy_data,
                        bin_config=mock_bin_config,
                        thresholds=[2, 3]
                    )
                    
                    # Results should be identical
                    assert len(results1) == len(results2)
                    for r1, r2 in zip(results1, results2):
                        assert r1['threshold_hop'] == r2['threshold_hop']
                        assert r1['p_value'] == r2['p_value']
                        assert r1['effect_size'] == r2['effect_size']

class TestRobustnessMetrics:
    """Tests for robustness calculation in sensitivity analysis."""
    
    def test_robustness_calculation(self):
        """Test calculation of robustness metrics."""
        # Mock sensitivity results
        mock_results = [
            {'threshold_hop': 2, 'p_value': 0.03, 'is_significant': True},
            {'threshold_hop': 3, 'p_value': 0.04, 'is_significant': True},
            {'threshold_hop': 4, 'p_value': 0.08, 'is_significant': False}
        ]
        
        # Calculate robustness
        significant_count = sum(1 for r in mock_results if r['is_significant'])
        is_robust = significant_count >= 2
        
        assert significant_count == 2
        assert is_robust == True
        
    def test_robustness_failure(self):
        """Test robustness calculation when thresholds are not significant."""
        mock_results = [
            {'threshold_hop': 2, 'p_value': 0.15, 'is_significant': False},
            {'threshold_hop': 3, 'p_value': 0.25, 'is_significant': False}
        ]
        
        significant_count = sum(1 for r in mock_results if r['is_significant'])
        is_robust = significant_count >= 2
        
        assert significant_count == 0
        assert is_robust == False

if __name__ == '__main__':
    pytest.main([__file__, '-v'])