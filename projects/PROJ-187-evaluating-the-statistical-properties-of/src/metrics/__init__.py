"""Fidelity metric modules (marginal and correlation)."""
from src.metrics.marginal import (
    detect_column_types,
    kde_estimate,
    ks_test,
    chi_square_test,
    compute_marginal_metrics,
)
from src.metrics.correlation import (
    correlation_matrices,
    fisher_z,
    fisher_z_deviation,
    permutation_correlation_test,
    compute_correlation_metrics,
)

__all__ = [
    "detect_column_types",
    "kde_estimate",
    "ks_test",
    "chi_square_test",
    "compute_marginal_metrics",
    "correlation_matrices",
    "fisher_z",
    "fisher_z_deviation",
    "permutation_correlation_test",
    "compute_correlation_metrics",
]