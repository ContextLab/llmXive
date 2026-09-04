from typing import Dict, Any

def get_strategy_summary() -> Dict[str, Any]:
    """
    Returns the statistical strategy parameters as defined in T000d.
    """
    return {
        "alpha": 0.05,
        "permutation_iterations": 1000,
        "dispersion_formula": "LRT/AIC",
        "model_selection_criteria": {
            "negative_binomial_threshold": 1.1,
            "poisson_threshold": 1.1
        }
    }
