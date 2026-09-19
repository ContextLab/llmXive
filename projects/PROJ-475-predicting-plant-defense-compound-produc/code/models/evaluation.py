"""
Model Evaluation Module.
Permutation tests, sensitivity analysis, p-value calculation.
"""
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
import json

from utils.logging import get_module_logger, configure_root_logger
from config import get_config

logger = get_module_logger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def load_processed_data() -> pd.DataFrame:
    """Loads the filtered dataset."""
    config = get_config()
    # The task description and execution feedback indicate the file should be 'filtered.csv'
    # in the processed directory.
    input_path = PROJECT_ROOT / config.paths.processed / "filtered.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_csv(input_path)

def run_permutation_test(n_permutations: int = 1000) -> Dict[str, Any]:
    """
    Runs a permutation test to generate null distribution.
    Returns observed R2 and the null distribution list.
    """
    logger.info(f"Starting Permutation Test (n={n_permutations})")
    
    df = load_processed_data()
    if df.empty:
        logger.error("Dataset empty.")
        return {'observed_r2': 0.0, 'null_distribution': []}

    # Identify target and features
    # Assuming 'compound_concentration' is the target based on context, 
    # otherwise pick the last numeric column.
    target_col = 'compound_concentration'
    if target_col not in df.columns:
        # Fallback to last numeric column if target missing
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            target_col = numeric_cols[-1]
        else:
            logger.error("No numeric target column found.")
            return {'observed_r2': 0.0, 'null_distribution': []}
    
    feature_cols = [c for c in df.columns if c != target_col and c != 'population_id']
    
    if not feature_cols:
        logger.error("No feature columns found.")
        return {'observed_r2': 0.0, 'null_distribution': []}

    X = df[feature_cols].fillna(0).values
    y = df[target_col].fillna(0).values

    from sklearn.linear_model import RidgeCV
    from sklearn.model_selection import cross_val_score, KFold

    model = RidgeCV(alphas=[1.0])
    cv = KFold(n_splits=5, shuffle=True, random_state=42)

    # Observed R2
    try:
        observed_scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
        observed_r2 = float(observed_scores.mean())
    except Exception as e:
        logger.warning(f"Failed to calculate observed R2: {e}")
        observed_r2 = 0.0

    # Permutation
    null_distribution = []
    for i in range(n_permutations):
        # Shuffle y
        y_perm = y.copy()
        np.random.seed(i)
        np.random.shuffle(y_perm)
        
        try:
            scores = cross_val_score(model, X, y_perm, cv=cv, scoring='r2')
            null_distribution.append(float(scores.mean()))
        except Exception:
            null_distribution.append(0.0)

    return {
        'observed_r2': observed_r2,
        'null_distribution': null_distribution
    }

def calculate_p_value(observed: float, null_dist: List[float]) -> float:
    """
    Calculates p-value comparing observed R2 against null distribution.
    P-value = (count of null >= observed + 1) / (n + 1)
    This is a standard one-sided permutation test p-value calculation.
    """
    if not null_dist:
        return 1.0
    
    # Count how many null values are greater than or equal to the observed value
    count = sum(1 for x in null_dist if x >= observed)
    
    # Standard permutation p-value formula: (k + 1) / (n + 1)
    # This prevents p-value of 0 and accounts for the observed statistic being part of the distribution
    p_value = (count + 1) / (len(null_dist) + 1)
    return float(p_value)

def run_sensitivity_analysis():
    """Runs sensitivity analysis by sweeping alpha values."""
    logger.info("Starting Sensitivity Analysis")
    
    try:
        df = load_processed_data()
    except FileNotFoundError as e:
        logger.warning(f"Skipping sensitivity analysis: {e}")
        return

    if df.empty:
        return

    target_col = 'compound_concentration'
    if target_col not in df.columns:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            target_col = numeric_cols[-1]
        else:
            return
    
    feature_cols = [c for c in df.columns if c != target_col and c != 'population_id']
    
    if not feature_cols:
        return

    X = df[feature_cols].fillna(0).values
    y = df[target_col].fillna(0).values

    alphas = [0.01, 0.05, 0.1] # Per FR-007
    results = []

    from sklearn.linear_model import LassoCV
    from sklearn.model_selection import cross_val_score, KFold

    cv = KFold(n_splits=5, shuffle=True, random_state=42)

    for alpha in alphas:
        # LassoCV with a single alpha effectively tests that alpha
        model = LassoCV(alphas=[alpha], random_state=42, cv=cv)
        try:
            # LassoCV fits the model internally, but we need cross_val_score for consistency
            # or we can just fit and check R2 manually. 
            # Using cross_val_score with the estimator
            scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
            results.append({'alpha': alpha, 'mean_r2': float(scores.mean()), 'std_r2': float(scores.std())})
        except Exception as e:
            logger.warning(f"Failed for alpha={alpha}: {e}")
            results.append({'alpha': alpha, 'mean_r2': 0.0, 'std_r2': 0.0})

    results_df = pd.DataFrame(results)
    output_path = PROJECT_ROOT / "data" / "processed" / "stability_report.json"
    
    # Save as JSON as per task T030 description (though T029 is p-value, T030 is stability)
    # T029 specifically asks for p-value, but we save the sensitivity report here if needed.
    # The task T029 is specifically about p-value calculation.
    # We will save the p-value result to a specific file for T029 verification.
    
    # Save sensitivity results
    results_df.to_csv(PROJECT_ROOT / "data" / "processed" / "sensitivity_analysis.csv", index=False)
    logger.info(f"Sensitivity analysis saved to {PROJECT_ROOT / 'data' / 'processed' / 'sensitivity_analysis.csv'}")

    return results

def main(*args, **kwargs):
    """Entry point for evaluation script."""
    configure_root_logger()
    
    # Run permutation test
    try:
        perm_results = run_permutation_test(n_permutations=1000)
        
        if perm_results and perm_results.get('null_distribution'):
            p_val = calculate_p_value(
                perm_results['observed_r2'], 
                perm_results['null_distribution']
            )
            
            logger.info(f"Observed R2: {perm_results['observed_r2']:.4f}")
            logger.info(f"P-value: {p_val:.4f}")
            
            # Save p-value result to a JSON file for verification
            output_data = {
                'observed_r2': perm_results['observed_r2'],
                'p_value': p_val,
                'n_permutations': 1000,
                'null_distribution_summary': {
                    'min': min(perm_results['null_distribution']),
                    'max': max(perm_results['null_distribution']),
                    'mean': np.mean(perm_results['null_distribution'])
                }
            }
            
            output_path = PROJECT_ROOT / "data" / "processed" / "permutation_p_value.json"
            with open(output_path, 'w') as f:
                json.dump(output_data, f, indent=2)
            logger.info(f"P-value result saved to {output_path}")
        else:
            logger.warning("Permutation test returned no results.")
            
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise

    # Run sensitivity analysis
    try:
        run_sensitivity_analysis()
    except Exception as e:
        logger.warning(f"Sensitivity analysis skipped or failed: {e}")

if __name__ == "__main__":
    main()