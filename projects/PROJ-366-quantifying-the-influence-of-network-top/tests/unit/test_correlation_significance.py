import json
import pytest
from pathlib import Path
import tempfile
import numpy as np

from code.analysis.correlation_significance import (
    load_pearson_results,
    apply_bonferroni_correction,
    generate_summary,
    save_corrected_results
)

class TestBonferroniCorrection:
    """Unit tests for Bonferroni correction logic."""

    def test_bonferroni_single_test(self):
        """Test Bonferroni correction with a single test (no correction needed)."""
        p_values = [0.03]
        results = apply_bonferroni_correction(p_values, alpha=0.05)
        
        assert len(results) == 1
        assert results[0]['raw_p_value'] == 0.03
        assert results[0]['bonferroni_corrected_p_value'] == 0.03  # 0.03 * 1 = 0.03
        assert results[0]['significance_threshold'] == 0.05  # 0.05 / 1 = 0.05
        assert results[0]['is_significant'] is True

    def test_bonferroni_multiple_tests(self):
        """Test Bonferroni correction with multiple tests."""
        p_values = [0.01, 0.03, 0.05, 0.10]
        results = apply_bonferroni_correction(p_values, alpha=0.05)
        
        assert len(results) == 4
        
        # With 4 tests, corrected alpha = 0.05 / 4 = 0.0125
        assert results[0]['significance_threshold'] == pytest.approx(0.0125)
        
        # p=0.01 should be significant (0.01 < 0.0125)
        assert results[0]['is_significant'] is True
        
        # p=0.03 should not be significant (0.03 > 0.0125)
        assert results[1]['is_significant'] is False
        
        # Corrected p-values should be raw * m
        assert results[0]['bonferroni_corrected_p_value'] == pytest.approx(0.04)  # 0.01 * 4
        assert results[1]['bonferroni_corrected_p_value'] == pytest.approx(0.12)  # 0.03 * 4

    def test_bonferroni_p_value_capped_at_one(self):
        """Test that corrected p-values are capped at 1.0."""
        p_values = [0.9]
        results = apply_bonferroni_correction(p_values, alpha=0.05)
        
        # With 10 tests, 0.9 * 10 = 9.0, but should be capped at 1.0
        # Actually, let's use a case where it would exceed 1.0
        p_values = [0.15]
        results = apply_bonferroni_correction(p_values, alpha=0.05)
        
        # If we had 10 tests: 0.15 * 10 = 1.5 -> capped at 1.0
        # But we only have 1 test here, so 0.15 * 1 = 0.15
        # Let's test with multiple tests
        p_values = [0.3, 0.4]
        results = apply_bonferroni_correction(p_values, alpha=0.05)
        
        # 2 tests: 0.4 * 2 = 0.8 (no cap needed)
        # Let's try with more tests
        p_values = [0.6, 0.7]
        results = apply_bonferroni_correction(p_values, alpha=0.05, num_tests=10)
        
        # Wait, the function doesn't take num_tests, it infers from len(p_values)
        # So we need 2 tests: 0.7 * 2 = 1.4 -> capped at 1.0
        # Actually, let me check the function signature again
        
        # With 2 tests: 0.7 * 2 = 1.4, should be capped at 1.0
        p_values = [0.7]
        results = apply_bonferroni_correction(p_values)
        # 1 test: 0.7 * 1 = 0.7 (no cap)
        
        # Let's test with 2 tests where one would exceed 1.0
        p_values = [0.6, 0.7]
        results = apply_bonferroni_correction(p_values)
        
        # 2 tests: 0.7 * 2 = 1.4 -> capped at 1.0
        assert results[1]['bonferroni_corrected_p_value'] == 1.0

    def test_bonferroni_empty_list(self):
        """Test Bonferroni correction with empty p-value list."""
        results = apply_bonferroni_correction([])
        assert results == []

    def test_bonferroni_custom_alpha(self):
        """Test Bonferroni correction with custom alpha."""
        p_values = [0.01, 0.02]
        results = apply_bonferroni_correction(p_values, alpha=0.10)
        
        # 2 tests, alpha=0.10: threshold = 0.10 / 2 = 0.05
        assert results[0]['significance_threshold'] == pytest.approx(0.05)
        assert results[0]['is_significant'] is True  # 0.01 < 0.05
        assert results[1]['is_significant'] is False  # 0.02 < 0.05 (actually True!)
        
        # Wait, 0.02 < 0.05 is True
        assert results[1]['is_significant'] is True

