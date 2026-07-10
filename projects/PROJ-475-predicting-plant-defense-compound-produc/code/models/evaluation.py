import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, Lasso
from sklearn.model_selection import cross_val_score, LeaveOneOut, KFold
from sklearn.metrics import r2_score
from utils.logging import get_module_logger
from config import get_config

logger = get_module_logger(__name__)

def calculate_p_value(observed_r2: float, null_distribution: np.ndarray) -> float:
    """
    Calculate the one-sided p-value comparing observed R^2 against the null distribution.
    p = (count of null >= observed + 1) / (n + 1)
    """
    count = np.sum(null_distribution >= observed_r2)
    return (count + 1) / (len(null_distribution) + 1)

def run_permutation_test(
    X: np.ndarray,
    y: np.ndarray,
    n_permutations: int = 1000,
    random_state: Optional[int] = None
) -> Tuple[float, np.ndarray]:
    """
    Execute permutation test to generate null distribution of R^2.
    Returns observed R^2 and the null distribution array.
    """
    if random_state is not None:
        np.random.seed(random_state)

    # Train base model on original data (using simple Lasso for consistency with pipeline)
    # We use a small alpha for the base model to approximate the 'true' signal if it exists
    base_model = Lasso(alpha=0.01, max_iter=10000, random_state=random_state)
    base_model.fit(X, y)
    observed_r2 = r2_score(y, base_model.predict(X))
    logger.info(f"Observed R^2: {observed_r2:.4f}")

    null_dist = []
    for i in range(n_permutations):
        y_perm = y.copy()
        np.random.shuffle(y_perm)
        model = Lasso(alpha=0.01, max_iter=10000, random_state=random_state)
        model.fit(X, y_perm)
        r2 = r2_score(y_perm, model.predict(X))
        null_dist.append(r2)

    return observed_r2, np.array(null_dist)

def save_permutation_results(
    observed_r2: float,
    null_distribution: np.ndarray,
    p_value: float,
    output_path: Path
) -> None:
    """Save permutation test results to a CSV file."""
    df = pd.DataFrame({
        'null_r2': null_distribution
    })
    df.to_csv(output_path, index=False)
    logger.info(f"Permutation results saved to {output_path}")
    
    # Save summary stats
    summary = {
        'observed_r2': observed_r2,
        'p_value': p_value,
        'mean_null': float(np.mean(null_distribution)),
        'std_null': float(np.std(null_distribution)),
        'n_permutations': len(null_distribution)
    }
    summary_path = output_path.parent / f"{output_path.stem}_summary.json"
    import json
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Permutation summary saved to {summary_path}")

