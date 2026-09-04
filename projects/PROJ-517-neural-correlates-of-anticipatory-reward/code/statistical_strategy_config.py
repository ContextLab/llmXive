"""
Statistical Strategy Configuration Module.

This module defines the statistical strategy parameters for the
Neural Correlates of Anticipatory Reward Processing analysis.
It serves as the central configuration for dispersion checks and
permutation test parameters as defined in SC-001.
"""

from typing import Dict, Any

# Statistical Strategy Parameters (SC-001)
STRATEGY_CONFIG: Dict[str, Any] = {
    "dispersion_check": {
        "method": "deviance_over_df",
        "formula": "deviance / (n_observations - n_parameters)",
        "threshold_high": 1.1,
        "threshold_low": 0.9,
        "description": "Check for overdispersion (NB) or underdispersion (Poisson)"
    },
    "model_selection": {
        "criterion": "AIC",
        "fallback": "NegativeBinomial",
        "description": "Select NegativeBinomial if dispersion > 1.1, else Poisson"
    },
    "permutation_test": {
        "algorithm": "freedman_lane",
        "iterations": 10000,
        "alpha": 0.05,
        "two_tailed": True,
        "description": "Freedman-Lane permutation test for GLM significance with covariates"
    },
    "covariates": {
        "required": ["cue_delay"],
        "optional": [],
        "collinearity_threshold": 5.0,
        "description": "VIF threshold for dropping collinear predictors"
    },
    "power_analysis": {
        "power_target": 0.80,
        "alpha": 0.05,
        "metric": "Cohen_f2",
        "description": "Calculate MDES based on observed variance and sample size"
    },
    "multiple_comparisons": {
        "method": "bonferroni",
        "threshold": 0.05,
        "description": "Apply Bonferroni correction if multiple neurons are analyzed"
    }
}

def get_strategy_summary() -> Dict[str, Any]:
    """
    Returns a summary of the statistical strategy parameters.

    Returns:
        Dict containing key strategy parameters for logging and reporting.
    """
    return {
        "dispersion_formula": STRATEGY_CONFIG["dispersion_check"]["formula"],
        "permutation_iterations": STRATEGY_CONFIG["permutation_test"]["iterations"],
        "alpha_level": STRATEGY_CONFIG["permutation_test"]["alpha"],
        "permutation_algorithm": STRATEGY_CONFIG["permutation_test"]["algorithm"],
        "model_selection_criterion": STRATEGY_CONFIG["model_selection"]["criterion"]
    }