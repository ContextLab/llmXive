"""
Unit tests for statistics module.

Tests pass@1 calculation, McNemar's test, Bonferroni correction,
and other statistical functions.
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.statistics import (
    calculate_pass_at_1,
    calculate_pass_rates_by_group,
    build_contingency_table,
    perform_mcnemar_test,
    apply_bonferroni_correction,
    run_mixed_effects_logistic_regression,
    analyze_sensitivity_to_thresholds,
    generate_statistics_report,
    load_results_from_json
)

@pytest.fixture
def sample_results():
    """Sample execution results for testing."""
    return [
        {'task_id': 'task1', 'perturbation_type': 'original', 'status': 'pass'},
        {'task_id': 'task1', 'perturbation_type': 'synonym', 'status': 'pass'},
        {'task_id': 'task2', 'perturbation_type': 'original', 'status': 'pass'},
        {'task_id': 'task2', 'perturbation_type': 'synonym', 'status': 'fail'},
        {'task_id': 'task3', 'perturbation_type': 'original', 'status': 'fail'},
        {'task_id': 'task3', 'perturbation_type': 'synonym', 'status': 'fail'},
        {'task_id': 'task4', 'perturbation_type': 'original', 'status': 'pass'},
        {'task_id': 'task4', 'perturbation_type': 'synonym', 'status': 'pass'},
        {'task_id': 'task5', 'perturbation_type': 'original', 'status': 'pass'},
        {'task_id': 'task5', 'perturbation_type': 'typo', 'status': 'fail'},
    ]

@pytest.fixture
def temp_results_file(tmp_path):
    """Create a temporary results file."""
    results = [
        {'task_id': 't1', 'perturbation_type': 'original', 'status': 'pass'},
        {'task_id': 't1', 'perturbation_type': 'synonym', 'status': 'pass'},
        {'task_id': 't2', 'perturbation_type': 'original', 'status': 'pass'},
        {'task_id': 't2', 'perturbation_type': 'synonym', 'status': 'fail'},
    ]
    file_path = tmp_path / "results.json"
    with open(file_path, 'w') as f:
        json.dump(results, f)
    return str(file_path)

class TestPassAt1Calculation:
    """Tests for pass@1 calculation functions."""

    def test_calculate_pass_at_1_all_passed(self):
        """Test pass rate when all results passed."""
        results = [
            {'task_id': 't1', 'status': 'pass'},
            {'task_id': 't2', 'status': 'pass'},
            {'task_id': 't3', 'status': 'pass'},
        ]
        rate, passed, total = calculate_pass_at_1(results)
        assert rate == 1.0
        assert passed == 3
        assert total == 3

    def test_calculate_pass_at_1_all_failed(self):
        """Test pass rate when all results failed."""
        results = [
            {'task_id': 't1', 'status': 'fail'},
            {'task_id': 't2', 'status': 'fail'},
        ]
        rate, passed, total = calculate_pass_at_1(results)
        assert rate == 0.0
        assert passed == 0
        assert total == 2

    def test_calculate_pass_at_1_mixed(self):
        """Test pass rate with mixed results."""
        results = [
            {'task_id': 't1', 'status': 'pass'},
            {'task_id': 't2', 'status': 'fail'},
            {'task_id': 't3', 'status': 'pass'},
            {'task_id': 't4', 'status': 'fail'},
            {'task_id': 't5', 'status': 'pass'},
        ]
        rate, passed, total = calculate_pass_at_1(results)
        assert rate == 0.6
        assert passed == 3
        assert total == 5

    def test_calculate_pass_at_1_empty(self):
        """Test pass rate with empty results."""
        rate, passed, total = calculate_pass_at_1([])
        assert rate == 0.0
        assert passed == 0
        assert total == 0

    def test_calculate_pass_at_1_by_perturbation_type(self, sample_results):
        """Test pass rate filtered by perturbation type."""
        # Original: 4 pass, 1 fail -> 0.8
        rate, passed, total = calculate_pass_at_1(sample_results, 'original')
        assert rate == 0.8
        assert passed == 4
        assert total == 5

        # Synonym: 3 pass, 2 fail -> 0.6
        rate, passed, total = calculate_pass_at_1(sample_results, 'synonym')
        assert rate == 0.6
        assert passed == 3
        assert total == 5

        # Typo: 0 pass, 1 fail -> 0.0
        rate, passed, total = calculate_pass_at_1(sample_results, 'typo')
        assert rate == 0.0
        assert passed == 0
        assert total == 1

    def test_calculate_pass_rates_by_group(self, sample_results):
        """Test pass rates calculation for all groups."""
        rates = calculate_pass_rates_by_group(sample_results)
        
        assert 'original' in rates
        assert rates['original']['rate'] == 0.8
        assert rates['original']['passed'] == 4
        assert rates['original']['total'] == 5
        
        assert 'synonym' in rates
        assert rates['synonym']['rate'] == 0.6
        assert rates['synonym']['passed'] == 3
        assert rates['synonym']['total'] == 5
        
        assert 'typo' in rates
        assert rates['typo']['rate'] == 0.0
        assert rates['typo']['passed'] == 0
        assert rates['typo']['total'] == 1

class TestContingencyTable:
    """Tests for contingency table construction."""

    def test_build_contingency_table(self, sample_results):
        """Test contingency table construction for McNemar's test."""
        # Expected:
        # task1: original=pass, synonym=pass -> both pass
        # task2: original=pass, synonym=fail -> original pass, synonym fail
        # task3: original=fail, synonym=fail -> both fail
        # task4: original=pass, synonym=pass -> both pass
        # task5: original=pass, typo=fail -> original pass, typo fail (different type)
        
        # For synonym vs original:
        # n_pass_pass = 2 (task1, task4)
        # n_pass_fail = 1 (task2)
        # n_fail_pass = 0
        # n_fail_fail = 1 (task3)
        
        n_pp, n_pf, n_fp, n_ff = build_contingency_table(
            sample_results, 'original', 'synonym'
        )
        
        assert n_pp == 2
        assert n_pf == 1
        assert n_fp == 0
        assert n_ff == 1