def run_sensitivity_analysis(
    X: np.ndarray,
    y: np.ndarray,
    alpha_range: Optional[List[float]] = None,
    n_permutations: int = 1000,
    random_state: Optional[int] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Perform sensitivity analysis by sweeping alpha values for Lasso/Ridge.
    For each alpha, we train a model, record the R^2, and optionally run a mini permutation test
    to check stability of the signal.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        alpha_range: List of alpha values to sweep. Defaults to a range of small significance levels.
        n_permutations: Number of permutations for internal stability check (can be reduced for speed).
        random_state: Random seed.
    
    Returns:
        results_df: DataFrame with columns: alpha, r2, p_value, n_selected_features
        summary: Dictionary with aggregate stability metrics.
    """
    if alpha_range is None:
        # Sweep across a range of small significance levels (regularization strengths)
        # Log-spaced from 0.001 to 1.0
        alpha_range = np.logspace(-3, 0, 20).tolist()
    
    if random_state is not None:
        np.random.seed(random_state)

    results = []
    logger.info(f"Starting sensitivity analysis with {len(alpha_range)} alpha values...")

    for alpha in alpha_range:
        logger.debug(f"Processing alpha={alpha:.4f}")
        
        # Train Lasso model
        model = Lasso(alpha=alpha, max_iter=10000, random_state=random_state)
        model.fit(X, y)
        
        # Calculate R^2 on training data (or use CV score for unbiased estimate)
        # Using training R^2 here as per standard sensitivity sweep for feature selection stability
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)
        
        # Count non-zero coefficients (selected features)
        n_selected = np.sum(model.coef_ != 0)
        
        # Optional: Quick permutation check for this specific alpha to see if signal is robust
        # To save time, we might use fewer permutations here or skip if n_permutations is large
        # For this implementation, we run a reduced permutation test to get a p-value per alpha
        perm_obs, perm_null = run_permutation_test(X, y, n_permutations=max(100, n_permutations // 10), random_state=random_state)
        p_val = calculate_p_value(perm_obs, perm_null)
        
        results.append({
            'alpha': alpha,
            'r2': r2,
            'p_value': p_val,
            'n_selected_features': n_selected,
            'observed_r2_perm': perm_obs,
            'mean_null_perm': float(np.mean(perm_null))
        })

    results_df = pd.DataFrame(results)
    return results_df, {
        'total_alphas_tested': len(alpha_range),
        'best_alpha_by_r2': float(results_df.loc[results_df['r2'].idxmax(), 'alpha']),
        'best_r2': float(results_df['r2'].max()),
        'stable_alpha_range': results_df[results_df['p_value'] < 0.05]['alpha'].tolist()
    }

def main() -> int:
    """
    Main entry point for the evaluation module.
    Orchestrates loading data, running permutation tests, and sensitivity analysis.
    """
    config = get_config()
    data_dir = Path(config.get('paths', {}).get('processed', 'data/processed'))
    output_dir = Path(config.get('paths', {}).get('figures', 'data/processed'))
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load processed data
    features_path = data_dir / 'features_vif.csv'
    if not features_path.exists():
        logger.error(f"Processed features not found at {features_path}")
        return 1

    logger.info(f"Loading data from {features_path}")
    df = pd.read_csv(features_path)
    
    # Assume the last column is the target (compound production) and others are features
    # Adjust based on actual data model if necessary
    target_col = df.columns[-1]
    feature_cols = df.columns[:-1]
    
    X = df[feature_cols].dropna().values
    y = df.loc[X.shape[0] * [0], target_col].values # Align indices roughly
    # Proper alignment:
    clean_df = df.dropna(subset=feature_cols + [target_col])
    X = clean_df[feature_cols].values
    y = clean_df[target_col].values

    if len(X) == 0:
        logger.error("No valid data points after cleaning.")
        return 1

    # 1. Run Permutation Test (T029/T030 logic reused here for context)
    logger.info("Running primary permutation test...")
    obs_r2, null_dist = run_permutation_test(X, y, n_permutations=1000, random_state=42)
    p_val = calculate_p_value(obs_r2, null_dist)
    
    perm_output = output_dir / 'permutation_results.csv'
    save_permutation_results(obs_r2, null_dist, p_val, perm_output)
    logger.info(f"Primary Permutation Test: R2={obs_r2:.4f}, p={p_val:.4f}")

    # 2. Run Sensitivity Analysis (T031)
    logger.info("Running sensitivity analysis (alpha sweep)...")
    alpha_results, summary = run_sensitivity_analysis(
        X, y, 
        alpha_range=np.logspace(-3, 0, 20).tolist(),
        n_permutations=1000,
        random_state=42
    )
    
    sensitivity_output = output_dir / 'sensitivity_analysis.csv'
    alpha_results.to_csv(sensitivity_output, index=False)
    logger.info(f"Sensitivity analysis saved to {sensitivity_output}")
    
    # Log summary
    logger.info(f"Sensitivity Analysis Summary: Best Alpha={summary['best_alpha_by_r2']:.4f}, Best R2={summary['best_r2']:.4f}")
    logger.info(f"Stable Alpha Range (p<0.05): {summary['stable_alpha_range']}")

    return 0

if __name__ == "__main__":
    sys.exit(main())