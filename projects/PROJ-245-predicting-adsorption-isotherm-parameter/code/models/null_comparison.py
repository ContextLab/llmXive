"""
Null Model Comparison Module.

Performs statistical comparison between the full model and the null model.
Implements paired t-test or Wilcoxon signed-rank test on RMSEs.
Verifies RMSE improvement is at least 20% lower than null model.
Outputs 95% confidence intervals via bootstrapping.
"""

import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from scipy import stats

# Ensure imports work when run as script or module
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from models.evaluate import bootstrap_confidence_intervals
    from models.null_model import run_null_model_baseline
else:
    from ..models.evaluate import bootstrap_confidence_intervals
    from ..models.null_model import run_null_model_baseline

logger = logging.getLogger(__name__)

def ensure_dirs(output_dir: Path) -> None:
    """Ensure output directory exists."""
    output_dir.mkdir(parents=True, exist_ok=True)

def load_preprocessed_data(data_path: Path) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load preprocessed data from parquet file.
    Returns features (X), target (y), and feature names.
    """
    import pandas as pd
    
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_parquet(data_path)
    
    # Identify feature columns (exclude target and metadata)
    target_cols = ['langmuir_capacity', 'henry_constant']
    metadata_cols = ['material_id', 'adsorbent_structure_id', 'descriptor_hash']
    
    feature_cols = [col for col in df.columns 
                   if col not in target_cols + metadata_cols]
    
    if len(feature_cols) == 0:
        raise ValueError("No feature columns found in dataset")
    
    X = df[feature_cols].values
    y = df['langmuir_capacity'].values
    
    return X, y, feature_cols

def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Root Mean Squared Error."""
    return np.sqrt(np.mean((y_true - y_pred) ** 2))

def calculate_null_model_metrics(
    X: np.ndarray, 
    y: np.ndarray, 
    folds_path: Path,
    exclusion_list_path: Optional[Path] = None
) -> List[float]:
    """
    Calculate RMSE for null model across folds.
    Returns list of RMSEs (one per fold).
    """
    logger.info("Calculating null model metrics across folds...")
    
    # Load folds
    with open(folds_path, 'r') as f:
        folds_data = json.load(f)
    
    fold_rmses = []
    
    for fold_idx, fold_info in enumerate(folds_data):
        train_indices = fold_info['train_indices']
        test_indices = fold_info['test_indices']
        
        # Train null model on training set (predict mean)
        y_train = y[train_indices]
        y_test = y[test_indices]
        
        null_prediction = np.mean(y_train)
        y_pred_null = np.full_like(y_test, null_prediction, dtype=float)
        
        # Calculate RMSE
        rmse = calculate_rmse(y_test, y_pred_null)
        fold_rmses.append(rmse)
        
        logger.debug(f"Fold {fold_idx}: Null RMSE = {rmse:.4f}")
    
    return fold_rmses

def calculate_trained_model_metrics(
    X: np.ndarray, 
    y: np.ndarray, 
    folds_path: Path,
    model_path: Path,
    exclusion_list_path: Optional[Path] = None
) -> List[float]:
    """
    Calculate RMSE for trained model across folds.
    Returns list of RMSEs (one per fold).
    """
    logger.info("Calculating trained model metrics across folds...")
    
    import joblib
    
    # Load the best model
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    model = joblib.load(model_path)
    
    # Load folds
    with open(folds_path, 'r') as f:
        folds_data = json.load(f)
    
    fold_rmses = []
    
    for fold_idx, fold_info in enumerate(folds_data):
        train_indices = fold_info['train_indices']
        test_indices = fold_info['test_indices']
        
        X_train = X[train_indices]
        y_train = y[train_indices]
        X_test = X[test_indices]
        y_test = y[test_indices]
        
        # Predict using trained model
        y_pred = model.predict(X_test)
        
        # Calculate RMSE
        rmse = calculate_rmse(y_test, y_pred)
        fold_rmses.append(rmse)
        
        logger.debug(f"Fold {fold_idx}: Full Model RMSE = {rmse:.4f}")
    
    return fold_rmses

