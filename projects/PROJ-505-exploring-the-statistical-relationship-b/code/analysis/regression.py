"""
Regression analysis module: baseline vs full model, VIF, coefficients.
"""
import os
import sys
import json
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import pandas as pd
import numpy as np
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import stattools
from utils.logging import AnalysisError, get_logger, log_duration

logger = get_logger(__name__)

def get_coupling_function_columns() -> List[str]:
    """Return list of coupling function column names."""
    return ['epsilon', 'newell', 'v_bs', 'v_bt']

def compute_vif(df: pd.DataFrame, cols: List[str]) -> Dict[str, float]:
    """Compute Variance Inflation Factor for each predictor."""
    vif_dict = {}
    for i, col in enumerate(cols):
        other_cols = [c for c in cols if c != col]
        y = df[col]
        X = df[other_cols]
        X = X.add_constant()
        model = OLS(y, X).fit()
        r2 = model.rsquared
        vif = 1 / (1 - r2)
        vif_dict[col] = vif
    return vif_dict

def run_regression_analysis(df: pd.DataFrame, target: str, predictors: List[str], output_path: Path) -> None:
    """
    Run regression analysis and save results.
    """
    logger.info(f"Running regression for target: {target}, predictors: {predictors}")
    
    # Prepare data
    y = df[target].dropna()
    X = df[predictors].dropna(axis=0, how='all')
    
    # Ensure alignment
    common_idx = y.index.intersection(X.index)
    y = y.loc[common_idx]
    X = X.loc[common_idx]
    
    if len(y) < 10:
        raise AnalysisError("Insufficient data points for regression.")
    
    X = X.add_constant()
    model = OLS(y, X).fit()
    
    # Compute VIF
    vif_dict = compute_vif(df, predictors)
    
    # Check for high VIF
    high_vif = {k: v for k, v in vif_dict.items() if v >= 5}
    if high_vif:
        logger.warning(f"High VIF detected: {high_vif}")
        # Save warning artifact
        warning_path = output_path.parent / "vif_warning.json"
        with open(warning_path, 'w') as f:
            json.dump(high_vif, f)
    
    # Save results
    results = {
        "params": model.params.to_dict(),
        "pvalues": model.pvalues.to_dict(),
        "rsquared": model.rsquared,
        "rsquared_adj": model.rsquared_adj,
        "vif": vif_dict,
        "high_vif": high_vif
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Regression results saved to {output_path}")

@log_duration
def main():
    """Entry point for regression analysis."""
    # Placeholder for loading data
    logger.info("Starting regression analysis...")
    # In a real scenario, load from aligned data
    pass

if __name__ == "__main__":
    main()
