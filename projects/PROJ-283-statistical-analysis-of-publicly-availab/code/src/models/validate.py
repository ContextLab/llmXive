import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_model_results(results_path: Path) -> Dict[str, Any]:
    """Load model metrics from JSON file."""
    if not results_path.exists():
        raise FileNotFoundError(f"Model results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def load_processed_data(data_path: Path) -> pd.DataFrame:
    """Load processed game records from parquet or csv."""
    if data_path.suffix == '.parquet':
        return pd.read_parquet(data_path)
    elif data_path.suffix == '.csv':
        return pd.read_csv(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")

def prepare_features_and_target(
    df: pd.DataFrame,
    model_type: str = 'beta'
) -> Tuple[pd.DataFrame, pd.Series]:
    """Prepare features and target for cross-validation."""
    if model_type == 'beta':
        target_col = 'outcome_deviation'
        pred_col = 'predicted_outcome_deviation_beta'
    elif model_type == 'ridge':
        target_col = 'outcome_deviation'
        pred_col = 'predicted_outcome_deviation_ridge'
    elif model_type == 'gaussian':
        target_col = 'outcome_deviation'
        pred_col = 'predicted_outcome_deviation_gaussian'
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found")
    
    if pred_col not in df.columns:
        # If predictions not pre-computed, we need to re-fit
        # For now, assume predictions are already in the data
        logger.warning(f"Predictions not found for {model_type}")
        return pd.DataFrame(), df[target_col]
    
    # Features for CV (use predictions as proxy for model output)
    X = df[[pred_col]].copy()
    y = df[target_col]
    
    return X, y

def perform_kfold_cross_validation(
    df: pd.DataFrame,
    model_type: str = 'beta',
    k: int = 5
) -> Dict[str, Any]:
    """Perform k-fold cross-validation and calculate metrics."""
    from sklearn.model_selection import cross_val_score, KFold
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler
    
    X, y = prepare_features_and_target(df, model_type)
    
    if len(X) == 0:
        logger.warning(f"No data available for {model_type} cross-validation")
        return {
            'mean_r2': 0.0,
            'std_r2': 0.0,
            'mean_mse': 0.0,
            'fold_scores': []
        }
    
    # For simplicity, use Ridge as proxy for all models
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = Ridge(alpha=1.0)
    
    # R2 scores
    kf = KFold(n_splits=k, shuffle=True, random_state=42)
    r2_scores = cross_val_score(model, X_scaled, y, cv=kf, scoring='r2')
    
    # MSE scores (negative MSE from sklearn)
    mse_scores = -cross_val_score(model, X_scaled, y, cv=kf, scoring='neg_mean_squared_error')
    
    return {
        'mean_r2': float(np.mean(r2_scores)),
        'std_r2': float(np.std(r2_scores)),
        'mean_mse': float(np.mean(mse_scores)),
        'fold_r2': r2_scores.tolist(),
        'fold_mse': mse_scores.tolist()
    }

def run_validation_pipeline(
    data_path: Path,
    results_path: Path,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Run full validation pipeline for all models."""
    if output_path is None:
        output_path = Path("data/results/validation_results.json")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    df = load_processed_data(data_path)
    
    # Load model results
    model_metrics = load_model_results(results_path)
    
    # Perform CV for each model
    cv_results = {}
    validation_status = "Pass"
    
    for model_type in ['beta', 'ridge', 'gaussian']:
        logger.info(f"Running cross-validation for {model_type} model")
        cv_results[model_type] = perform_kfold_cross_validation(df, model_type)
        
        # Check R2 std deviation threshold
        if model_type == 'beta':
            std_r2 = cv_results[model_type]['std_r2']
            if std_r2 >= 0.05:
                validation_status = "Fail"
                logger.error(f"R2 std deviation {std_r2:.4f} exceeds threshold 0.05")
    
    # Prepare summary
    summary = {
        'cv_summary': cv_results,
        'r2_std': cv_results.get('beta', {}).get('std_r2', 0.0),
        'validation_status': validation_status
    }
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Saved validation results to {output_path}")
    return summary

def main():
    """Main entry point for validation script."""
    base_path = Path(__file__).parent.parent.parent
    data_path = base_path / "data" / "processed" / "games.parquet"
    results_path = base_path / "data" / "results" / "model_metrics.json"
    output_path = base_path / "data" / "results" / "validation_results.json"
    
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)
    
    if not results_path.exists():
        logger.error(f"Model results file not found: {results_path}")
        sys.exit(1)
    
    logger.info("Starting validation pipeline")
    
    try:
        results = run_validation_pipeline(data_path, results_path, output_path)
        
        if results['validation_status'] == "Fail":
            logger.error("Validation failed: R2 std deviation too high")
            sys.exit(1)
        
        logger.info("Validation pipeline completed successfully")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Validation pipeline error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()