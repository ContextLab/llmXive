"""
Resampling Engine for OLS Stability Analysis.

Implements robust OLS fitting loops across dataset subsets,
handling singular matrices and logging warnings.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import OLSInfluence
import warnings

from src.utils.config import SAMPLE_SIZE_TIERS
from src.models.data_models import StabilityResult, DatasetProfile

logger = logging.getLogger(__name__)

def _validate_subset_singularity(X: pd.DataFrame, y: pd.Series) -> bool:
    """
    Check if the subset is likely to cause a singular matrix error.
    Returns True if the subset is valid for fitting, False otherwise.
    """
    n_samples, n_features = X.shape
    
    # Constraint: subset size >= 10 * number of predictors
    if n_samples < 10 * n_features:
        logger.warning(f"Subset too small: {n_samples} samples for {n_features} features. Skipping.")
        return False
    
    # Check for constant columns or zero variance which cause singularity
    if X.std().min() == 0:
        logger.warning("Subset contains constant columns. Skipping.")
        return False
    
    return True

def _fit_ols_robust(X: pd.DataFrame, y: pd.Series) -> Optional[Tuple[np.ndarray, float, float]]:
    """
    Fit OLS model with robust error handling for singular matrices.
    
    Returns:
        Tuple of (coefficients, condition_number, cooks_distance_max) or None if fit fails.
    """
    try:
        # Add constant term for intercept
        X_const = sm.add_constant(X)
        
        # Check for singularity before fitting
        if not _validate_subset_singularity(X_const, y):
            return None
        
        # Fit OLS model
        model = sm.OLS(y, X_const)
        results = model.fit()
        
        # Extract coefficients (excluding intercept)
        coefficients = results.params[1:].values  # Skip intercept
        
        # Calculate condition number
        condition_number = np.linalg.cond(X_const.values)
        
        # Calculate Cook's distance
        influence = OLSInfluence(results)
        cooks_d = influence.cooks_distance[0]
        max_cooks_d = float(np.max(cooks_d))
        
        if condition_number > 1e10:
            logger.warning(f"High condition number detected: {condition_number:.2e}. Coefficients may be unstable.")
        
        return coefficients, condition_number, max_cooks_d

    except np.linalg.LinAlgError as e:
        logger.warning(f"Singular matrix error during OLS fit: {str(e)}. Skipping subset.")
        return None
    except Exception as e:
        logger.warning(f"Unexpected error during OLS fit: {str(e)}. Skipping subset.")
        return None

def generate_subsets(
    df: pd.DataFrame, 
    target_col: str, 
    feature_cols: List[str],
    seed: int = 42,
    n_subsets: int = 50
) -> List[Dict[str, Any]]:
    """
    Generate random subsets of the dataset across sample size tiers.
    
    Args:
        df: Full dataset
        target_col: Name of the target variable
        feature_cols: List of feature column names
        seed: Random seed for reproducibility
        n_subsets: Number of subsets to generate per tier
        
    Returns:
        List of dictionaries containing subset data and metadata
    """
    np.random.seed(seed)
    subsets = []
    
    n_total = len(df)
    
    for tier_pct in SAMPLE_SIZE_TIERS:
        tier_size = int(n_total * tier_pct / 100)
        
        if tier_size < 10:
            logger.warning(f"Tier {tier_pct}% results in too few samples ({tier_size}). Skipping tier.")
            continue
        
        for i in range(n_subsets):
            # Randomly sample without replacement
            subset_indices = np.random.choice(n_total, size=tier_size, replace=False)
            subset_df = df.iloc[subset_indices]
            
            subsets.append({
                'tier': tier_pct,
                'subset_index': i,
                'size': tier_size,
                'data': subset_df,
                'target': target_col,
                'features': feature_cols
            })
    
    return subsets

def run_resampling_loop(
    subsets: List[Dict[str, Any]],
    max_failures: int = 100
) -> List[StabilityResult]:
    """
    Execute robust OLS fitting on all subsets.
    
    Args:
        subsets: List of subset dictionaries from generate_subsets
        max_failures: Maximum number of consecutive failures before stopping
        
    Returns:
        List of StabilityResult objects containing fit results
    """
    results = []
    consecutive_failures = 0
    
    for subset_data in subsets:
        df_subset = subset_data['data']
        target = subset_data['target']
        features = subset_data['features']
        
        X = df_subset[features]
        y = df_subset[target]
        
        fit_result = _fit_ols_robust(X, y)
        
        if fit_result is None:
            consecutive_failures += 1
            if consecutive_failures >= max_failures:
                logger.error(f"Reached maximum consecutive failures ({max_failures}). Stopping resampling loop.")
                break
            continue
        
        coefficients, condition_number, max_cooks_d = fit_result
        
        result = StabilityResult(
            tier=subset_data['tier'],
            subset_id=subset_data['subset_index'],
            sample_size=subset_data['size'],
            coefficients=coefficients.tolist(),
            condition_number=condition_number,
            max_cooks_distance=max_cooks_d,
            success=True
        )
        results.append(result)
        consecutive_failures = 0
        
        logger.info(f"Successfully fitted subset: tier={subset_data['tier']}%, "
                   f"size={subset_data['size']}, id={subset_data['subset_index']}")
    
    logger.info(f"Resampling loop completed. {len(results)} successful fits out of {len(subsets)} subsets.")
    return results

def ingest_and_profile(
    dataset_path: str,
    target_col: str,
    feature_cols: List[str],
    output_path: str,
    n_subsets: int = 50,
    seed: int = 42
) -> None:
    """
    Main pipeline function to run resampling experiment on a dataset.
    
    Args:
        dataset_path: Path to the input dataset (CSV or similar)
        target_col: Name of the target variable
        feature_cols: List of feature column names
        output_path: Path to save the stability results
        n_subsets: Number of subsets per tier
        seed: Random seed
    """
    # Load dataset
    logger.info(f"Loading dataset from {dataset_path}")
    df = pd.read_csv(dataset_path)
    
    # Validate columns
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset")
    for col in feature_cols:
        if col not in df.columns:
            raise ValueError(f"Feature column '{col}' not found in dataset")
    
    # Generate subsets
    logger.info(f"Generating {n_subsets} subsets per tier across {SAMPLE_SIZE_TIERS}% tiers")
    subsets = generate_subsets(df, target_col, feature_cols, seed=seed, n_subsets=n_subsets)
    
    # Run resampling loop
    logger.info("Starting robust OLS fitting loop")
    results = run_resampling_loop(subsets)
    
    # Save results
    logger.info(f"Saving {len(results)} results to {output_path}")
    results_df = pd.DataFrame([
        {
            'tier': r.tier,
            'subset_id': r.subset_id,
            'sample_size': r.sample_size,
            'coefficients': r.coefficients,
            'condition_number': r.condition_number,
            'max_cooks_distance': r.max_cooks_distance,
            'success': r.success
        }
        for r in results
    ])
    
    # Flatten coefficients for CSV storage
    for i, coef_name in enumerate(feature_cols):
        results_df[f'coef_{coef_name}'] = results_df['coefficients'].apply(
            lambda x: x[i] if len(x) > i else None
        )
    
    results_df.drop(columns=['coefficients'], inplace=True)
    results_df.to_csv(output_path, index=False)
    
    logger.info(f"Resampling experiment completed successfully. Results saved to {output_path}")