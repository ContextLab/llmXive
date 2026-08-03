"""
Validation module for spatial cross-validation and model comparison.
Implements 5-fold spatial cross-validation ensuring spatially disjoint train/test sets.
"""
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from sklearn.model_selection import KFold
import json

from logger import get_logger, get_project_root
from models import fit_ols_model, fit_spatial_models, build_spatial_weights, SpatialWeightMatrixError

logger = get_logger(__name__)

def generate_spatial_blocks(df: pd.DataFrame, n_blocks: int = 5) -> pd.Series:
    """
    Generates spatially disjoint blocks for cross-validation.
    Uses a simple coordinate-based binning strategy to ensure spatial separation.
    
    Args:
        df: DataFrame containing geometry or x/y coordinates
        n_blocks: Number of spatial blocks (default 5)
        
    Returns:
        Series of block assignments (0 to n_blocks-1)
    """
    if 'geometry' in df.columns and df['geometry'].geom_type.iloc[0] in ['Point', 'MultiPoint']:
        # Extract centroids if geometry is present
        x_coords = df['geometry'].centroid.x.values
        y_coords = df['geometry'].centroid.y.values
    elif 'x' in df.columns and 'y' in df.columns:
        x_coords = df['x'].values
        y_coords = df['y'].values
    else:
        raise ValueError("DataFrame must contain 'geometry' (Point) or 'x'/'y' columns for spatial blocking")
    
    # Combine x and y into a single spatial index using Hilbert curve approximation
    # For simplicity, we use a space-filling curve approach: sort by x then y
    # Create a 2D grid index
    x_min, x_max = x_coords.min(), x_coords.max()
    y_min, y_max = y_coords.min(), y_coords.max()
    
    # Normalize coordinates to [0, 1]
    x_norm = (x_coords - x_min) / (x_max - x_min + 1e-10)
    y_norm = (y_coords - y_min) / (y_max - y_min + 1e-10)
    
    # Create a combined spatial index (simple Hilbert-like approximation)
    # Using Morton code approximation: interleave bits
    # For simplicity, we'll use a simpler approach: sort by x, then assign blocks
    # This ensures spatial continuity along the x-axis
    sorted_indices = np.argsort(x_norm)
    n_samples = len(sorted_indices)
    block_size = n_samples // n_blocks
    
    blocks = np.zeros(n_samples, dtype=int)
    for i, idx in enumerate(sorted_indices):
        block_idx = min(i // block_size, n_blocks - 1)
        blocks[idx] = block_idx
    
    return pd.Series(blocks, index=df.index)

def spatial_kfold_split(df: pd.DataFrame, n_splits: int = 5, random_state: int = 42) -> List[Tuple[pd.Index, pd.Index]]:
    """
    Generates spatially disjoint train/test splits for cross-validation.
    
    Args:
        df: DataFrame with spatial information
        n_splits: Number of folds (default 5)
        random_state: Random seed for reproducibility
        
    Returns:
        List of (train_index, test_index) tuples
    """
    np.random.seed(random_state)
    blocks = generate_spatial_blocks(df, n_splits)
    unique_blocks = np.unique(blocks)
    
    # Shuffle blocks to ensure randomness
    np.random.shuffle(unique_blocks)
    
    splits = []
    for i in range(n_splits):
        # Test set is one block
        test_mask = blocks == unique_blocks[i]
        # Train set is all other blocks
        train_mask = ~test_mask
        
        splits.append((
            df.index[train_mask],
            df.index[test_mask]
        ))
    
    return splits

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, model_type: str = 'OLS') -> Dict[str, float]:
    """
    Calculate performance metrics: RMSE, R², AIC (approximated).
    
    Args:
        y_true: True values
        y_pred: Predicted values
        model_type: Type of model (for AIC calculation)
        
    Returns:
        Dictionary with RMSE, R², and AIC
    """
    residuals = y_true - y_pred
    
    # RMSE
    rmse = np.sqrt(np.mean(residuals ** 2))
    
    # R²
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    # AIC approximation (requires number of parameters)
    # For OLS: k = number of features + 1 (intercept)
    # For spatial models: k = number of features + 1 (intercept) + 1 (spatial parameter)
    n_params = 5 if model_type == 'OLS' else 6  # Approximation
    n = len(y_true)
    aic = n * np.log(np.mean(residuals ** 2)) + 2 * n_params
    
    return {
        'rmse': float(rmse),
        'r2': float(r2),
        'aic': float(aic)
    }

