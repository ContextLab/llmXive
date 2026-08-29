"""
Regression modeling for perovskite thermal conductivity prediction.

This module fits a multiple linear regression model with K-fold cross-validation,
evaluates performance on a held-out test set, and reports R² and RMSE.

Usage:
    python src/analysis/regression.py --input data/results/descriptors.csv --output data/results/model_metrics.json --seed 42
"""
import sys
import logging
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.preprocessing import StandardScaler

# Import seed management
from src.utils.seed_manager import init_seed, add_seed_argument, get_seed, is_seed_initialized
from src.utils.validation import setup_logger, handle_error


def fit_model(X: np.ndarray, y: np.ndarray, cv: int = 5, random_state: int = 42) -> Tuple[LinearRegression, Dict[str, float]]:
    """
    Fit a linear regression model with cross-validation.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        cv: Number of cross-validation folds.
        random_state: Random state for reproducibility.
    
    Returns:
        Tuple of (fitted model, cross-validation metrics).
    """
    logger = setup_logger(__name__)
    
    # Initialize seed
    if not is_seed_initialized():
        init_seed(random_state)
    
    model = LinearRegression()
    
    # Perform cross-validation
    cv_scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
    
    cv_metrics = {
        "mean_r2": float(np.mean(cv_scores)),
        "std_r2": float(np.std(cv_scores)),
        "cv_scores": [float(score) for score in cv_scores]
    }
    
    logger.info(f"Cross-validation R²: {cv_metrics['mean_r2']:.4f} (+/- {cv_metrics['std_r2']:.4f})")
    
    # Fit on full data for feature importance
    model.fit(X, y)
    
    return model, cv_metrics


def evaluate_test(model: LinearRegression, X_test: np.ndarray, y_test: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
    """
    Evaluate the model on a held-out test set.
    
    Args:
        model: Fitted regression model.
        X_test: Test feature matrix.
        y_test: Test target vector.
        feature_names: List of feature names.
    
    Returns:
        Dictionary of evaluation metrics and feature importance.
    """
    y_pred = model.predict(X_test)
    
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    # Feature importance (absolute coefficients)
    feature_importance = {
        name: float(abs(coef)) 
        for name, coef in zip(feature_names, model.coef_)
    }
    
    metrics = {
        "r2": float(r2),
        "rmse": float(rmse),
        "n_test_samples": len(y_test),
        "feature_importance": feature_importance
    }
    
    return metrics


def run_regression_analysis(df: pd.DataFrame, predictors: List[str], target: str = "thermal_conductivity", stratify_col: str = "chemistry_class", test_size: float = 0.2, cv: int = 5, random_state: int = 42) -> Dict[str, Any]:
    """
    Run full regression analysis pipeline.
    
    Args:
        df: Input dataframe.
        predictors: List of predictor column names.
        target: Target column name.
        stratify_col: Column to stratify the split by.
        test_size: Proportion of data for test set.
        cv: Number of cross-validation folds.
        random_state: Random state for reproducibility.
    
    Returns:
        Dictionary containing all analysis results.
    """
    logger = setup_logger(__name__)
    
    # Initialize seed
    if not is_seed_initialized():
        init_seed(random_state)
    
    # Prepare data
    X = df[predictors].values
    y = df[target].values
    stratify = df[stratify_col].values if stratify_col in df.columns else None
    
    # Handle missing values
    valid_mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    X = X[valid_mask]
    y = y[valid_mask]
    if stratify is not None:
        stratify = stratify[valid_mask]
    
    logger.info(f"Data shape after cleaning: {X.shape}")
    
    if len(X) < 10:
        raise ValueError("Insufficient samples for regression analysis")
    
    # Split data
    if stratify is not None:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=stratify
        )
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Fit model
    model, cv_metrics = fit_model(X_train_scaled, y_train, cv=cv, random_state=random_state)
    
    # Evaluate on test set
    test_metrics = evaluate_test(model, X_test_scaled, y_test, predictors)
    
    # Check R² > 0.5 target
    r2_pass = test_metrics["r2"] > 0.5
    test_metrics["r2_target_met"] = r2_pass
    
    results = {
        "cross_validation": cv_metrics,
        "test_set": test_metrics,
        "n_train": len(y_train),
        "n_test": len(y_test),
        "random_state": random_state,
        "r2_target": 0.5,
        "r2_target_met": r2_pass
    }
    
    return results


def save_regression_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save regression results to a JSON file.
    
    Args:
        results: The regression results dictionary.
        output_path: Path to save the results.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Regression analysis for perovskite thermal conductivity")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file path")
    parser.add_argument("--output", type=str, default="data/results/model_metrics.json", help="Output JSON file path")
    parser.add_argument("--predictors", type=str, nargs="+", default=["tolerance_factor", "unit_cell_volume", "bond_length_variance", "avg_tilting_angle"], help="Predictor column names")
    parser.add_argument("--target", type=str, default="thermal_conductivity", help="Target column name")
    parser.add_argument("--stratify-by", type=str, default="chemistry_class", help="Column to stratify by")
    parser.add_argument("--test-size", type=float, default=0.2, help="Proportion of data for test set")
    parser.add_argument("--cv", type=int, default=5, help="Number of cross-validation folds")
    parser = add_seed_argument(parser)
    
    args = parser.parse_args()
    
    # Initialize seed
    init_seed(args.seed)
    
    try:
        input_path = Path(args.input)
        output_path = Path(args.output)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        logger = setup_logger(__name__)
        logger.info(f"Loading data from {input_path}")
        
        df = pd.read_csv(input_path)
        
        logger.info("Running regression analysis...")
        
        results = run_regression_analysis(
            df, args.predictors, args.target, 
            args.stratify_by, args.test_size, args.cv, args.seed
        )
        
        save_regression_results(results, output_path)
        logger.info(f"Saved regression results to {output_path}")
        
        # Print summary
        logger.info(f"Test R²: {results['test_set']['r2']:.4f}")
        logger.info(f"R² > 0.5 target met: {results['r2_target_met']}")
        
    except Exception as e:
        handle_error(f"Error in regression analysis: {e}", level="CRITICAL")
        sys.exit(1)


if __name__ == "__main__":
    main()