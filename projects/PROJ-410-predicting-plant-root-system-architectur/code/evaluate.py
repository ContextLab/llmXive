import os
import sys
import logging
import argparse
import json
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, StratifiedKFold, KFold
from sklearn.linear_model import Lasso, ElasticNet, LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib

# Import shared configuration
try:
    from config import ensure_directories, PROJECT_ROOT
except ImportError:
    # Fallback for direct execution context
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    def ensure_directories():
        pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_model(model_path: str):
    """Load a trained model from disk."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    return joblib.load(model_path)

def load_split_data(data_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load training data and return features (X) and target (y)."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    df = pd.read_parquet(data_path)
    
    # Assume standard column naming convention: target is 'phenotype_value', rest are features
    # Or detect target column if 'phenotype_value' doesn't exist but 'target' does
    target_col = None
    possible_targets = ['phenotype_value', 'target', 'root_trait', 'value']
    for col in possible_targets:
        if col in df.columns:
            target_col = col
            break
    
    if target_col is None:
        # Fallback: assume last column is target
        target_col = df.columns[-1]
        logger.warning(f"Target column '{target_col}' inferred as last column.")

    y = df[target_col]
    X = df.drop(columns=[target_col])
    return X, y

def compute_cv_scores(
    model, 
    X: pd.DataFrame, 
    y: pd.Series, 
    n_splits: int = 5, 
    scoring: str = 'r2'
) -> Dict[str, float]:
    """
    Compute cross-validation scores for a given model.
    
    Args:
        model: The sklearn model instance.
        X: Feature matrix.
        y: Target vector.
        n_splits: Number of CV folds.
        scoring: Scoring metric string (e.g., 'r2', 'neg_mean_squared_error').
    
    Returns:
        Dictionary with mean and std of the scores.
    """
    # Determine CV strategy based on data type
    # If y is continuous, use KFold. If discrete (classification), use StratifiedKFold.
    # For regression tasks in this project, we assume continuous targets.
    if y.dtype in ['object', 'category']:
        # Discrete target - check if we can convert or if it's actually regression
        try:
            y_unique = y.unique()
            if len(y_unique) < 20: # Heuristic for classification-like continuous
                kfold = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
            else:
                kfold = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        except:
            kfold = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    else:
        kfold = KFold(n_splits=n_splits, shuffle=True, random_state=42)

    scores = cross_val_score(model, X, y, cv=kfold, scoring=scoring)
    
    return {
        "mean": float(np.mean(scores)),
        "std": float(np.std(scores)),
        "scores": scores.tolist()
    }

def evaluate_model_cv(
    model_name: str, 
    model_path: str, 
    data_path: str, 
    n_splits: int = 5
) -> Dict[str, Any]:
    """
    Load a model and data, then evaluate using cross-validation.
    
    Args:
        model_name: Name identifier for the model (e.g., 'Lasso', 'RF').
        model_path: Path to the saved model file.
        data_path: Path to the parquet data file.
        n_splits: Number of CV folds.
    
    Returns:
        Dictionary containing evaluation metrics.
    """
    logger.info(f"Evaluating {model_name} from {model_path} on {data_path}")
    
    model = load_model(model_path)
    X, y = load_split_data(data_path)
    
    # Handle high dimensionality if needed (optional preprocessing inside eval)
    # For now, assume model is trained on compatible X
    
    cv_results = compute_cv_scores(model, X, y, n_splits=n_splits)
    
    # Also compute single-split metrics on the full data for reference (not CV)
    # Note: This is for internal consistency check, not the final metric
    model.fit(X, y)
    y_pred = model.predict(X)
    
    single_split_metrics = {
        "r2": float(r2_score(y, y_pred)),
        "mae": float(mean_absolute_error(y, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y, y_pred)))
    }

    return {
        "model_name": model_name,
        "cv_scores": cv_results,
        "single_split_metrics": single_split_metrics,
        "n_samples": len(y),
        "n_features": X.shape[1]
    }

def run_cv_for_all_models(
    models_dir: str, 
    data_dir: str, 
    output_path: str, 
    n_splits: int = 5
) -> None:
    """
    Iterate over all models in a directory, evaluate them, and save results.
    
    Args:
        models_dir: Directory containing saved model files (.pkl or .joblib).
        data_dir: Directory containing data files.
        output_path: Path to save the JSON results.
        n_splits: Number of CV folds.
    """
    models_path = Path(models_dir)
    data_path = Path(data_dir)
    
    if not models_path.exists():
        raise FileNotFoundError(f"Models directory not found: {models_dir}")
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    # Ensure output directory exists
    ensure_directories()
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    # Map model filenames to names (e.g., 'lasso_model.joblib' -> 'Lasso')
    model_map = {
        'lasso': 'Lasso',
        'elasticnet': 'ElasticNet',
        'random_forest': 'RandomForest',
        'gradient_boosting': 'GradientBoosting',
        'linear': 'LinearRegression',
        'null': 'NullModel'
    }
    
    for model_file in models_path.glob('*.joblib'):
        model_name_key = model_file.stem.lower().replace('_', '')
        model_name = next((v for k, v in model_map.items() if k in model_name_key), model_file.stem)
        
        # Find corresponding data file (assume single unified data or specific naming)
        # For this implementation, we assume data_dir contains the specific split file
        # or we iterate over splits if multiple exist. 
        # Simplified: Assume one primary data file per condition or a generic one.
        # Let's look for a file matching the condition or a generic 'train.parquet'
        
        data_files = list(data_path.glob('*.parquet'))
        if not data_files:
            logger.warning(f"No data files found in {data_dir}, skipping {model_name}")
            continue
        
        # If multiple data files, we might need to evaluate per file.
        # For now, evaluate on the first found or a specific one if named.
        for df_path in data_files:
            try:
                eval_result = evaluate_model_cv(
                    model_name=model_name,
                    model_path=str(model_file),
                    data_path=str(df_path),
                    n_splits=n_splits
                )
                eval_result['data_source'] = str(df_path)
                results.append(eval_result)
            except Exception as e:
                logger.error(f"Error evaluating {model_name} on {df_path}: {e}")
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved evaluation results to {output_file}")

def apply_variance_filter(
    X: pd.DataFrame, 
    threshold: float = 0.0
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Remove features with variance below a threshold.
    
    This is a critical step for high-dimensional genomic data to remove
    invariant or near-invariant SNPs that provide no predictive power
    and can destabilize models.
    
    Args:
        X: Feature DataFrame.
        threshold: Minimum variance required to keep a feature. 
                   0.0 removes only strictly constant features.
    
    Returns:
        Tuple of (filtered DataFrame, list of dropped column names).
    """
    if X.empty:
        return X, []
    
    # Calculate variance for each column
    variances = X.var(axis=0)
    
    # Identify columns to drop
    cols_to_drop = variances[variances <= threshold].index.tolist()
    
    if cols_to_drop:
        logger.info(f"Dropping {len(cols_to_drop)} features with variance <= {threshold}")
        X_filtered = X.drop(columns=cols_to_drop)
    else:
        X_filtered = X
        logger.info("No features dropped by variance filtering.")
    
    return X_filtered, cols_to_drop

