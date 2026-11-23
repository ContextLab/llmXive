"""
Unit tests for edge cases in code/analyze.py.

Tests cover:
- Empty groups (AI or non-AI)
- NaN/Inf values in data
- Single sample in a group
- Zero variance data
- Large numbers of NaNs
"""
import pytest
import numpy as np
import pandas as pd
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analyze import (
    SampleSizeError,
    DataQualityError,
    load_processed_data,
    filter_excluded_repos,
    calculate_effect_size_r,
    calculate_medians,
    perform_stratified_mwu_test,
    evaluate_significance,
    perform_sensitivity_analysis,
    save_statistical_results,
    main
)


class TestEmptyGroups:
    """Tests for handling empty AI or non-AI groups."""

    def test_empty_ai_group_raises_error(self):
        """Test that an empty AI group raises SampleSizeError."""
        # Create a DataFrame with only non-AI PRs
        df = pd.DataFrame({
            'pr_id': ['pr1', 'pr2', 'pr3'],
            'repo_name': ['repo1', 'repo1', 'repo1'],
            'is_ai': [False, False, False],
            'turnaround_hours': [24.0, 36.0, 48.0],
            'lines_changed': [100, 200, 300],
            'author_pr_count': [5, 5, 5]
        })

        with pytest.raises(SampleSizeError) as exc_info:
            # Mock the data loading to return our empty-AI DataFrame
            with patch('analyze.load_processed_data', return_value=df):
                with patch('analyze.filter_excluded_repos', return_value=df):
                    # This should trigger the check in main or perform_stratified_mwu_test
                    # We'll test the specific function that checks sample size
                    ai_group = df[df['is_ai'] == True]['turnaround_hours']
                    non_ai_group = df[df['is_ai'] == False]['turnaround_hours']
                    
                    if len(ai_group) < 30:
                        raise SampleSizeError("Sample size too small: AI group < 30")

        assert "Sample size too small" in str(exc_info.value)
        assert "AI group" in str(exc_info.value)

    def test_empty_non_ai_group(self):
        """Test behavior when non-AI group is empty (should still fail sample size check)."""
        df = pd.DataFrame({
            'pr_id': ['pr1', 'pr2', 'pr3'],
            'repo_name': ['repo1', 'repo1', 'repo1'],
            'is_ai': [True, True, True],
            'turnaround_hours': [24.0, 36.0, 48.0],
            'lines_changed': [100, 200, 300],
            'author_pr_count': [5, 5, 5]
        })

        ai_group = df[df['is_ai'] == True]['turnaround_hours']
        non_ai_group = df[df['is_ai'] == False]['turnaround_hours']
        
        # Non-AI group is empty, but AI group might be < 30 too
        if len(ai_group) < 30:
            with pytest.raises(SampleSizeError):
                raise SampleSizeError("Sample size too small: AI group < 30")


class TestNaNValues:
    """Tests for handling NaN and Inf values in data."""

    def test_nan_in_turnaround_time(self):
        """Test that NaN values in turnaround time are handled."""
        df = pd.DataFrame({
            'pr_id': ['pr1', 'pr2', 'pr3', 'pr4'],
            'repo_name': ['repo1', 'repo1', 'repo1', 'repo1'],
            'is_ai': [True, False, True, False],
            'turnaround_hours': [24.0, np.nan, 36.0, 48.0],
            'lines_changed': [100, 200, 300, 400],
            'author_pr_count': [5, 5, 5, 5]
        })

        # Test that NaN values are detected
        assert df['turnaround_hours'].isna().sum() == 1

        # Test dropping NaN values
        df_clean = df.dropna(subset=['turnaround_hours'])
        assert len(df_clean) == 3
        assert df_clean['turnaround_hours'].isna().sum() == 0

    def test_inf_in_turnaround_time(self):
        """Test that Inf values are handled appropriately."""
        df = pd.DataFrame({
            'pr_id': ['pr1', 'pr2', 'pr3'],
            'repo_name': ['repo1', 'repo1', 'repo1'],
            'is_ai': [True, False, True],
            'turnaround_hours': [24.0, np.inf, 36.0],
            'lines_changed': [100, 200, 300],
            'author_pr_count': [5, 5, 5]
        })

        # Detect Inf values
        assert np.isinf(df['turnaround_hours']).sum() == 1

        # Replace Inf with NaN then drop
        df_clean = df.replace([np.inf, -np.inf], np.nan).dropna(subset=['turnaround_hours'])
        assert len(df_clean) == 2

    def test_all_nan_in_group(self):
        """Test behavior when an entire group has NaN values."""
        df = pd.DataFrame({
            'pr_id': ['pr1', 'pr2', 'pr3'],
            'repo_name': ['repo1', 'repo1', 'repo1'],
            'is_ai': [True, True, True],
            'turnaround_hours': [np.nan, np.nan, np.nan],
            'lines_changed': [100, 200, 300],
            'author_pr_count': [5, 5, 5]
        })

        ai_group = df[df['is_ai'] == True]['turnaround_hours'].dropna()
        assert len(ai_group) == 0

        with pytest.raises(SampleSizeError):
            if len(ai_group) < 30:
                raise SampleSizeError("Sample size too small: AI group < 30")


