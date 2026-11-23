"""
Model validation module for cross-validation and metric calculation.

Implements T029 (Cross-Validation) and T030 (CV Metrics Calculation).
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import logging
import json
from sklearn.model_selection import KFold
from sklearn.linear_model import Ridge
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import norm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants from config (assuming defaults if not imported)
RANDOM_SEED = 42
SC_003_THRESHOLD = 0.05  # Target threshold for std_dev_r

def load_model_results(results_path: str = "data/results/model_metrics.json") -> Optional[Dict]:
    """Load model metrics from JSON file."""
    path = Path(results_path)
    if not path.exists():
        logger.warning(f"Model results file not found: {path}")
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load model results: {e}")
        return None

def load_processed_data(data_path: str = "data/processed/games.parquet") -> Optional[pd.DataFrame]:
    """Load processed game data."""
    path = Path(data_path)
    if not path.exists():
        logger.warning(f"Processed data file not found: {path}")
        return None
    try:
        if path.suffix == '.parquet':
            return pd.read_parquet(path)
        elif path.suffix == '.csv':
            return pd.read_csv(path)
        else:
            logger.error(f"Unsupported file format: {path.suffix}")
            return None
    except Exception as e:
        logger.error(f"Failed to load processed data: {e}")
        return None

def prepare_features_and_target(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare features (X) and target (y) from the dataframe.
    
    Returns:
        Tuple of (X, y) where X is a 2D numpy array and y is a 1D numpy array.
    """
    # Select features based on the schema and modeling requirements
    feature_cols = [
        'material_imbalance_move10',
        'avg_move_time_white',
        'avg_move_time_black',
        'white_rating',
        'black_rating'
    ]
    
    # Check if all required columns exist
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing feature columns: {missing_cols}. Using available ones.")
        feature_cols = [col for col in feature_cols if col in df.columns]
    
    if not feature_cols:
        raise ValueError("No valid feature columns found in the dataframe.")
    
    # Handle target variable
    target_col = 'outcome_deviation'
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataframe.")
    
    X = df[feature_cols].dropna().values
    y = df.loc[X.index, target_col].values if target_col in df.columns else np.array([])
    
    # Ensure y aligns with X after dropping NaNs
    valid_mask = ~np.isnan(X).any(axis=1)
    X = X[valid_mask]
    y = y[valid_mask]
    
    return X, y

def perform_kfold_cross_validation(
    X: np.ndarray, 
    y: np.ndarray, 
    model_type: str = "Ridge",
    k: int = 5,
    random_seed: int = RANDOM_SEED
) -> Dict[str, List[float]]:
    """
    Perform k-fold cross-validation for the specified model type.
    
    Args:
        X: Feature matrix (2D numpy array)
        y: Target vector (1D numpy array)
        model_type: Type of model to use ("Ridge", "Gaussian GLM", "Beta")
        k: Number of folds
        random_seed: Random seed for reproducibility
        
    Returns:
        Dictionary with keys 'r2_scores' and 'mse_scores' containing lists of scores.
    """
    kf = KFold(n_splits=k, shuffle=True, random_state=random_seed)
    
    r2_scores = []
    mse_scores = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        try:
            if model_type == "Ridge":
                model = Ridge(alpha=1.0, random_state=random_seed)
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                
            elif model_type == "Gaussian GLM":
                # Add intercept for statsmodels
                X_train_const = sm.add_constant(X_train)
                X_test_const = sm.add_constant(X_test)
                model = sm.GLM(y_train, X_train_const, family=sm.families.Gaussian()).fit()
                y_pred = model.predict(X_test_const)
                
            elif model_type == "Beta":
                # Beta regression requires y in (0, 1)
                # Assuming y has been transformed appropriately before calling this
                # If not, we apply a simple transformation here for demonstration
                y_train_beta = (y_train * 0.98 + 0.01)  # Map to (0, 1)
                y_test_beta = (y_test * 0.98 + 0.01)
                
                X_train_const = sm.add_constant(X_train)
                X_test_const = sm.add_constant(X_test)
                
                # Fit Beta regression
                model = sm.GLM(y_train_beta, X_train_const, family=sm.families.Beta()).fit()
                y_pred = model.predict(X_test_const)
                
                # For R2 calculation, we need to map back or use the transformed y
                # Here we calculate R2 on the transformed scale for consistency
                y_test_for_r2 = y_test_beta
                
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            # Calculate metrics
            ss_res = np.sum((y_test - y_pred) ** 2)
            ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
            mse = np.mean((y_test - y_pred) ** 2)
            
            r2_scores.append(float(r2))
            mse_scores.append(float(mse))
            
            logger.info(f"Fold {fold_idx + 1}/{k}: R²={r2:.4f}, MSE={mse:.4f}")
            
        except Exception as e:
            logger.error(f"Error in fold {fold_idx + 1}: {e}")
            # Skip this fold or handle error as needed
            continue
    
    return {
        'r2_scores': r2_scores,
        'mse_scores': mse_scores
    }

