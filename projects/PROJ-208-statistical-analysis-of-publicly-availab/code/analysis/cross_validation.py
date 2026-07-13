"""
Leave-One-Repository-Out Cross-Validation for Mixed Effects Model.

Implements SC-004: Evaluate model generalizability by training on all but one
repository and testing on the held-out repository. Reports Mean Absolute Error (MAE)
and R-squared (R²) metrics for each fold.
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

# Project root handling
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.config import get_config, get_path
from utils.validators import validate_dataset_schema
from analysis.mixed_effects_model import fit_mixed_effects_model, extract_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned dataset from the processed directory."""
    config = get_config()
    data_path = get_path(config, "processed_cleaned_issues")
    
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {data_path}. "
                                "Run preprocessing pipeline first.")
    
    df = pd.read_csv(data_path)
    
    # Validate schema
    schema_path = get_path(config, "contracts_dataset")
    if schema_path.exists():
        validate_dataset_schema(df, schema_path)
    
    logger.info(f"Loaded {len(df)} issues from {data_path}")
    return df

def prepare_data_for_cv(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Prepare data for cross-validation.
    
    Returns:
      df: Cleaned dataframe with necessary columns
      repo_list: List of unique repositories
    """
    required_cols = ['resolution_time_hours', 'primary_language', 'repository']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Filter out infinite or NaN values in target
    df = df.dropna(subset=['resolution_time_hours'])
    df = df[~np.isinf(df['resolution_time_hours'])]
    
    repo_list = df['repository'].unique().tolist()
    logger.info(f"Prepared data for {len(repo_list)} repositories")
    return df, repo_list

def train_test_split_by_repo(df: pd.DataFrame, holdout_repo: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split data into train (all but holdout) and test (holdout) sets."""
    train_df = df[df['repository'] != holdout_repo].copy()
    test_df = df[df['repository'] == holdout_repo].copy()
    return train_df, test_df

def evaluate_model_on_fold(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    fixed_effects: List[str]
) -> Optional[Dict[str, Any]]:
    """
    Fit model on training data and evaluate on test data.
    
    Returns metrics dict or None if model fails to converge.
    """
    if len(train_df) < 10 or len(test_df) < 5:
        logger.warning(f"Fold too small: train={len(train_df)}, test={len(test_df)}")
        return None

    try:
        # Fit model on training set
        logger.info(f"Fitting model on {len(train_df)} samples...")
        model, summary = fit_mixed_effects_model(train_df, fixed_effects)
        
        # Check convergence
        if not model.converged:
            logger.warning("Model did not converge on training set")
            return None

        # Extract results to get fixed effects coefficients
        results = extract_results(model, summary)
        coeffs = results['fixed_effects_coefficients']
        
        # Predict on test set using fixed effects only
        # We need to align columns
        X_test = test_df[fixed_effects].copy()
        
        # Ensure all columns exist
        for col in fixed_effects:
            if col not in X_test.columns:
                # Handle categorical columns if necessary (simple dummy encoding)
                # For this implementation, we assume fixed_effects are already numeric or
                # the model handles them. If not, we need to re-fit the encoding.
                # Simplified approach: use the training model's encoding if available.
                # For robustness, we'll try to predict using the model's predict method
                # if available, or manually calculate.
                pass

        # Manual prediction using fixed effects coefficients
        # Intercept + sum(coeff * feature)
        intercept = coeffs.get('Intercept', 0)
        predictions = np.full(len(X_test), intercept)
        
        for feat, coeff in coeffs.items():
            if feat == 'Intercept':
                continue
            if feat in X_test.columns:
                predictions += coeff * X_test[feat]
            else:
                # If feature is categorical and not in test, skip or handle
                logger.debug(f"Feature {feat} not found in test set columns")

        # Calculate metrics
        y_true = test_df['resolution_time_hours'].values
        y_pred = predictions

        # Avoid log issues if target is 0 or negative (though cleaned data should be positive)
        # MAE
        mae = np.mean(np.abs(y_true - y_pred))
        
        # R-squared
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        return {
            "mae": float(mae),
            "r2": float(r2),
            "n_train": len(train_df),
            "n_test": len(test_df)
        }

    except Exception as e:
        logger.error(f"Error evaluating fold for {holdout_repo}: {e}", exc_info=True)
        return None

def run_leave_one_out_cv(
    df: pd.DataFrame,
    fixed_effects: List[str]
) -> Dict[str, Any]:
    """
    Perform leave-one-repository-out cross-validation.
    
    Args:
        df: Cleaned dataframe
        fixed_effects: List of fixed effect feature names
        
    Returns:
        Dictionary containing fold results and aggregate metrics
    """
    _, repo_list = prepare_data_for_cv(df)
    logger.info(f"Starting LOO-CV with {len(repo_list)} folds")
    
    fold_results = []
    
    for i, repo in enumerate(repo_list):
        logger.info(f"Fold {i+1}/{len(repo_list)}: Holding out {repo}")
        train_df, test_df = train_test_split_by_repo(df, repo)
        
        result = evaluate_model_on_fold(train_df, test_df, fixed_effects)
        if result:
            result['held_out_repo'] = repo
            result['fold_id'] = i
            fold_results.append(result)
    
    if not fold_results:
        raise RuntimeError("No folds completed successfully")
    
    # Aggregate metrics
    mae_values = [r['mae'] for r in fold_results]
    r2_values = [r['r2'] for r in fold_results]
    
    aggregate = {
        "total_folds": len(repo_list),
        "successful_folds": len(fold_results),
        "mean_mae": float(np.mean(mae_values)),
        "std_mae": float(np.std(mae_values)),
        "mean_r2": float(np.mean(r2_values)),
        "std_r2": float(np.std(r2_values)),
        "min_mae": float(np.min(mae_values)),
        "max_mae": float(np.max(mae_values)),
        "min_r2": float(np.min(r2_values)),
        "max_r2": float(np.max(r2_values)),
        "fold_details": fold_results
    }
    
    return aggregate

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save cross-validation results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for cross-validation analysis."""
    config = get_config()
    
    # Fixed effects to use (matching the mixed effects model specification)
    # Based on typical features: language, issue type, etc.
    # We assume these columns exist after preprocessing
    fixed_effects = ['primary_language_encoded', 'issue_type_encoded', 'priority_encoded']
    
    # Fallback if encoded columns don't exist, use raw categorical (model might handle)
    # For this implementation, we assume the preprocessing step created encoded columns
    # or the model handles categoricals. We'll try common names.
    available_cols = load_cleaned_data().columns.tolist()
    # Simple heuristic: pick numeric columns or encoded ones
    # In a real scenario, this should be defined in config
    if 'primary_language_encoded' not in available_cols:
        logger.warning("Encoded columns not found, attempting to use raw categorical columns")
        # This is a simplified fallback; real implementation needs proper encoding
        fixed_effects = ['primary_language', 'issue_type'] # Model must handle these

    try:
        df = load_cleaned_data()
        
        # Ensure target column exists
        if 'resolution_time_hours' not in df.columns:
            raise ValueError("Target column 'resolution_time_hours' not found in data")
        
        results = run_leave_one_out_cv(df, fixed_effects)
        
        output_path = get_path(config, "cv_results")
        save_results(results, output_path)
        
        # Print summary
        print("\n=== Cross-Validation Summary ===")
        print(f"Total Folds: {results['total_folds']}")
        print(f"Successful Folds: {results['successful_folds']}")
        print(f"Mean MAE: {results['mean_mae']:.2f} hours (+/- {results['std_mae']:.2f})")
        print(f"Mean R²: {results['mean_r2']:.3f} (+/- {results['std_r2']:.3f})")
        print(f"R² Range: [{results['min_r2']:.3f}, {results['max_r2']:.3f}]")
        
        return 0
        
    except Exception as e:
        logger.error(f"Cross-validation failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())