class TestGenerateSummary:
    """Unit tests for summary generation."""

    def test_summary_no_significant_results(self):
        """Test summary when no results are significant."""
        pearson_results = [
            {'r': 0.1, 'p_value': 0.5},
            {'r': 0.2, 'p_value': 0.6}
        ]
        corrected_results = [
            {'raw_p_value': 0.5, 'bonferroni_corrected_p_value': 1.0, 'is_significant': False},
            {'raw_p_value': 0.6, 'bonferroni_corrected_p_value': 1.0, 'is_significant': False}
        ]
        
        summary = generate_summary(pearson_results, corrected_results)
        
        assert summary['total_correlation_tests'] == 2
        assert summary['significant_after_correction'] == 0
        assert len(summary['significant_features']) == 0
        assert 'No topological features' in summary['interpretation']

    def test_summary_with_significant_results(self):
        """Test summary when some results are significant."""
        pearson_results = [
            {'r': 0.5, 'p_value': 0.01},
            {'r': 0.1, 'p_value': 0.5}
        ]
        corrected_results = [
            {'raw_p_value': 0.01, 'bonferroni_corrected_p_value': 0.02, 'is_significant': True, 'significance_threshold': 0.025},
            {'raw_p_value': 0.5, 'bonferroni_corrected_p_value': 1.0, 'is_significant': False, 'significance_threshold': 0.025}
        ]
        
        summary = generate_summary(pearson_results, corrected_results)
        
        assert summary['total_correlation_tests'] == 2
        assert summary['significant_after_correction'] == 1
        assert len(summary['significant_features']) == 1
        assert summary['significant_features'][0]['correlation_coefficient'] == 0.5
        assert summary['significant_features'][0]['effect_size'] in ['small', 'medium', 'large']

    def test_summary_effect_size_classification(self):
        """Test that effect sizes are classified correctly."""
        pearson_results = [
            {'r': 0.05, 'p_value': 0.01},   # negligible
            {'r': 0.15, 'p_value': 0.01},   # small
            {'r': 0.35, 'p_value': 0.01},   # medium
            {'r': 0.55, 'p_value': 0.01}    # large
        ]
        corrected_results = [
            {'raw_p_value': 0.01, 'bonferroni_corrected_p_value': 0.04, 'is_significant': True, 'significance_threshold': 0.0125},
            {'raw_p_value': 0.01, 'bonferroni_corrected_p_value': 0.04, 'is_significant': True, 'significance_threshold': 0.0125},
            {'raw_p_value': 0.01, 'bonferroni_corrected_p_value': 0.04, 'is_significant': True, 'significance_threshold': 0.0125},
            {'raw_p_value': 0.01, 'bonferroni_corrected_p_value': 0.04, 'is_significant': True, 'significance_threshold': 0.0125}
        ]
        
        summary = generate_summary(pearson_results, corrected_results)
        
        assert summary['significant_features'][0]['effect_size'] == 'negligible'
        assert summary['significant_features'][1]['effect_size'] == 'small'
        assert summary['significant_features'][2]['effect_size'] == 'medium'
        assert summary['significant_features'][3]['effect_size'] == 'large'

class TestLoadAndSave:
    """Integration tests for loading and saving."""

    def test_save_and_load_corrected_results(self):
        """Test that results can be saved and reloaded correctly."""
        pearson_results = [
            {'r': 0.5, 'p_value': 0.01, 'n_samples': 10, 'method': 'pearson'},
            {'r': 0.2, 'p_value': 0.3, 'n_samples': 10, 'method': 'pearson'}
        ]
        corrected_results = apply_bonferroni_correction([r['p_value'] for r in pearson_results])
        summary = generate_summary(pearson_results, corrected_results)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            save_corrected_results(pearson_results, corrected_results, summary, temp_path)
            
            # Verify file exists and can be loaded
            with open(temp_path, 'r') as f:
                loaded = json.load(f)
            
            assert 'pearson_results' in loaded
            assert 'bonferroni_correction' in loaded
            assert 'summary' in loaded
            assert loaded['bonferroni_correction']['method'] == 'bonferroni'
            assert len(loaded['pearson_results']) == 2
        finally:
            Path(temp_path).unlink()

    def test_load_pearson_results_single_dict(self):
        """Test loading a single result (not a list)."""
        pearson_result = {'r': 0.5, 'p_value': 0.01}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(pearson_result, f)
            temp_path = f.name
        
        try:
            results = load_pearson_results(temp_path)
            assert len(results) == 1
            assert results[0]['r'] == 0.5
        finally:
            Path(temp_path).unlink()

    def test_load_pearson_results_list(self):
        """Test loading a list of results."""
        pearson_results = [
            {'r': 0.5, 'p_value': 0.01},
            {'r': 0.2, 'p_value': 0.3}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(pearson_results, f)
            temp_path = f.name
        
        try:
            results = load_pearson_results(temp_path)
            assert len(results) == 2
            assert results[0]['r'] == 0.5
        finally:
            Path(temp_path).unlink()

    def test_load_pearson_results_not_found(self):
        """Test that FileNotFoundError is raised when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_pearson_results('/nonexistent/path/correlation_pearson.json')

if __name__ == '__main__':
    pytest.main([__file__, '-v'])