def run_spatial_cross_validation(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: List[str],
    n_splits: int = 5,
    model_types: List[str] = ['OLS', 'Lag', 'Error'],
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Run 5-fold spatial cross-validation for multiple model types.
    Ensures spatially disjoint train/test sets.
    
    Args:
        df: Input DataFrame with spatial data
        target_col: Name of the target variable
        feature_cols: List of feature column names
        n_splits: Number of folds (default 5)
        model_types: List of model types to evaluate
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary containing cross-validation results for each model type
    """
    logger.info(f"Starting spatial cross-validation with {n_splits} folds")
    
    # Generate spatial splits
    splits = spatial_kfold_split(df, n_splits, random_state)
    
    results = {model_type: [] for model_type in model_types}
    
    for fold_idx, (train_idx, test_idx) in enumerate(splits):
        logger.info(f"Processing fold {fold_idx + 1}/{n_splits}")
        
        train_df = df.loc[train_idx].copy()
        test_df = df.loc[test_idx].copy()
        
        # Ensure spatial separation
        train_blocks = generate_spatial_blocks(train_df, n_splits)
        test_blocks = generate_spatial_blocks(test_df, n_splits)
        
        # Verify no overlap in blocks (simplified check)
        if len(set(train_blocks.unique()) & set(test_blocks.unique())) > 0:
            logger.warning(f"Fold {fold_idx + 1}: Some spatial overlap detected in blocks")
        
        for model_type in model_types:
            try:
                # Prepare data
                X_train = train_df[feature_cols].values
                y_train = train_df[target_col].values
                X_test = test_df[feature_cols].values
                y_test = test_df[target_col].values
                
                # Build spatial weights for training data
                # Note: For true spatial CV, we should rebuild weights for each fold
                # This is a simplified approach
                w = build_spatial_weights(train_df)
                
                # Fit model
                if model_type == 'OLS':
                    model_result = fit_ols_model(y_train, X_train, w=w)
                    y_pred = model_result['predictions']
                elif model_type in ['Lag', 'Error']:
                    model_result = fit_spatial_models(y_train, X_train, w=w, model_type=model_type)
                    y_pred = model_result['predictions']
                else:
                    logger.error(f"Unknown model type: {model_type}")
                    continue
                
                # Calculate metrics on test set
                metrics = calculate_metrics(y_test, y_pred, model_type)
                metrics['fold'] = fold_idx + 1
                results[model_type].append(metrics)
                
                logger.info(f"Fold {fold_idx + 1} {model_type} - RMSE: {metrics['rmse']:.4f}, R²: {metrics['r2']:.4f}")
                
            except Exception as e:
                logger.error(f"Error in fold {fold_idx + 1} for {model_type}: {str(e)}")
                # Record failure
                results[model_type].append({
                    'fold': fold_idx + 1,
                    'error': str(e),
                    'rmse': None,
                    'r2': None,
                    'aic': None
                })
    
    # Aggregate results
    aggregated_results = {}
    for model_type, fold_results in results.items():
        valid_results = [r for r in fold_results if r.get('rmse') is not None]
        if valid_results:
            aggregated_results[model_type] = {
                'mean_rmse': np.mean([r['rmse'] for r in valid_results]),
                'std_rmse': np.std([r['rmse'] for r in valid_results]),
                'mean_r2': np.mean([r['r2'] for r in valid_results]),
                'std_r2': np.std([r['r2'] for r in valid_results]),
                'mean_aic': np.mean([r['aic'] for r in valid_results]),
                'std_aic': np.std([r['aic'] for r in valid_results]),
                'fold_results': fold_results
            }
        else:
            aggregated_results[model_type] = {
                'mean_rmse': None,
                'std_rmse': None,
                'mean_r2': None,
                'std_r2': None,
                'mean_aic': None,
                'std_aic': None,
                'fold_results': fold_results,
                'error': "No valid results for this model type"
            }
    
    return aggregated_results

def main():
    """
    Main function to run spatial cross-validation on the harmonized dataset.
    """
    logger.info("Starting spatial cross-validation pipeline")
    
    # Load harmonized data
    project_root = get_project_root()
    data_path = project_root / "data" / "processed" / "harmonized.parquet"
    
    if not data_path.exists():
        logger.error(f"Harmonized data not found at {data_path}")
        return None
    
    try:
        df = pd.read_parquet(data_path)
        logger.info(f"Loaded {len(df)} records from {data_path}")
    except Exception as e:
        logger.error(f"Failed to load harmonized data: {str(e)}")
        return None
    
    # Define target and features
    target_col = 'noise_level_db'
    feature_cols = ['traffic_volume', 'population_density', 'land_use_commercial', 'land_use_residential']
    
    # Filter out rows with missing values in target or features
    valid_cols = [target_col] + feature_cols
    df_clean = df.dropna(subset=valid_cols)
    
    if len(df_clean) < 10:
        logger.error("Not enough valid data points for cross-validation")
        return None
    
    logger.info(f"Running cross-validation on {len(df_clean)} valid records")
    
    # Run spatial cross-validation
    results = run_spatial_cross_validation(
        df=df_clean,
        target_col=target_col,
        feature_cols=feature_cols,
        n_splits=5,
        model_types=['OLS', 'Lag', 'Error'],
        random_state=42
    )
    
    # Save results
    output_path = project_root / "data" / "processed" / "cv_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Cross-validation results saved to {output_path}")
    
    # Print summary
    print("\n=== Spatial Cross-Validation Summary ===")
    for model_type, summary in results.items():
        if summary.get('mean_rmse') is not None:
            print(f"{model_type}:")
            print(f"  Mean RMSE: {summary['mean_rmse']:.4f} (+/- {summary['std_rmse']:.4f})")
            print(f"  Mean R²: {summary['mean_r2']:.4f} (+/- {summary['std_r2']:.4f})")
            print(f"  Mean AIC: {summary['mean_aic']:.4f} (+/- {summary['std_aic']:.4f})")
        else:
            print(f"{model_type}: Failed to converge")
    
    return results

if __name__ == "__main__":
    main()