"""
Analysis module for energy systems inequity study.
Contains modules for Propensity Score Matching, Balance Diagnostics, Causal Inference, and Sensitivity Analysis.
"""

from .balance import calculate_smd, plot_balance, check_balance_status
# Future imports:
# from .psm import estimate_propensity, match_pairs
# from .causal import run_ols, run_did
# from .sensitivity import sweep_caliper

__all__ = [
    'calculate_smd',
    'plot_balance',
    'check_balance_status'
    # 'estimate_propensity',
    # 'match_pairs',
    # 'run_ols',
    # 'run_did',
    # 'sweep_caliper'
]