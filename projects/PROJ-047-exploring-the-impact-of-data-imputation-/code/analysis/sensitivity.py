import pandas as pd
import numpy as np
import json
from scipy import stats
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def verify_bias_trend(df_summary: pd.DataFrame) -> Dict[str, Any]:
    """
    Verify monotonic trend of bias vs beta.
    Calculate Spearman rho and regression slope.
    """
    # Aggregate mean absolute bias per beta
    df_summary['abs_bias_mean'] = df_summary.filter(like='_bias').abs().mean(axis=1)
    
    # Group by beta and calculate mean absolute bias
    agg = df_summary.groupby('beta')['abs_bias_mean'].mean().reset_index()
    agg = agg.sort_values('beta')
    
    if len(agg) < 2:
        logger.error("Not enough beta levels to verify trend.")
        return {
            'rho': 0.0,
            'p_value': 1.0,
            'slope': 0.0,
            'monotonicity_confirmed': False,
            'status': 'failed',
            'error': 'Not enough beta levels'
        }
    
    # Spearman correlation
    rho, p_value = stats.spearmanr(agg['beta'], agg['abs_bias_mean'])
    
    # Linear regression for slope
    slope, intercept, r_value, p_val_reg, std_err = stats.linregress(agg['beta'], agg['abs_bias_mean'])
    
    # Verify conditions: rho > 0.9, p < 0.05, slope > 0
    monotonicity_confirmed = (rho > 0.9) and (p_value < 0.05) and (slope > 0)
    
    return {
        'rho': float(rho),
        'p_value': float(p_value),
        'slope': float(slope),
        'monotonicity_confirmed': bool(monotonicity_confirmed),
        'status': 'passed' if monotonicity_confirmed else 'failed'
    }

def verify_coverage_trend(df_summary: pd.DataFrame) -> Dict[str, Any]:
    """
    Verify monotonic trend of coverage rate vs beta (should be negative).
    """
    # Aggregate mean coverage per beta
    # Find columns with '_covered'
    covered_cols = [c for c in df_summary.columns if 'covered' in c]
    if not covered_cols:
        logger.error("No coverage columns found.")
        return {
            'rho': 0.0,
            'p_value': 1.0,
            'slope': 0.0,
            'negative_slope_confirmed': False,
            'status': 'failed'
        }
    
    df_summary['coverage_rate'] = df_summary[covered_cols].mean(axis=1)
    
    agg = df_summary.groupby('beta')['coverage_rate'].mean().reset_index()
    agg = agg.sort_values('beta')
    
    if len(agg) < 2:
        logger.error("Not enough beta levels to verify coverage trend.")
        return {
            'rho': 0.0,
            'p_value': 1.0,
            'slope': 0.0,
            'negative_slope_confirmed': False,
            'status': 'failed'
        }
    
    # Spearman correlation
    rho, p_value = stats.spearmanr(agg['beta'], agg['coverage_rate'])
    
    # Linear regression for slope
    slope, intercept, r_value, p_val_reg, std_err = stats.linregress(agg['beta'], agg['coverage_rate'])
    
    # Verify conditions: rho < 0 (negative correlation), p < 0.05, slope < 0
    negative_slope_confirmed = (rho < 0) and (p_value < 0.05) and (slope < 0)
    
    return {
        'rho': float(rho),
        'p_value': float(p_value),
        'slope': float(slope),
        'negative_slope_confirmed': bool(negative_slope_confirmed),
        'status': 'passed' if negative_slope_confirmed else 'failed'
    }