class TestMcNemarTest:
    """Tests for McNemar's test implementation."""

    def test_mcnemar_test_with_discordant_pairs(self, sample_results):
        """Test McNemar's test when discordant pairs exist."""
        result = perform_mcnemar_test(sample_results, 'synonym')
        
        assert 'statistic' in result
        assert 'pvalue' in result
        assert 'n_pass_pass' in result
        assert 'n_pass_fail' in result
        assert 'n_fail_pass' in result
        assert 'n_fail_fail' in result
        
        # Should have discordant pairs
        assert result['n_pass_fail'] > 0 or result['n_fail_pass'] > 0

    def test_mcnemar_test_no_discordant_pairs(self):
        """Test McNemar's test when no discordant pairs exist."""
        results = [
            {'task_id': 't1', 'perturbation_type': 'original', 'status': 'pass'},
            {'task_id': 't1', 'perturbation_type': 'synonym', 'status': 'pass'},
            {'task_id': 't2', 'perturbation_type': 'original', 'status': 'fail'},
            {'task_id': 't2', 'perturbation_type': 'synonym', 'status': 'fail'},
        ]
        
        result = perform_mcnemar_test(results, 'synonym')
        
        assert result['n_pass_fail'] == 0
        assert result['n_fail_pass'] == 0
        assert result.get('note') == 'No discordant pairs'

    def test_mcnemar_test_empty_results(self):
        """Test McNemar's test with empty results."""
        result = perform_mcnemar_test([], 'synonym')
        
        assert result['n_pass_pass'] == 0
        assert result['n_pass_fail'] == 0
        assert result['n_fail_pass'] == 0
        assert result['n_fail_fail'] == 0

