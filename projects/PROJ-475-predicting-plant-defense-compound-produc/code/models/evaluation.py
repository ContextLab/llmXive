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

from utils.logging import get_module_logger
from config import get_config

logger = get_module_logger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def load_processed_data() -> pd.DataFrame:
    """Loads the filtered dataset."""
    config = get_config()
    input_path = PROJECT_ROOT / config.paths.processed / "filtered.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_csv(input_path)

def run_permutation_test(n_permutations: int = 1000) -> Dict[str, Any]:
    """
    Runs a permutation test to generate null distribution.
    """
    logger.info(f"Starting Permutation Test (n={n_permutations})")
    
    df = load_processed_data()
    if df.empty:
        logger.error("Dataset empty.")
        return {}

    target_col = 'compound_concentration' if 'compound_concentration' in df.columns else df.select_dtypes(include=[np.number]).columns[-1]
    feature_cols = [c for c in df.columns if c != target_col and c != 'population_id']
    
    X = df[feature_cols].fillna(0)
    y = df[target_col].fillna(0)

    from sklearn.linear_model import RidgeCV
    from sklearn.model_selection import cross_val_score, KFold

    model = RidgeCV(alphas=[1.0])
    cv = KFold(n_splits=5, shuffle=True, random_state=42)

    # Observed R2
    try:
        observed_scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
        observed_r2 = observed_scores.mean()
    except Exception:
        observed_r2 = 0.0

    # Permutation
    null_distribution = []
    for i in range(n_permutations):
        y_perm = y.sample(frac=1, random_state=i).reset_index(drop=True)
        try:
            scores = cross_val_score(model, X, y_perm, cv=cv, scoring='r2')
            null_distribution.append(scores.mean())
        except Exception:
            null_distribution.append(0.0)

    return {
        'observed_r2': observed_r2,
        'null_distribution': null_distribution
    }

def calculate_p_value(observed: float, null_dist: List[float]) -> float:
    """Calculates p-value from observed and null distribution."""
    count = sum(1 for x in null_dist if x >= observed)
    return count / len(null_dist)

def run_sensitivity_analysis():
    """Runs sensitivity analysis by sweeping alpha values."""
    logger.info("Starting Sensitivity Analysis")
    
    df = load_processed_data()
    if df.empty:
        return

    target_col = 'compound_concentration' if 'compound_concentration' in df.columns else df.select_dtypes(include=[np.number]).columns[-1]
    feature_cols = [c for c in df.columns if c != target_col and c != 'population_id']
    
    X = df[feature_cols].fillna(0)
    y = df[target_col].fillna(0)

    alphas = [0.01, 0.1, 1.0, 10.0, 100.0]
    results = []

    from sklearn.linear_model import LassoCV
    from sklearn.model_selection import cross_val_score, KFold

    cv = KFold(n_splits=5, shuffle=True, random_state=42)

    for alpha in alphas:
        model = LassoCV(alphas=[alpha], random_state=42)
        try:
            scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
            results.append({'alpha': alpha, 'mean_r2': scores.mean(), 'std_r2': scores.std()})
        except Exception as e:
            logger.warning(f"Failed for alpha={alpha}: {e}")
            results.append({'alpha': alpha, 'mean_r2': 0.0, 'std_r2': 0.0})

    results_df = pd.DataFrame(results)
    output_path = PROJECT_ROOT / "data" / "processed" / "sensitivity_analysis.csv"
    results_df.to_csv(output_path, index=False)
    logger.info(f"Sensitivity analysis saved to {output_path}")

def main(*args, **kwargs):
    """Entry point for evaluation script."""
    configure_root_logger()
    run_permutation_test()
    run_sensitivity_analysis()

if __name__ == "__main__":
    main()
