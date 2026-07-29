import pytest
import numpy as np
from code.analysis.meta_analysis import perform_subgroup_analysis, MetaAnalysisStats


def test_subgroup_analysis_cochran_q():
    """
    Test subgroup analysis using Cochran's Q.
    Creates synthetic data with known between-group heterogeneity.
    """
    # Group A: Effect sizes ~ 0.5
    # Group B: Effect sizes ~ 1.5
    # This should yield a significant Q_between
    data = [
        {'effect_size': 0.4, 'se': 0.1, 'study_id': 'S1', 'group': 'A'},
        {'effect_size': 0.5, 'se': 0.1, 'study_id': 'S2', 'group': 'A'},
        {'effect_size': 0.6, 'se': 0.1, 'study_id': 'S3', 'group': 'A'},
        {'effect_size': 1.4, 'se': 0.1, 'study_id': 'S4', 'group': 'B'},
        {'effect_size': 1.5, 'se': 0.1, 'study_id': 'S5', 'group': 'B'},
        {'effect_size': 1.6, 'se': 0.1, 'study_id': 'S6', 'group': 'B'},
    ]

    stats = perform_subgroup_analysis(data, 'group')

    assert isinstance(stats, MetaAnalysisStats)
    assert stats.heterogeneity_q > 0
    assert stats.heterogeneity_df == 1  # 2 groups - 1
    assert stats.subgroup_stats is not None
    assert 'q_between' in stats.subgroup_stats
    assert 'p_value' in stats.subgroup_stats

    # With such distinct groups (0.5 vs 1.5) and small SE, p-value should be very low
    assert stats.subgroup_stats['p_value'] < 0.05


def test_subgroup_analysis_single_group():
    """Test that analysis fails gracefully if only one group exists."""
    data = [
        {'effect_size': 0.5, 'se': 0.1, 'study_id': 'S1', 'group': 'A'},
        {'effect_size': 0.6, 'se': 0.1, 'study_id': 'S2', 'group': 'A'},
    ]

    with pytest.raises(ValueError, match="must have at least 2 levels"):
        perform_subgroup_analysis(data, 'group')


def test_subgroup_analysis_missing_variable():
    """Test that analysis fails if the subgroup variable is missing."""
    data = [
        {'effect_size': 0.5, 'se': 0.1, 'study_id': 'S1'},
        {'effect_size': 0.6, 'se': 0.1, 'study_id': 'S2'},
    ]

    with pytest.raises(ValueError, match="not found in data"):
        perform_subgroup_analysis(data, 'nonexistent_var')