def calculate_cv_metrics(
    cv_results: Dict[str, List[float]],
    model_type: str = "Ridge"
) -> Dict[str, Any]:
    """
    Calculate CV metrics and validate against SC-003 threshold.
    
    Args:
        cv_results: Dictionary containing 'r2_scores' and 'mse_scores' lists.
        model_type: Type of model being evaluated.
        
    Returns:
        Dictionary containing 'cv_summary' and 'validation_status'.
        
    Raises:
        ValueError: If std_dev_r >= 0.05 (SC-003 threshold violation).
    """
    r2_scores = cv_results.get('r2_scores', [])
    mse_scores = cv_results.get('mse_scores', [])
    
    if not r2_scores:
        raise ValueError("No R² scores available for calculation.")
    
    # Calculate summary statistics
    mean_r2 = float(np.mean(r2_scores))
    std_r2 = float(np.std(r2_scores))
    mean_mse = float(np.mean(mse_scores)) if mse_scores else 0.0
    std_mse = float(np.std(mse_scores)) if mse_scores else 0.0
    
    cv_summary = {
        'mean_r2': mean_r2,
        'std_r2': std_r2,
        'mean_mse': mean_mse,
        'std_mse': std_mse,
        'n_folds': len(r2_scores),
        'r2_scores': r2_scores,
        'mse_scores': mse_scores
    }
    
    # Validate against SC-003 threshold
    # SC-003: std_dev_r < 0.05
    if std_r2 >= SC_003_THRESHOLD:
        error_msg = (
            f"SC-003 Validation Failed: Standard deviation of R² ({std_r2:.4f}) "
            f"exceeds threshold ({SC_003_THRESHOLD}). "
            f"Model performance is too variable across folds."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    validation_status = {
        'passed': True,
        'threshold': SC_003_THRESHOLD,
        'actual_std_r2': std_r2,
        'message': f"SC-003 passed: std_r2={std_r2:.4f} < {SC_003_THRESHOLD}"
    }
    
    logger.info(f"CV Metrics calculated for {model_type}: Mean R²={mean_r2:.4f}, Std R²={std_r2:.4f}")
    
    return {
        'cv_summary': cv_summary,
        'validation_status': validation_status
    }

def run_validation_pipeline(
    data_path: str = "data/processed/games.parquet",
    results_path: str = "data/results/model_metrics.json",
    k: int = 5,
    model_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run the full validation pipeline: load data, perform CV, calculate metrics.
    
    Args:
        data_path: Path to processed data file.
        results_path: Path to model metrics file.
        k: Number of CV folds.
        model_types: List of model types to evaluate. Defaults to ["Ridge"].
        
    Returns:
        Dictionary containing validation results for all model types.
    """
    if model_types is None:
        model_types = ["Ridge"]
    
    logger.info(f"Starting validation pipeline with models: {model_types}")
    
    # Load data
    df = load_processed_data(data_path)
    if df is None:
        raise FileNotFoundError(f"Processed data not found at {data_path}")
    
    # Prepare features and target
    X, y = prepare_features_and_target(df)
    logger.info(f"Loaded {len(X)} samples with {X.shape[1]} features")
    
    validation_results = {}
    
    for model_type in model_types:
        logger.info(f"Performing {k}-fold CV for {model_type}")
        
        # Perform cross-validation
        cv_scores = perform_kfold_cross_validation(
            X, y, model_type=model_type, k=k
        )
        
        # Calculate metrics
        try:
            metrics = calculate_cv_metrics(cv_scores, model_type=model_type)
            validation_results[model_type] = metrics
        except ValueError as e:
            logger.error(f"Validation failed for {model_type}: {e}")
            validation_results[model_type] = {
                'error': str(e),
                'validation_status': {'passed': False, 'message': str(e)}
            }
    
    return validation_results

def main():
    """Main entry point for the validation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run model validation pipeline")
    parser.add_argument("--data", type=str, default="data/processed/games.parquet",
                      help="Path to processed data file")
    parser.add_argument("--results", type=str, default="data/results/model_metrics.json",
                      help="Path to model metrics file")
    parser.add_argument("--k", type=int, default=5, help="Number of CV folds")
    parser.add_argument("--models", type=str, nargs="+", 
                      default=["Ridge"], help="Model types to evaluate")
    
    args = parser.parse_args()
    
    try:
        results = run_validation_pipeline(
            data_path=args.data,
            results_path=args.results,
            k=args.k,
            model_types=args.models
        )
        
        # Save results
        output_path = Path("data/results/validation_metrics.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Validation results saved to {output_path}")
        
        # Check if any validation failed
        failed_models = [
            model for model, res in results.items()
            if isinstance(res, dict) and res.get('validation_status', {}).get('passed', False) == False
        ]
        
        if failed_models:
            logger.warning(f"Validation failed for models: {failed_models}")
            sys.exit(1)
        
        logger.info("All validations passed successfully.")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Validation pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
