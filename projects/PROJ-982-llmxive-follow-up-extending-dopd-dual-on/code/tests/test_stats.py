"""
Tests for statistical analysis module.

Verifies Mann-Whitney U test output format, direction, and integration.
"""
import pytest
import numpy as np
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

from analysis.stats import (
    load_accuracy_logs,
    calculate_effect_size,
    calculate_coefficient_of_variation,
    run_mann_whitney_test,
    analyze_generalization_results
)


class TestMannWhitneyTest:
    """Tests for Mann-Whitney U test functionality."""
    
    def test_output_format(self):
        """Verify Mann-Whitney U test output contains required fields."""
        # Create synthetic data for testing
        dopd_data = np.array([0.85, 0.87, 0.82, 0.88, 0.84])
        uniform_data = np.array([0.75, 0.78, 0.72, 0.76, 0.74])
        
        results = run_mann_whitney_test(dopd_data, uniform_data)
        
        # Verify required fields exist
        required_fields = [
            'u_statistic', 'p_value', 'effect_size',
            'n_dopd', 'n_uniform', 'mean_dopd', 'mean_uniform',
            'std_dopd', 'std_uniform', 'cv_dopd', 'cv_uniform',
            'is_significant', 'exploratory', 'alternative'
        ]
        
        for field in required_fields:
            assert field in results, f"Missing required field: {field}"
        
        # Verify types
        assert isinstance(results['u_statistic'], (int, float))
        assert isinstance(results['p_value'], (int, float))
        assert isinstance(results['effect_size'], (int, float))
        assert isinstance(results['is_significant'], bool)
        assert isinstance(results['exploratory'], bool)
        
        # Verify p-value is in valid range
        assert 0 <= results['p_value'] <= 1, "p-value must be between 0 and 1"
        
        # Verify effect size is in valid range (-1 to 1)
        assert -1 <= results['effect_size'] <= 1, "Effect size must be between -1 and 1"
    
    def test_one_tailed_direction(self):
        """Verify one-tailed test with 'greater' alternative."""
        # DOPD should have higher accuracy
        dopd_data = np.array([0.9, 0.92, 0.88, 0.91, 0.89])
        uniform_data = np.array([0.7, 0.72, 0.68, 0.71, 0.69])
        
        results = run_mann_whitney_test(dopd_data, uniform_data, alternative='greater')
        
        # With clear separation, p-value should be very small
        assert results['p_value'] < 0.05, "Expected significant result with clear separation"
        assert results['effect_size'] > 0, "Expected positive effect size when DOPD > Uniform"
        assert results['alternative'] == 'greater'
    
    def test_no_difference(self):
        """Verify test handles cases with no real difference."""
        # Same distribution
        data = np.array([0.8, 0.82, 0.78, 0.81, 0.79])
        
        results = run_mann_whitney_test(data, data)
        
        # p-value should be high (close to 0.5 for identical distributions)
        assert results['p_value'] > 0.05, "Expected non-significant result for identical data"
        assert abs(results['effect_size']) < 0.1, "Expected near-zero effect size for identical data"
    
    def test_small_sample_size(self):
        """Verify test works with minimal sample sizes."""
        dopd_data = np.array([0.9, 0.85])
        uniform_data = np.array([0.7, 0.75])
        
        results = run_mann_whitney_test(dopd_data, uniform_data)
        
        assert results['n_dopd'] == 2
        assert results['n_uniform'] == 2
        assert 'p_value' in results
        assert 'u_statistic' in results
    
    def test_empty_input_raises_error(self):
        """Verify empty input raises appropriate error."""
        with pytest.raises(ValueError):
            run_mann_whitney_test(np.array([]), np.array([0.8]))
        
        with pytest.raises(ValueError):
            run_mann_whitney_test(np.array([0.8]), np.array([]))
        
        with pytest.raises(ValueError):
            run_mann_whitney_test(np.array([]), np.array([]))

class TestEffectSizeCalculation:
    """Tests for effect size calculation."""
    
    def test_effect_size_range(self):
        """Verify effect size is within valid bounds."""
        # Maximum positive effect
        u_stat = 0
        effect = calculate_effect_size(u_stat, 10, 10)
        assert effect == 1.0
        
        # Maximum negative effect (U = n1*n2)
        u_stat = 100
        effect = calculate_effect_size(u_stat, 10, 10)
        assert effect == -1.0
        
        # Zero effect (U = n1*n2/2)
        u_stat = 50
        effect = calculate_effect_size(u_stat, 10, 10)
        assert abs(effect) < 0.01
    
    def test_zero_sample_size(self):
        """Verify handling of zero sample size."""
        effect = calculate_effect_size(0, 0, 10)
        assert effect == 0.0
        
        effect = calculate_effect_size(0, 10, 0)
        assert effect == 0.0

