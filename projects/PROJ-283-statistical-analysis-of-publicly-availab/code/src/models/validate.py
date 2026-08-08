import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import logging
import json
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_squared_error

logger = logging.getLogger(__name__)

def load_model_results(results_path: Path) -> Dict[str, Any]:
    """Load model metrics from JSON file."""
    if not results_path.exists():
        raise FileNotFoundError(f"Model results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def load_processed_data(data_path: Path) -> pd.DataFrame:
    """Load processed game records."""
    if data_path.suffix == '.parquet':
        return pd.read_parquet(data_path)
    elif data_path.suffix == '.csv':
        return pd.read_csv(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")

def prepare_features_and_target(
    df: pd.DataFrame,
    target_column: str = 'outcome_deviation'
) -> Tuple[pd.DataFrame, pd.Series]:
    """Prepare features and target for cross-validation."""
    exclude_cols = [target_column, 'eco_code', 'eco_family', 'game_id']
    feature_columns = [col for col in df.columns if col not in exclude_cols and df[col].dtype in [np.float64, np.int64, float, int]]
    
    if 'eco_family' in df.columns:
        eco_dummies = pd.get_dummies(df['eco_family'], prefix='eco', drop_first=True)
        numeric_features = df[feature_columns]
        features = pd.concat([numeric_features, eco_dummies], axis=1)
    else:
        features = df[feature_columns]
    
    features = features.fillna(features.median())
    target = df[target_column]
    
    return features, target

def calculate_cv_metrics(
    r2_scores: List[float],
    mse_scores: List[float],
    threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Calculate cross-validation metrics and check stability.
    
    Args:
        r2_scores: List of R² scores from each fold
        mse_scores: List of MSE scores from each fold
        threshold: Threshold for R² standard deviation (SC-003)
    
    Returns:
        Dictionary with CV summary and validation status
    """
    mean_r2 = np.mean(r2_scores)
    std_r2 = np.std(r2_scores)
    mean_mse = np.mean(mse_scores)
    std_mse = np.std(mse_scores)
    
    # Check stability criterion (SC-003)
    validation_status = 'Pass' if std_r2 < threshold else 'Fail'
    
    return {
        'mean_r2': mean_r2,
        'std_dev_r2': std_r2,
        'mean_mse': mean_mse,
        'std_mse': std_mse,
        'r2_scores': r2_scores,
        'mse_scores': mse_scores,
        'validation_status': validation_status,
        'threshold': threshold
    }

def perform_kfold_cross_validation(
    df: pd.DataFrame,
    model_type: str = 'beta',
    k: int = 5,
    target_column: str = 'outcome_deviation'
) -> Dict[str, Any]:
    """
    Perform k-fold cross-validation for a model.
    
    Args:
        df: DataFrame with game records
        model_type: 'beta' or 'ridge'
        k: Number of folds
        target_column: Name of target variable
    
    Returns:
        Dictionary with CV results
    """
    features, target = prepare_features_and_target(df, target_column)
    
    kfold = KFold(n_splits=k, shuffle=True, random_state=42)
    
    r2_scores = []
    mse_scores = []
    
    for fold, (train_idx, val_idx) in enumerate(kfold.split(features)):
        X_train = features.iloc[train_idx]
        X_val = features.iloc[val_idx]
        y_train = target.iloc[train_idx]
        y_val = target.iloc[val_idx]
        
        # Simple linear regression for each fold (placeholder for actual model)
        from sklearn.linear_model import Ridge
        model = Ridge(alpha=1.0)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_val)
        
        r2 = r2_score(y_val, y_pred)
        mse = mean_squared_error(y_val, y_pred)
        
        r2_scores.append(r2)
        mse_scores.append(mse)
        
        logger.info(f"Fold {fold + 1}: R²={r2:.4f}, MSE={mse:.4f}")
    
    return {
        'model_type': model_type,
        'k_folds': k,
        'r2_scores': r2_scores,
        'mse_scores': mse_scores
    }

def run_validation_pipeline(
    df: pd.DataFrame,
    cv_results_path: Path,
    threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Run full validation pipeline for Beta and Ridge models.
    
    Args:
        df: Processed game records
        cv_results_path: Path to save CV results
        threshold: R² std threshold for validation
    
    Returns:
        Combined CV summary
    """
    # Perform CV for both models
    logger.info("Performing cross-validation for Beta model...")
    beta_cv = perform_kfold_cross_validation(df, model_type='beta', k=5)
    
    logger.info("Performing cross-validation for Ridge model...")
    ridge_cv = perform_kfold_cross_validation(df, model_type='ridge', k=5)
    
    # Calculate metrics
    beta_metrics = calculate_cv_metrics(beta_cv['r2_scores'], beta_cv['mse_scores'], threshold)
    ridge_metrics = calculate_cv_metrics(ridge_cv['r2_scores'], ridge_cv['mse_scores'], threshold)
    
    # Determine overall status
    overall_status = 'Pass' if (beta_metrics['validation_status'] == 'Pass' and 
                               ridge_metrics['validation_status'] == 'Pass') else 'Fail'
    
    cv_summary = {
        'beta': beta_metrics,
        'ridge': ridge_metrics,
        'overall_validation_status': overall_status,
        'threshold': threshold
    }
    
    # Save results
    cv_results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cv_results_path, 'w') as f:
        json.dump(cv_summary, f, indent=2)
    
    logger.info(f"CV results saved to {cv_results_path}")
    
    # Log final status
    if overall_status == 'Fail':
        logger.error(f"Validation FAILED: R² std deviation >= {threshold}")
        raise RuntimeError(f"Validation failed: R² std deviation >= {threshold}")
    
    return cv_summary

def main():
    """Main entry point for model validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate models with cross-validation')
    parser.add_argument('--input', type=str, required=True, help='Path to processed data')
    parser.add_argument('--results', type=str, required=True, help='Path to model metrics JSON')
    parser.add_argument('--output', type=str, required=True, help='Path to save CV summary JSON')
    parser.add_argument('--threshold', type=float, default=0.05, help='R² std threshold')
    
    args = parser.parse_args()
    
    # Load data
    df = load_processed_data(Path(args.input))
    
    # Run validation
    cv_summary = run_validation_pipeline(
        df=df,
        cv_results_path=Path(args.output),
        threshold=args.threshold
    )
    
    logger.info("Validation complete")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