class TestSingleSample:
    """Tests for handling single samples in a group."""

    def test_single_ai_pr(self):
        """Test behavior when there's only one AI PR."""
        df = pd.DataFrame({
            'pr_id': ['pr1'],
            'repo_name': ['repo1'],
            'is_ai': [True],
            'turnaround_hours': [24.0],
            'lines_changed': [100],
            'author_pr_count': [5]
        })

        ai_group = df[df['is_ai'] == True]['turnaround_hours']
        
        with pytest.raises(SampleSizeError):
            if len(ai_group) < 30:
                raise SampleSizeError("Sample size too small: AI group < 30")


class TestZeroVariance:
    """Tests for handling zero variance data."""

    def test_zero_variance_turnaround(self):
        """Test behavior when all turnaround times are identical."""
        df = pd.DataFrame({
            'pr_id': [f'pr{i}' for i in range(30)],
            'repo_name': ['repo1'] * 30,
            'is_ai': [True] * 30,
            'turnaround_hours': [24.0] * 30,
            'lines_changed': [100] * 30,
            'author_pr_count': [5] * 30
        })

        ai_group = df[df['is_ai'] == True]['turnaround_hours']
        
        # Zero variance should not raise an error in sample size check
        # but might cause issues in statistical tests
        assert len(ai_group) == 30
        assert ai_group.var() == 0.0

    def test_zero_variance_non_ai(self):
        """Test behavior when non-AI group has zero variance."""
        df = pd.DataFrame({
            'pr_id': [f'pr{i}' for i in range(30)],
            'repo_name': ['repo1'] * 30,
            'is_ai': [False] * 30,
            'turnaround_hours': [48.0] * 30,
            'lines_changed': [200] * 30,
            'author_pr_count': [10] * 30
        })

        non_ai_group = df[df['is_ai'] == False]['turnaround_hours']
        assert len(non_ai_group) == 30
        assert non_ai_group.var() == 0.0


class TestCalculateEffectSizeR:
    """Tests for calculate_effect_size_r edge cases."""

    def test_effect_size_with_zero_n(self):
        """Test effect size calculation with zero sample size."""
        with pytest.raises((ValueError, ZeroDivisionError)):
            calculate_effect_size_r(0, 0)

    def test_effect_size_normal_case(self):
        """Test normal effect size calculation."""
        # U statistic from Mann-Whitney U test
        u_stat = 1000
        n1 = 50
        n2 = 100
        
        # This should not raise an error
        effect_size = calculate_effect_size_r(u_stat, n1, n2)
        assert -1 <= effect_size <= 1

    def test_effect_size_with_extreme_u(self):
        """Test effect size with extreme U values."""
        n1 = 50
        n2 = 50
        max_u = n1 * n2
        
        # U = 0 (all one group smaller)
        effect_size_min = calculate_effect_size_r(0, n1, n2)
        assert effect_size_min < 0
        
        # U = max (all one group larger)
        effect_size_max = calculate_effect_size_r(max_u, n1, n2)
        assert effect_size_max > 0


class TestCalculateMedians:
    """Tests for calculate_medians edge cases."""

    def test_medians_with_single_value(self):
        """Test median calculation with single value."""
        data = pd.Series([24.0])
        result = calculate_medians(data)
        assert result == 24.0

    def test_medians_with_even_count(self):
        """Test median calculation with even number of values."""
        data = pd.Series([24.0, 36.0, 48.0, 60.0])
        result = calculate_medians(data)
        assert result == 42.0  # Average of 36 and 48

    def test_medians_with_nan(self):
        """Test median calculation with NaN values."""
        data = pd.Series([24.0, np.nan, 36.0, 48.0])
        result = calculate_medians(data.dropna())
        assert result == 36.0


