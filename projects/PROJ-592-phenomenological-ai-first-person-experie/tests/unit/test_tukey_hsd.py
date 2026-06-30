"""
Unit tests for Tukey HSD post-hoc tests.
"""
import pytest
import numpy as np
from code.analysis.tukey_hsd import perform_tukey_hsd, run_tukey_posthoc, TukeyHSDError


class TestTukeyHSD:
    def test_perform_tukey_basic(self):
        """Test basic functionality with synthetic data."""
        # Create data with clear separation
        values = [1.0, 1.1, 1.2, 2.0, 2.1, 2.2]
        groups = ['A', 'A', 'A', 'B', 'B', 'B']

        result = perform_tukey_hsd(values, groups, alpha=0.05)

        assert 'summary_table' in result
        assert 'reject' in result
        assert 'p_values' in result
        assert 'mean_diff' in result
        assert 'groups' in result

        # Check that groups are sorted
        assert result['groups'] == ['A', 'B']

    def test_perform_tukey_single_group_error(self):
        """Test that a single group raises an error."""
        with pytest.raises(TukeyHSDError):
            perform_tukey_hsd([1.0, 2.0], ['A', 'A'])

    def test_perform_tukey_mismatched_lengths(self):
        """Test that mismatched lengths raise an error."""
        with pytest.raises(TukeyHSDError):
            perform_tukey_hsd([1.0, 2.0], ['A', 'B', 'C'])

    def test_run_tukey_posthoc_dict(self):
        """Test the dictionary-based wrapper."""
        data = {
            'Group_A': [1.0, 1.1, 1.2],
            'Group_B': [2.0, 2.1, 2.2],
            'Group_C': [1.5, 1.6, 1.7]
        }

        result = run_tukey_posthoc(data)

        assert 'summary_table' in result
        assert len(result['groups']) == 3

    def test_run_tukey_empty_dict(self):
        """Test that empty dictionary raises an error."""
        with pytest.raises(TukeyHSDError):
            run_tukey_posthoc({})

    def test_run_tukey_single_group_dict(self):
        """Test that a dictionary with only one group raises an error."""
        data = {'Group_A': [1.0, 2.0]}
        with pytest.raises(TukeyHSDError):
            run_tukey_posthoc(data)

    def test_run_tukey_empty_list_in_dict(self):
        """Test that a dictionary with an empty list for a group handles it gracefully (skips)."""
        data = {
            'Group_A': [1.0, 2.0],
            'Group_B': []
        }
        # Should raise error if only one valid group remains
        with pytest.raises(TukeyHSDError):
            run_tukey_posthoc(data)