class TestCoefficientOfVariation:
    """Tests for CV calculation."""
    
    def test_cv_calculation(self):
        """Verify CV is calculated correctly."""
        data = np.array([10, 12, 11, 13, 9])
        mean_val = np.mean(data)
        std_val = np.std(data)
        expected_cv = (std_val / mean_val) * 100
        
        actual_cv = calculate_coefficient_of_variation(data)
        assert abs(actual_cv - expected_cv) < 0.001
    
    def test_zero_mean_handling(self):
        """Verify handling of zero mean."""
        data = np.array([0, 0, 0])
        cv = calculate_coefficient_of_variation(data)
        assert cv == 0.0
    
    def test_empty_array(self):
        """Verify handling of empty array."""
        data = np.array([])
        cv = calculate_coefficient_of_variation(data)
        assert cv == 0.0

class TestLoadAccuracyLogs:
    """Tests for loading accuracy logs from files."""
    
    def test_load_from_json_files(self):
        """Verify loading from JSON log files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test log files
            for i in range(3):
                log_data = {
                    'accuracies': [0.7, 0.75, 0.8, 0.85, 0.9],
                    'seed': i
                }
                filepath = os.path.join(tmpdir, f"run_{i}_dopd_accuracy.json")
                with open(filepath, 'w') as f:
                    json.dump(log_data, f)
            
            # Load and verify
            accuracies = load_accuracy_logs(tmpdir, 'dopd')
            assert len(accuracies) == 3
            assert np.allclose(accuracies, [0.9, 0.9, 0.9])  # Last value from each
    
    def test_load_final_accuracy_field(self):
        """Verify loading from final_accuracy field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_data = {
                'final_accuracy': 0.85,
                'seed': 42
            }
            filepath = os.path.join(tmpdir, "test_uniform_accuracy.json")
            with open(filepath, 'w') as f:
                json.dump(log_data, f)
            
            accuracies = load_accuracy_logs(tmpdir, 'uniform')
            assert len(accuracies) == 1
            assert accuracies[0] == 0.85
    
    def test_no_files_raises_error(self):
        """Verify error when no files found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                load_accuracy_logs(tmpdir, 'dopd')
    
    def test_malformed_json_raises_error(self):
        """Verify error for malformed JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_dopd_accuracy.json")
            with open(filepath, 'w') as f:
                f.write("{invalid json}")
            
            with pytest.raises(ValueError):
                load_accuracy_logs(tmpdir, 'dopd')

class TestGeneralizationAnalysis:
    """Integration tests for full analysis pipeline."""
    
    def test_full_analysis_pipeline(self):
        """Verify complete analysis from log loading to result generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create DOPD logs
            for i in range(5):
                log_data = {
                    'accuracies': [0.7 + i * 0.02, 0.75 + i * 0.02, 0.8 + i * 0.02, 0.85 + i * 0.02],
                    'seed': i
                }
                filepath = os.path.join(tmpdir, f"dopd_run_{i}_accuracy.json")
                with open(filepath, 'w') as f:
                    json.dump(log_data, f)
            
            # Create Uniform logs (lower performance)
            for i in range(5):
                log_data = {
                    'accuracies': [0.6 + i * 0.02, 0.65 + i * 0.02, 0.7 + i * 0.02, 0.75 + i * 0.02],
                    'seed': i
                }
                filepath = os.path.join(tmpdir, f"uniform_run_{i}_accuracy.json")
                with open(filepath, 'w') as f:
                    json.dump(log_data, f)
            
            # Run analysis
            results = analyze_generalization_results(tmpdir)
            
            # Verify results structure
            assert 'p_value' in results
            assert 'effect_size' in results
            assert 'conclusion' in results
            assert 'is_significant' in results
            assert results['n_dopd'] == 5
            assert results['n_uniform'] == 5
            
            # Verify statistical expectations (DOPD should outperform)
            assert results['mean_dopd'] > results['mean_uniform']
            assert results['effect_size'] > 0
            
            # Verify output path functionality
            output_path = os.path.join(tmpdir, "analysis_results.json")
            results_with_save = analyze_generalization_results(tmpdir, output_path)
            
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                saved_results = json.load(f)
                assert 'p_value' in saved_results
                assert saved_results['p_value'] == results_with_save['p_value']
    
    def test_seeds_separation_verification(self):
        """Verify that analysis can distinguish between different seed runs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create logs with explicit seed metadata
            for seed in [1, 2, 3]:
                dopd_data = {'accuracies': [0.8, 0.85, 0.9], 'seed': seed}
                filepath = os.path.join(tmpdir, f"dopd_seed_{seed}_accuracy.json")
                with open(filepath, 'w') as f:
                    json.dump(dupd_data, f)
            
            for seed in [4, 5, 6]:
                uniform_data = {'accuracies': [0.7, 0.75, 0.8], 'seed': seed}
                filepath = os.path.join(tmpdir, f"uniform_seed_{seed}_accuracy.json")
                with open(filepath, 'w') as f:
                    json.dump(uniform_data, f)
            
            results = analyze_generalization_results(tmpdir)
            
            # Should have 3 samples from each regime
            assert results['n_dopd'] == 3
            assert results['n_uniform'] == 3
            assert results['n_dopd'] + results['n_uniform'] == 6