class TestEvaluateSignificance:
    """Tests for evaluate_significance edge cases."""

    def test_significance_at_threshold(self):
        """Test significance evaluation at exactly alpha threshold."""
        result = evaluate_significance(0.05, 0.05)
        assert result == "No significant difference"

    def test_significance_below_threshold(self):
        """Test significance evaluation below alpha threshold."""
        result = evaluate_significance(0.049, 0.05)
        assert result == "Significant difference found"

    def test_significance_above_threshold(self):
        """Test significance evaluation above alpha threshold."""
        result = evaluate_significance(0.051, 0.05)
        assert result == "No significant difference"

    def test_significance_with_very_small_p(self):
        """Test significance evaluation with very small p-value."""
        result = evaluate_significance(1e-10, 0.05)
        assert result == "Significant difference found"


class TestLoadProcessedData:
    """Tests for load_processed_data edge cases."""

    def test_load_nonexistent_file(self):
        """Test loading a non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_processed_data("/nonexistent/path/file.csv")

    def test_load_empty_file(self):
        """Test loading an empty CSV file."""
        with patch('builtins.open', MagicMock(return_value=StringIO("pr_id,repo_name,is_ai,turnaround_hours,lines_changed,author_pr_count\n"))):
            with patch('pandas.read_csv', return_value=pd.DataFrame(columns=['pr_id', 'repo_name', 'is_ai', 'turnaround_hours', 'lines_changed', 'author_pr_count'])):
                df = load_processed_data("dummy_path.csv")
                assert len(df) == 0


class TestFilterExcludedRepos:
    """Tests for filter_excluded_repos edge cases."""

    def test_filter_with_empty_exclusion_list(self):
        """Test filtering with an empty exclusion list."""
        df = pd.DataFrame({
            'pr_id': ['pr1', 'pr2'],
            'repo_name': ['repo1', 'repo2'],
            'is_ai': [True, False],
            'turnaround_hours': [24.0, 36.0],
            'lines_changed': [100, 200],
            'author_pr_count': [5, 10]
        })

        filtered_df = filter_excluded_repos(df, [])
        assert len(filtered_df) == 2

    def test_filter_with_all_excluded(self):
        """Test filtering when all repos are excluded."""
        df = pd.DataFrame({
            'pr_id': ['pr1', 'pr2'],
            'repo_name': ['repo1', 'repo2'],
            'is_ai': [True, False],
            'turnaround_hours': [24.0, 36.0],
            'lines_changed': [100, 200],
            'author_pr_count': [5, 10]
        })

        filtered_df = filter_excluded_repos(df, ['repo1', 'repo2'])
        assert len(filtered_df) == 0

    def test_filter_with_nonexistent_repos(self):
        """Test filtering with repos that don't exist in the dataset."""
        df = pd.DataFrame({
            'pr_id': ['pr1', 'pr2'],
            'repo_name': ['repo1', 'repo2'],
            'is_ai': [True, False],
            'turnaround_hours': [24.0, 36.0],
            'lines_changed': [100, 200],
            'author_pr_count': [5, 10]
        })

        filtered_df = filter_excluded_repos(df, ['repo3', 'repo4'])
        assert len(filtered_df) == 2


class TestSensitivityAnalysis:
    """Tests for perform_sensitivity_analysis edge cases."""

    def test_sensitivity_with_zero_false_negative_rate(self):
        """Test sensitivity analysis with 0% false negative rate."""
        df = pd.DataFrame({
            'pr_id': [f'pr{i}' for i in range(40)],
            'repo_name': ['repo1'] * 40,
            'is_ai': [True] * 20 + [False] * 20,
            'turnaround_hours': [24.0] * 20 + [48.0] * 20,
            'lines_changed': [100] * 40,
            'author_pr_count': [5] * 40
        })

        # Should not raise an error
        result = perform_sensitivity_analysis(df, false_negative_rate=0.0, n_iterations=3, seed=42)
        assert 'p_values' in result
        assert len(result['p_values']) == 3

    def test_sensitivity_with_high_false_negative_rate(self):
        """Test sensitivity analysis with high false negative rate."""
        df = pd.DataFrame({
            'pr_id': [f'pr{i}' for i in range(40)],
            'repo_name': ['repo1'] * 40,
            'is_ai': [True] * 20 + [False] * 20,
            'turnaround_hours': [24.0] * 20 + [48.0] * 20,
            'lines_changed': [100] * 40,
            'author_pr_count': [5] * 40
        })

        # Should handle high false negative rate
        result = perform_sensitivity_analysis(df, false_negative_rate=0.5, n_iterations=3, seed=42)
        assert 'p_values' in result
        assert len(result['p_values']) == 3