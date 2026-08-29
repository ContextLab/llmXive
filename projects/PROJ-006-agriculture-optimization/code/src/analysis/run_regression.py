import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

from src.utils.io_helpers import read_csv_strict, write_json_strict, setup_logging, FatalError

logger = setup_logging("run_regression")

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for features."""
    X = df[features].copy()
    # Add constant for intercept if not included in VIF calculation context
    # VIF is calculated for predictors only
    vif_data = {}
    for i, feature in enumerate(features):
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data[feature] = float(vif)
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {feature}: {e}")
            vif_data[feature] = float('inf')
    return vif_data

def run_regression_models(df: pd.DataFrame) -> Dict[str, Any]:
    """Run Model 1 (Stability) and Model 2 (HFIAS) with appropriate SEs."""
    results = {}
    
    # Detect aggregation
    unique_villages = df['village_id'].nunique()
    n_rows = len(df)
    is_aggregated = (unique_villages == n_rows) or (unique_villages <= 1)
    
    model_type = 'aggregated' if is_aggregated else 'clustered'
    logger.info(f"Detected model type: {model_type} (N={n_rows}, Clusters={unique_villages})")

    # Features
    features = [
        'CSA_Index', 'finance_access', 'practice_mixed_farming',
        'practice_terracing', 'practice_conservation_tillage',
        'practice_agroforestry', 'extension_visits', 'education_level',
        'land_size'
    ]

    # Model 1: Stability_Score
    y1 = df['Stability_Score']
    X1 = df[features]
    X1 = sm.add_constant(X1)
    
    # Model 2: HFIAS
    y2 = df['HFIAS']
    X2 = df[features]
    X2 = sm.add_constant(X2)

    # Fit Model 1
    try:
        if model_type == 'clustered':
            # Cluster-robust SEs
            model1 = sm.OLS(y1, X1).fit(cov_type='cluster', cov_kwds={'groups': df['village_id']})
        else:
            # Robust (HC3) SEs
            model1 = sm.OLS(y1, X1).fit(cov_type='HC3')
        
        results['model_1'] = {
            'coefficients': model1.params.to_dict(),
            'p_values': model1.pvalues.to_dict(),
            'std_err': model1.bse.to_dict(),
            'rsquared_adj': float(model1.rsquared_adj),
            'model_type': model_type
        }
    except Exception as e:
        logger.error(f"Model 1 fitting failed: {e}")
        results['model_1'] = {'error': str(e)}

    # Fit Model 2
    try:
        if model_type == 'clustered':
            model2 = sm.OLS(y2, X2).fit(cov_type='cluster', cov_kwds={'groups': df['village_id']})
        else:
            model2 = sm.OLS(y2, X2).fit(cov_type='HC3')
        
        results['model_2'] = {
            'coefficients': model2.params.to_dict(),
            'p_values': model2.pvalues.to_dict(),
            'std_err': model2.bse.to_dict(),
            'rsquared_adj': float(model2.rsquared_adj),
            'model_type': model_type
        }
    except Exception as e:
        logger.error(f"Model 2 fitting failed: {e}")
        results['model_2'] = {'error': str(e)}

    # VIF Calculation
    vif_scores = calculate_vif(df, features)
    collinearity_warning = any(v > 5 for v in vif_scores.values())
    results['vif_scores'] = vif_scores
    results['collinearity_warning'] = collinearity_warning

    # Bonferroni Correction
    num_tests = len(features) * 2  # 2 models
    alpha = 0.05
    adjusted_alpha = alpha / num_tests
    results['bonferroni_corrected_p_values'] = {
        'model_1': {k: (v if v < 1 else 1.0) * num_tests for k, v in results['model_1'].get('p_values', {}).items()},
        'model_2': {k: (v if v < 1 else 1.0) * num_tests for k, v in results['model_2'].get('p_values', {}).items()}
    }
    results['adjusted_alpha'] = adjusted_alpha
    results['model_type'] = model_type

    return results

def main():
    parser = argparse.ArgumentParser(description="Run regression analysis")
    parser.add_argument("--input", type=str, default="data/processed/analysis_dataset.csv", help="Input dataset path")
    parser.add_argument("--output", type=str, default="data/processed/regression_results.json", help="Output results path")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FatalError(f"Input file not found: {input_path}")

    logger.info(f"Loading dataset from {input_path}")
    df = read_csv_strict(input_path)

    logger.info("Running regression models...")
    results = run_regression_models(df)

    logger.info(f"Writing results to {output_path}")
    write_json_strict(results, output_path)
    logger.info("Regression analysis complete.")

if __name__ == "__main__":
    main()
