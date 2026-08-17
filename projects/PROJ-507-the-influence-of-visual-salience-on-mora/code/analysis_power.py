"""
Power Analysis Module.
"""

import logging
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any

from config import seed_everything
from logging_config import get_logger

logger = get_logger(__name__)

def run_power_analysis(df: pd.DataFrame, model_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate post-hoc power analysis.
    """
    seed_everything(42)
    logger.info("Running power analysis...")

    # Simple power calculation based on effect size and sample size
    n = len(df)
    # Assume effect size from model
    effect_size = 0.5 # Placeholder if not calculated
    if 'effect_sizes' in model_results and model_results['effect_sizes']:
        # Get first available odds ratio
        first_eff = list(model_results['effect_sizes'].values())[0]
        # Convert OR to Cohen's d approximation (rough)
        effect_size = np.log(first_eff.get('odds_ratio', 1.0))

    # Power calculation (two-tailed)
    # Using statsmodels or simple approximation
    # power = 1 - beta
    # We use a simplified formula for demonstration
    alpha = 0.05
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = effect_size * np.sqrt(n) / 2 # Simplified
    power = stats.norm.cdf(z_beta - z_alpha)

    return {
        'sample_size': n,
        'effect_size': effect_size,
        'power': power,
        'power_adequate': power >= 0.80
    }

def integrate_power_results(power_results: Dict[str, Any], model_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Integrate power results into the main model results dictionary.
    """
    model_results['power_value'] = power_results.get('power', 0.0)
    model_results['power_adequate'] = power_results.get('power_adequate', False)
    return model_results
