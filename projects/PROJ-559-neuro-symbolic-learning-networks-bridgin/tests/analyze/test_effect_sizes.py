"""
Unit tests for effect sizes analysis module.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
import tempfile
import json

from code.analyze.effect_sizes import (
    load_effect_size_data,
    calculate_cohens_d,
    run_pairwise_effect_sizes,
    validate_ci_width,
    generate_effect_size_report
)

class TestCalculateCohensD:
    """Tests for Cohen's d calculation."""

    def test_basic_calculation(self):
        """Test basic Cohen's d calculation with known values."""
        group1 = pd.Series([10, 12, 11, 13, 14])
        group2 = pd.Series([8, 9, 7, 10, 8])

        result = calculate_cohens_d(group1, group2)

        assert 'cohens_d' in result
        assert 'ci_lower' in result
        assert 'ci_upper' in result
        assert 'ci_width' in result
        assert result['n1'] == 5
        assert result['n2'] == 5

        # Cohen's d should be positive (group1 > group2)
        assert result['cohens_d'] > 0

    def test_identical_groups(self):
        """Test with identical groups (d should be 0)."""
        group1 = pd.Series([5, 6, 7, 8, 9])
        group2 = pd.Series([5, 6, 7, 8, 9])

        result = calculate_cohens_d(group1, group2)

        assert abs(result['cohens_d']) < 1e-10
        assert result['ci_width'] > 0  # CI should still have width due to sampling

    def test_small_sample_error(self):
        """Test that groups with < 2 samples raise an error."""
        group1 = pd.Series([10])
        group2 = pd.Series([5, 6, 7])

        with pytest.raises(ValueError):
            calculate_cohens_d(group1, group2)

    def test_ci_width_calculation(self):
        """Test that CI width is correctly calculated."""
        group1 = pd.Series([10, 12, 11, 13, 14, 15, 16, 17, 18, 19])
        group2 = pd.Series([8, 9, 7, 10, 8, 9, 7, 10, 8, 9])

        result = calculate_cohens_d(group1, group2)

        expected_width = result['ci_upper'] - result['ci_lower']
        assert abs(result['ci_width'] - expected_width) < 1e-10

class TestPairwiseEffectSizes:
    """Tests for pairwise effect size computation."""

    def test_three_conditions(self):
        """Test pairwise comparisons with three conditions."""
        df = pd.DataFrame({
            'condition': ['neural'] * 20 + ['symbolic'] * 20 + ['neuro_symbolic'] * 20,
            'correct': [0.8] * 20 + [0.6] * 20 + [0.7] * 20
        })

        comparisons = run_pairwise_effect_sizes(df, metric='correct')

        assert len(comparisons) == 3  # 3 pairwise comparisons for 3 groups
        
        condition_pairs = [(c['condition_1'], c['condition_2']) for c in comparisons]
        assert ('neural', 'symbolic') in condition_pairs
        assert ('neural', 'neuro_symbolic') in condition_pairs
        assert ('symbolic', 'neuro_symbolic') in condition_pairs

    def test_missing_metric_column(self):
        """Test that missing metric column raises an error."""
        df = pd.DataFrame({
            'condition': ['A', 'B'],
            'other_col': [1, 2]
        })

        with pytest.raises(ValueError):
            run_pairwise_effect_sizes(df, metric='nonexistent')

    def test_single_condition(self):
        """Test with only one condition (no comparisons)."""
        df = pd.DataFrame({
            'condition': ['neural'] * 10,
            'correct': [0.8] * 10
        })

        comparisons = run_pairwise_effect_sizes(df, metric='correct')
        assert len(comparisons) == 0

class TestValidateCIWidth:
    """Tests for CI width validation."""

    def test_all_within_threshold(self):
        """Test validation when all CIs are within threshold."""
        comparisons = [
            {'condition_1': 'A', 'condition_2': 'B', 'ci_width': 0.10},
            {'condition_1': 'A', 'condition_2': 'C', 'ci_width': 0.15}
        ]

        validation = validate_ci_width(comparisons, threshold=0.20)

        assert validation['passed'] is True
        assert len(validation['violations']) == 0

    def test_violations_detected(self):
        """Test validation when some CIs exceed threshold."""
        comparisons = [
            {'condition_1': 'A', 'condition_2': 'B', 'ci_width': 0.10},
            {'condition_1': 'A', 'condition_2': 'C', 'ci_width': 0.25},
            {'condition_1': 'B', 'condition_2': 'C', 'ci_width': 0.30}
        ]

        validation = validate_ci_width(comparisons, threshold=0.20)

        assert validation['passed'] is False
        assert len(validation['violations']) == 2

        for v in validation['violations']:
            assert v['ci_width'] > 0.20

    def test_custom_threshold(self):
        """Test validation with custom threshold."""
        comparisons = [
            {'condition_1': 'A', 'condition_2': 'B', 'ci_width': 0.15}
        ]

        validation = validate_ci_width(comparisons, threshold=0.10)

        assert validation['passed'] is False
        assert len(validation['violations']) == 1

class TestLoadEffectSizeData:
    """Tests for data loading."""

    def test_load_valid_csv(self):
        """Test loading a valid CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("condition,correct\n")
            f.write("neural,0.8\n")
            f.write("symbolic,0.6\n")
            f.write("neuro_symbolic,0.7\n")
            temp_path = f.name

        try:
            df = load_effect_size_data(temp_path)
            assert len(df) == 3
            assert 'condition' in df.columns
            assert 'correct' in df.columns
        finally:
            os.unlink(temp_path)

    def test_missing_file(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_effect_size_data('nonexistent_file.csv')

    def test_missing_required_columns(self):
        """Test that missing required columns raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("condition,other_col\n")
            f.write("neural,0.8\n")
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_effect_size_data(temp_path)
        finally:
            os.unlink(temp_path)

class TestGenerateEffectSizeReport:
    """Tests for report generation."""

    def test_report_generation(self):
        """Test that a valid JSON report is generated."""
        comparisons = [
            {
                'condition_1': 'A',
                'condition_2': 'B',
                'cohens_d': 0.5,
                'ci_lower': 0.2,
                'ci_upper': 0.8,
                'ci_width': 0.6,
                'n1': 10,
                'n2': 10
            }
        ]
        validation = {'passed': True, 'violations': []}

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'report.json')
            generate_effect_size_report(comparisons, validation, output_path)

            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                report = json.load(f)

            assert 'effect_sizes' in report
            assert 'validation' in report
            assert 'metadata' in report
            assert len(report['effect_sizes']) == 1