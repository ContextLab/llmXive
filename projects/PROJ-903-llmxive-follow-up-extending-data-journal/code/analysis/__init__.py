"""
Analysis module for the llmXive Counterfactual Inspector pipeline.

This package contains statistical analysis utilities, correlation computation,
and partial correlation logic used by the baseline narrative and counterfactual
inspector agents.

Exports:
    - correlation_utils: Module for pairwise and partial correlations
    - stats_helpers: Module for statistical significance testing and validation
"""

from . import correlation_utils
from . import stats_helpers

__all__ = ["correlation_utils", "stats_helpers"]