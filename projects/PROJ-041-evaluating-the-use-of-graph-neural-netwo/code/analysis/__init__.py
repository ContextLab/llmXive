"""
Analysis module for GNN Anomaly Detection project.

This module contains scripts and utilities for:
- Statistical significance testing (Permutation Tests, Benjamini-Hochberg)
- Feature attribution and importance ranking
- Model comparison and pattern identification
"""

from .attribution import (
    rank_feature_importance,
    compute_structural_feature_importance,
    compare_gnn_rf_rankings,
    save_feature_ranking
)

from .significance_tests import (
    run_permutation_test,
    benjamini_hochberg_correction,
    compare_model_pairs,
    save_significance_report
)

__all__ = [
    'rank_feature_importance',
    'compute_structural_feature_importance',
    'compare_gnn_rf_rankings',
    'save_feature_ranking',
    'run_permutation_test',
    'benjamini_hochberg_correction',
    'compare_model_pairs',
    'save_significance_report'
]