def run_cross_fold_comparison(
    null_rmses: List[float], 
    full_rmses: List[float],
    improvement_threshold: float = 0.20
) -> Dict[str, Any]:
    """
    Perform paired statistical test between null and full model RMSEs.
    
    Args:
        null_rmses: List of RMSEs from null model across folds
        full_rmses: List of RMSEs from full model across folds
        improvement_threshold: Minimum required improvement (default 0.20 = 20%)
    
    Returns:
        Dictionary with comparison results
    """
    logger.info("Running cross-fold statistical comparison...")
    
    if len(null_rmses) != len(full_rmses):
        raise ValueError("Number of folds must match for both models")
    
    if len(null_rmses) < 2:
        raise ValueError("Need at least 2 folds for statistical comparison")
    
    null_rmses = np.array(null_rmses)
    full_rmses = np.array(full_rmses)
    
    # Calculate mean RMSEs
    rmse_null_mean = np.mean(null_rmses)
    rmse_full_mean = np.mean(full_rmses)
    
    # Calculate improvement percentage
    improvement_pct = (rmse_null_mean - rmse_full_mean) / rmse_null_mean
    
    logger.info(f"Null Model Mean RMSE: {rmse_null_mean:.4f}")
    logger.info(f"Full Model Mean RMSE: {rmse_full_mean:.4f}")
    logger.info(f"Improvement: {improvement_pct*100:.2f}%")
    
    # Check if improvement meets threshold
    meets_threshold = improvement_pct >= improvement_threshold
    logger.info(f"Meets {improvement_threshold*100}% improvement threshold: {meets_threshold}")
    
    # Perform paired statistical test
    # Use Wilcoxon signed-rank test (non-parametric, robust to non-normality)
    # If data is normally distributed, could use t-test
    stat, p_value = stats.wilcoxon(null_rmses, full_rmses)
    
    logger.info(f"Wilcoxon statistic: {stat:.4f}")
    logger.info(f"P-value: {p_value:.6f}")
    
    # Check statistical significance (p < 0.05)
    is_significant = p_value < 0.05
    logger.info(f"Statistically significant (p < 0.05): {is_significant}")
    
    # Calculate 95% confidence interval for the difference using bootstrapping
    # Bootstrap the difference in RMSEs
    n_resamples = 1000
    random_state = 42
    
    np.random.seed(random_state)
    differences = null_rmses - full_rmses
    bootstrap_diffs = []
    
    for _ in range(n_resamples):
        sampled_indices = np.random.choice(len(differences), size=len(differences), replace=True)
        sampled_diff = np.mean(differences[sampled_indices])
        bootstrap_diffs.append(sampled_diff)
    
    ci_95 = np.percentile(bootstrap_diffs, [2.5, 97.5])
    
    logger.info(f"95% CI for improvement: [{ci_95[0]:.4f}, {ci_95[1]:.4f}]")
    
    result = {
        "rmse_full": float(rmse_full_mean),
        "rmse_null": float(rmse_null_mean),
        "improvement_pct": float(improvement_pct),
        "meets_threshold": bool(meets_threshold),
        "p_value": float(p_value),
        "is_significant": bool(is_significant),
        "ci_95": [float(ci_95[0]), float(ci_95[1])],
        "n_folds": len(null_rmses),
        "test_method": "wilcoxon_signed_rank"
    }
    
    return result

def main():
    """Main entry point for null model comparison."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compare full model vs null model")
    parser.add_argument("--data-dir", type=str, default="data/processed",
                      help="Directory containing preprocessed data")
    parser.add_argument("--model-path", type=str, default="trained_models/best_model.pkl",
                      help="Path to trained model file")
    parser.add_argument("--folds-path", type=str, default="data/results/folds.json",
                      help="Path to folds configuration")
    parser.add_argument("--output-path", type=str, default="data/validation/null_model_comparison.json",
                      help="Output path for comparison results")
    parser.add_argument("--threshold", type=float, default=0.20,
                      help="Minimum improvement threshold (default: 0.20)")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting null model comparison...")
    
    try:
        # Ensure output directory exists
        output_path = Path(args.output_path)
        ensure_dirs(output_path.parent)
        
        # Load data
        data_path = Path(args.data_dir) / "imputed_dataset.parquet"
        if not data_path.exists():
            # Try alternative path
            data_path = Path(args.data_dir) / "descriptors.parquet"
        
        X, y, feature_names = load_preprocessed_data(data_path)
        logger.info(f"Loaded {len(y)} samples with {len(feature_names)} features")
        
        # Calculate null model metrics
        folds_path = Path(args.folds_path)
        if not folds_path.exists():
            raise FileNotFoundError(f"Folds file not found: {folds_path}")
        
        null_rmses = calculate_null_model_metrics(X, y, folds_path)
        
        # Calculate full model metrics
        model_path = Path(args.model_path)
        full_rmses = calculate_trained_model_metrics(X, y, folds_path, model_path)
        
        # Run comparison
        result = run_cross_fold_comparison(null_rmses, full_rmses, args.threshold)
        
        # Save results
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("NULL MODEL COMPARISON RESULTS")
        print("="*60)
        print(f"Null Model RMSE:   {result['rmse_null']:.4f}")
        print(f"Full Model RMSE:   {result['rmse_full']:.4f}")
        print(f"Improvement:       {result['improvement_pct']*100:.2f}%")
        print(f"Meets Threshold:   {result['meets_threshold']}")
        print(f"P-value:           {result['p_value']:.6f}")
        print(f"Significant:       {result['is_significant']}")
        print(f"95% CI:            [{result['ci_95'][0]:.4f}, {result['ci_95'][1]:.4f}]")
        print("="*60)
        
        if not result['meets_threshold']:
            logger.warning(f"Improvement ({result['improvement_pct']*100:.2f}%) does not meet threshold ({args.threshold*100}%)")
        
        if not result['is_significant']:
            logger.warning(f"Results not statistically significant (p={result['p_value']:.6f})")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during null model comparison: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())