class TestBonferroniCorrection:
    """Tests for Bonferroni correction."""

    def test_bonferroni_single_test(self):
        """Test Bonferroni correction with single test."""
        pvalues = [0.03]
        result = apply_bonferroni_correction(pvalues)
        
        assert result['num_tests'] == 1
        assert result['alpha_corrected'] == 0.05
        assert result['corrected_pvalues'][0] == 0.03
        assert result['rejected'][0] == (0.03 < 0.05)

    def test_bonferroni_multiple_tests(self):
        """Test Bonferroni correction with multiple tests."""
        pvalues = [0.01, 0.03, 0.06]
        result = apply_bonferroni_correction(pvalues)
        
        assert result['num_tests'] == 3
        assert result['alpha_corrected'] == pytest.approx(0.05 / 3)
        
        # Corrected p-values
        expected_corrected = [0.03, 0.09, 1.0]  # min(p * 3, 1.0)
        for i, exp in enumerate(expected_corrected):
            assert result['corrected_pvalues'][i] == pytest.approx(exp)
        
        # Rejection decisions
        alpha_corrected = 0.05 / 3
        expected_rejected = [p < alpha_corrected for p in expected_corrected]
        assert result['rejected'] == expected_rejected

    def test_bonferroni_empty_list(self):
        """Test Bonferroni correction with empty list."""
        result = apply_bonferroni_correction([])
        
        assert result['num_tests'] == 0
        assert result['corrected_pvalues'] == []
        assert result['rejected'] == []

    def test_bonferroni_pvalue_capping(self):
        """Test that corrected p-values are capped at 1.0."""
        pvalues = [0.5]
        result = apply_bonferroni_correction(pvalues)
        
        assert result['corrected_pvalues'][0] == 1.0

class TestMixedEffectsModel:
    """Tests for mixed-effects logistic regression."""

    def test_mixed_effects_empty_results(self):
        """Test mixed-effects model with empty results."""
        result = run_mixed_effects_logistic_regression([])
        
        assert 'error' in result
        assert result['coefficients'] == {}

    def test_mixed_effects_single_type(self):
        """Test mixed-effects model with only one perturbation type."""
        results = [
            {'task_id': 't1', 'perturbation_type': 'original', 'status': 'pass'},
            {'task_id': 't2', 'perturbation_type': 'original', 'status': 'fail'},
        ]
        
        result = run_mixed_effects_logistic_regression(results)
        
        assert 'error' in result or 'Only one perturbation type' in result.get('model_summary', '')

class TestSensitivityAnalysis:
    """Tests for sensitivity analysis."""

    def test_sensitivity_empty_results(self):
        """Test sensitivity analysis with empty results."""
        result = analyze_sensitivity_to_thresholds([])
        
        assert 'error' in result

    def test_sensitivity_with_results(self):
        """Test sensitivity analysis with results containing semantic similarity."""
        results = [
            {'task_id': 't1', 'perturbation_type': 'synonym', 'status': 'pass', 'semantic_similarity': 0.96},
            {'task_id': 't2', 'perturbation_type': 'synonym', 'status': 'fail', 'semantic_similarity': 0.97},
            {'task_id': 't3', 'perturbation_type': 'synonym', 'status': 'pass', 'semantic_similarity': 0.92},
        ]
        
        result = analyze_sensitivity_to_thresholds(results, [0.90, 0.95, 0.99])
        
        assert 0.90 in result['pass_rates']
        assert 0.95 in result['pass_rates']
        assert 0.99 in result['pass_rates']
        
        # At 0.90: all 3 results included, 2 pass -> 0.667
        assert result['pass_rates'][0.90]['sample_size'] == 3
        
        # At 0.95: 2 results included, 1 pass -> 0.5
        assert result['pass_rates'][0.95]['sample_size'] == 2
        
        # At 0.99: 0 results included
        assert result['pass_rates'][0.99]['sample_size'] == 0

class TestLoadResults:
    """Tests for loading results from JSON."""

    def test_load_results_from_json_file(self, temp_results_file):
        """Test loading results from a JSON file."""
        results = load_results_from_json(temp_results_file)
        
        assert len(results) == 4
        assert results[0]['task_id'] == 't1'

    def test_load_results_from_json_missing_file(self, tmp_path):
        """Test loading results from a missing file."""
        with pytest.raises(FileNotFoundError):
            load_results_from_json(str(tmp_path / "nonexistent.json"))

class TestGenerateReport:
    """Tests for report generation."""

    def test_generate_statistics_report(self, tmp_path, sample_results):
        """Test generation of statistics report."""
        output_path = str(tmp_path / "report.json")
        
        report = generate_statistics_report(sample_results, output_path)
        
        # Check report structure
        assert 'pass_rates_by_group' in report
        assert 'mcnemar_tests' in report
        assert 'summary' in report
        
        # Check file was created
        assert Path(output_path).exists()
        
        # Verify content
        with open(output_path, 'r') as f:
            saved_report = json.load(f)
        
        assert saved_report['summary']['original_pass_rate'] == 0.8