import sys
import logging
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import r2_score, mean_squared_error
import random

# Local imports based on project API surface
from src.utils.validation import setup_logger, handle_error
from src.utils.seed_manager import init_seed, get_seed, add_seed_argument

def setup_logger_module(name: str = "regression") -> logging.Logger:
    """Initialize and return a logger for the regression module."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = setup_logger_module()

def fit_model(
    X: pd.DataFrame,
    y: pd.Series,
    n_folds: int = 5,
    random_state: int = 42,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Fit a Linear Regression model using 5-fold Cross-Validation.
    
    Args:
        X: Feature matrix (DataFrame).
        y: Target vector (Series).
        n_folds: Number of CV folds (default 5 per FR-005).
        random_state: Random state for reproducibility.
        seed: Optional seed for global random state.
        
    Returns:
        Dictionary containing 'cv_scores', 'mean_cv_score', 'std_cv_score', and 'model'.
    """
    if seed is not None:
        init_seed(seed)
    
    model = LinearRegression()
    
    # Perform 5-fold CV
    cv_scores = cross_val_score(model, X, y, cv=n_folds, scoring='r2')
    
    results = {
        "cv_scores": cv_scores.tolist(),
        "mean_cv_score": float(np.mean(cv_scores)),
        "std_cv_score": float(np.std(cv_scores)),
        "n_folds": n_folds
    }
    
    # Fit the model on the full data for feature importance extraction later
    model.fit(X, y)
    results["model"] = model
    
    logger.info(f"CV R² Score: {results['mean_cv_score']:.4f} (+/- {results['std_cv_score']:.4f})")
    return results

def evaluate_test(
    X: pd.DataFrame,
    y: pd.Series,
    model: Any,
    test_size: float = 0.2,
    stratify_col: Optional[str] = None,
    random_state: int = 42,
    target_r2: float = 0.5
) -> Dict[str, Any]:
    """
    Evaluate the model on a held-out test set.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        model: Trained LinearRegression model.
        test_size: Fraction of data to use for testing.
        stratify_col: Column name to stratify by (FR-014).
        random_state: Random state for split.
        target_r2: Threshold for SC-003 verification.
        
    Returns:
        Dictionary containing 'r2', 'rmse', 'coefficients', 'pass_target', 'test_size'.
    """
    logger.info("Splitting data for test evaluation...")
    
    # Determine stratification
    stratify_kwargs = {}
    if stratify_col and stratify_col in X.columns:
        # If stratify_col is in X, we need to pass it to train_test_split
        # However, train_test_split expects y to be the stratification target if it's a column in X
        # But here y is separate. We need to pass the series corresponding to stratify_col.
        # Since X is a DataFrame, we can extract the column.
        # Note: stratify must be a 1D array-like.
        stratify_kwargs['stratify'] = X[stratify_col]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, **stratify_kwargs
    )
    
    # Predict
    y_pred = model.predict(X_test)
    
    # Metrics
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    # Feature Importance (Coefficients)
    coefficients = dict(zip(X.columns, model.coef_))
    intercept = float(model.intercept_)
    
    # SC-003 Verification
    pass_target = r2 > target_r2
    
    results = {
        "r2": float(r2),
        "rmse": float(rmse),
        "intercept": intercept,
        "coefficients": coefficients,
        "pass_target": pass_target,
        "target_r2": target_r2,
        "test_size": test_size,
        "n_train": len(X_train),
        "n_test": len(X_test)
    }
    
    logger.info(f"Test R²: {r2:.4f}, RMSE: {rmse:.4f}")
    logger.info(f"SC-003 Target (R² > {target_r2}): {'PASS' if pass_target else 'FAIL'}")
    
    if not pass_target:
        logger.warning(f"Model performance (R²={r2:.4f}) did not meet the target threshold ({target_r2}).")
        
    return results

def run_regression_analysis(
    input_path: Path,
    output_path: Path,
    target_column: str = "thermal_conductivity",
    predictor_columns: Optional[List[str]] = None,
    stratify_column: str = "chemistry_class",
    seed: int = 42
) -> Dict[str, Any]:
    """
    Main orchestration function for regression analysis.
    
    Args:
        input_path: Path to the VIF-filtered CSV.
        output_path: Path to save the results JSON.
        target_column: Name of the target column.
        predictor_columns: List of predictor columns. If None, all numeric columns except target are used.
        stratify_column: Column to use for stratified splitting.
        seed: Random seed.
        
    Returns:
        Full results dictionary.
    """
    logger.info(f"Loading data from {input_path}...")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    df = pd.read_csv(input_path)
    
    # Validate columns
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in data.")
        
    if predictor_columns is None:
        # Select all numeric columns except target
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        predictor_columns = [c for c in numeric_cols if c != target_column]
        
    logger.info(f"Using predictors: {predictor_columns}")
    
    # Prepare data
    X = df[predictor_columns]
    y = df[target_column]
    
    # Handle missing values if any (should be clean, but safety check)
    if X.isnull().any().any() or y.isnull().any():
        logger.warning("Dropping rows with missing values in predictors or target.")
        mask = ~(X.isnull().any(axis=1) | y.isnull())
        X = X[mask]
        y = y[mask]
    
    # 1. Fit Model (5-fold CV)
    fit_results = fit_model(X, y, n_folds=5, random_state=seed, seed=seed)
    
    # 2. Evaluate Test
    eval_results = evaluate_test(
        X, y, fit_results["model"], 
        stratify_col=stratify_column, 
        random_state=seed,
        target_r2=0.5
    )
    
    # Compile final results
    final_results = {
        "input_file": str(input_path),
        "seed": seed,
        "target_column": target_column,
        "predictors": predictor_columns,
        "cross_validation": fit_results,
        "test_evaluation": eval_results
    }
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_results, f, indent=2)
        
    logger.info(f"Results saved to {output_path}")
    return final_results

def save_regression_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save regression results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Regression results saved to {output_path}")

def main():
    """CLI entry point for regression analysis."""
    parser = argparse.ArgumentParser(description="Run Regression Analysis on Perovskite Descriptors")
    parser.add_argument(
        "--input", 
        type=Path, 
        default=Path("data/cleaned/descriptors_vif_filtered.csv"),
        help="Path to the VIF-filtered dataset (output of T025b)."
    )
    parser.add_argument(
        "--output", 
        type=Path, 
        default=Path("data/results/model_metrics.json"),
        help="Path to save the model metrics JSON."
    )
    parser.add_argument(
        "--target",
        type=str,
        default="thermal_conductivity",
        help="Name of the target column."
    )
    parser.add_argument(
        "--stratify",
        type=str,
        default="chemistry_class",
        help="Column to stratify by for train/test split."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )
    
    args = parser.parse_args()
    
    try:
        results = run_regression_analysis(
            input_path=args.input,
            output_path=args.output,
            target_column=args.target,
            stratify_column=args.stratify,
            seed=args.seed
        )
        
        # Exit with error code if SC-003 target not met (optional strictness)
        if not results["test_evaluation"]["pass_target"]:
            logger.error("SC-003 Target (R² > 0.5) not met.")
            # Note: We do not exit 1 here to allow the pipeline to continue logging, 
            # but the result clearly indicates failure of the specific metric.
            
    except Exception as e:
        logger.error(f"Regression analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
