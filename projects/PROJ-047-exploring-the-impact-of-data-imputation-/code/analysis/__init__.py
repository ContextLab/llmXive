"""
Analysis module for causal inference and imputation.
"""
from .entities import SyntheticDataset, CausalEstimate, ImputationResult
from .imputation import apply_mean_imputation, apply_knn_imputation, apply_mice_imputation
from .causal_estimation import estimate_ate_ipw, estimate_ate_psm
from .se_combination import apply_rubins_rules, apply_bootstrap_ci
from .pipeline import run_imputation_and_estimation

__all__ = [
    'SyntheticDataset', 'CausalEstimate', 'ImputationResult',
    'apply_mean_imputation', 'apply_knn_imputation', 'apply_mice_imputation',
    'estimate_ate_ipw', 'estimate_ate_psm',
    'apply_rubins_rules', 'apply_bootstrap_ci',
    'run_imputation_and_estimation'
]