def main():
    parser = argparse.ArgumentParser(description="Evaluate models and apply variance filtering.")
    parser.add_argument("--models-dir", type=str, required=True, help="Directory containing model files")
    parser.add_argument("--data-dir", type=str, required=True, help="Directory containing data files")
    parser.add_argument("--output", type=str, default="data/processed/evaluation_results.json", help="Output JSON path")
    parser.add_argument("--n-splits", type=int, default=5, help="Number of CV splits")
    parser.add_argument("--variance-threshold", type=float, default=0.0, help="Variance threshold for filtering")
    parser.add_argument("--filter-only", action="store_true", help="Only run variance filtering on a specific data file and exit")
    parser.add_argument("--data-file", type=str, default=None, help="Specific data file to filter if --filter-only is set")
    
    args = parser.parse_args()
    
    if args.filter_only:
        if not args.data_file:
            parser.error("--data-file is required when using --filter-only")
        
        X, _ = load_split_data(args.data_file)
        X_filtered, dropped = apply_variance_filter(X, args.variance_threshold)
        
        output_path = Path(args.data_file).parent / f"{Path(args.data_file).stem}_filtered.parquet"
        X_filtered.to_parquet(output_path)
        logger.info(f"Filtered data saved to {output_path}")
        logger.info(f"Dropped columns: {dropped[:10]}... ({len(dropped)} total)")
        return

    # Run standard evaluation
    run_cv_for_all_models(
        models_dir=args.models_dir,
        data_dir=args.data_dir,
        output_path=args.output,
        n_splits=args.n_splits
    )

if __name__ == "__main__":
    main()