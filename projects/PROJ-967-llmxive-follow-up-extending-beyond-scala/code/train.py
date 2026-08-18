"""
Training module for the llmXive entanglement analysis pipeline.

This module implements the predictive modeling logic for User Story 3 (US3).
It handles model selection based on sample size, training of Ridge Regression
or Random Forest models, cross-validation, and permutation testing.

Dependencies:
- scikit-learn (Ridge, RandomForestRegressor, cross_val_score, StratifiedKFold)
- pandas
- numpy
- pickle
"""

import argparse
import json
import logging
import os
import sys
import pickle
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.dummy import DummyRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from scipy.stats import pearsonr

# Import shared utilities from the project
# Note: These imports assume the code/ directory is in the PYTHONPATH
# or the script is run as a module from the project root.
from features import setup_logging

def setup_directories(base_path: Path) -> None:
    """Ensure required output directories exist."""
    (base_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (base_path / "results").mkdir(parents=True, exist_ok=True)

def load_features(file_path: Path) -> pd.DataFrame:
    """
    Load the feature dataset from JSON.
    
    Args:
        file_path: Path to the features.json file.
        
    Returns:
        DataFrame containing features and target.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Feature file not found: {file_path}")
        
    df = pd.read_json(file_path)
    
    # Validate required columns
    required_cols = ['sample_id', 'fidelity_loss', 'variance', 'entropy', 
                     'skewness', 'kurtosis', 'mahalanobis_distance']
                     
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in features: {missing_cols}")
        
    return df
    
def load_model_selection(file_path: Path) -> Dict[str, Any]:
    """Load the model selection configuration."""
    if not file_path.exists():
        raise FileNotFoundError(f"Model selection file not found: {file_path}")
        
    with open(file_path, 'r') as f:
        return json.load(f)

def prepare_data(df: pd.DataFrame, model_type: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare data for training, including stratified split.
    
    Args:
        df: DataFrame with features and target.
        model_type: Type of model selected ('ridge', 'rf', or 'fail').
        
    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    if model_type == 'fail':
        logging.warning("Model selection failed. Skipping data preparation.")
        return None, None, None, None
        
    # Define feature columns
    feature_cols = ['variance', 'entropy', 'skewness', 'kurtosis', 'mahalanobis_distance']
    X = df[feature_cols].values
    y = df['fidelity_loss'].values
    
    # Remove any rows with NaN in features or target
    mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    X = X[mask]
    y = y[mask]
    
    if len(X) < 10:
        logging.error("Insufficient data points after cleaning.")
        return None, None, None, None
        
    # Quantile-based binning for stratification
    # Create 5 bins based on the target variable
    bins = np.linspace(y.min(), y.max(), 6)
    # Handle edge case where all values are the same
    if len(np.unique(bins)) < 2:
        bins = np.unique(y)
        if len(bins) < 2:
            # If only one unique value, use equal frequency bins
            _, bin_indices = pd.qcut(y, q=5, retbins=True, duplicates='drop')
            if len(bin_indices) < 2:
                logging.warning("Cannot stratify with single target value. Using random split.")
                stratify = None
            else:
                stratify = pd.cut(y, bins=bin_indices, labels=False)
        else:
            stratify = pd.cut(y, bins=bins, labels=False)
    else:
        try:
            stratify = pd.cut(y, bins=bins, labels=False)
        except ValueError:
            # Fallback to random split if stratification fails
            logging.warning("Stratification failed. Using random split.")
            stratify = None
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=stratify
    )
    
    logging.info(f"Data split: Train={len(X_train)}, Test={len(X_test)}")
    
    return X_train, X_test, y_train, y_test

def train_model(X_train: np.ndarray, y_train: np.ndarray, model_type: str) -> object:
    """
    Train the selected model.
    
    Args:
        X_train: Training features.
        y_train: Training targets.
        model_type: 'ridge' or 'rf'.
        
    Returns:
        Trained model object.
    """
    if model_type == 'ridge':
        logging.info("Training Ridge Regression model.")
        model = Ridge(alpha=1.0, random_state=42)
    elif model_type == 'rf':
        logging.info("Training Random Forest model.")
        model = RandomForestRegressor(
            n_estimators=100, 
            random_state=42, 
            n_jobs=2,
            max_depth=None,
            min_samples_split=2,
            min_samples_leaf=1
        )
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
        
    model.fit(X_train, y_train)
    return model

def run_cross_validation(model: object, X: np.ndarray, y: np.ndarray, model_type: str) -> Dict[str, float]:
    """
    Run k-fold cross-validation.
    
    Args:
        model: Trained model.
        X: Features.
        y: Targets.
        model_type: 'ridge' or 'rf'.
        
    Returns:
        Dictionary with CV metrics.
    """
    n_splits = 5
    if len(y) < n_splits:
        logging.warning(f"Sample size ({len(y)}) too small for {n_splits}-fold CV.")
        return {"mean_r2": None, "std_r2": None, "mean_mae": None}
        
    # Use stratified k-fold if possible
    if model_type == 'rf':
        # For RF, we can use standard KFold or StratifiedKFold if we bin y
        try:
            bins = np.linspace(y.min(), y.max(), 6)
            stratify = pd.cut(y, bins=bins, labels=False)
            cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        except ValueError:
            cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    else:
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    try:
        r2_scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
        mae_scores = cross_val_score(model, X, y, cv=cv, scoring='neg_mean_absolute_error')
        mae_scores = -mae_scores  # Convert back to positive
        
        return {
            "mean_r2": float(np.mean(r2_scores)),
            "std_r2": float(np.std(r2_scores)),
            "mean_mae": float(np.mean(mae_scores)),
            "r2_scores": r2_scores.tolist(),
            "mae_scores": mae_scores.tolist()
        }
    except Exception as e:
        logging.error(f"Cross-validation failed: {e}")
        return {"mean_r2": None, "std_r2": None, "mean_mae": None}

def calculate_permutation_pvalue(model: object, X_train: np.ndarray, y_train: np.ndarray, 
                                 n_permutations: int = 1000, random_state: int = 42) -> float:
    """
    Calculate permutation test p-value.
    
    Args:
        model: Trained model.
        X_train: Training features.
        y_train: Training targets.
        n_permutations: Number of permutations.
        random_state: Random seed.
        
    Returns:
        p-value.
    """
    np.random.seed(random_state)
    
    # Calculate observed R2
    y_pred_obs = model.predict(X_train)
    r2_obs = r2_score(y_train, y_pred_obs)
    
    # Permutation distribution
    r2_perm = []
    for _ in range(n_permutations):
        y_perm = np.random.permutation(y_train)
        model_perm = type(model)(**model.get_params())
        model_perm.fit(X_train, y_perm)
        y_pred_perm = model_perm.predict(X_train)
        r2_perm.append(r2_score(y_perm, y_pred_perm))
    
    r2_perm = np.array(r2_perm)
    p_value = np.mean(r2_perm >= r2_obs)
    
    return float(p_value)

def evaluate_model(model: object, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    """
    Evaluate model on test set.
    
    Args:
        model: Trained model.
        X_test: Test features.
        y_test: Test targets.
        
    Returns:
        Dictionary with evaluation metrics.
    """
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    return {
        "r2": float(r2),
        "mae": float(mae),
        "residuals": (y_test - y_pred).tolist()
    }

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save results to JSON."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logging.info(f"Results saved to {output_path}")

def save_model(model: object, output_path: Path) -> None:
    """Save trained model to pickle."""
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)
    logging.info(f"Model saved to {output_path}")

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Train and evaluate entanglement prediction models.")
    parser.add_argument(
        "--features-path", 
        type=str, 
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed/features.json",
        help="Path to features.json"
    )
    parser.add_argument(
        "--model-selection-path",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed/model_selection.json",
        help="Path to model_selection.json"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results",
        help="Directory to save results"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results/model.pkl",
        help="Path to save the trained model"
    )
    parser.add_argument(
        "--results-path",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results/results.json",
        help="Path to save results JSON"
    )
    parser.add_argument(
        "--n-permutations",
        type=int,
        default=1000,
        help="Number of permutations for permutation test"
    )
    return parser.parse_args()

def main() -> int:
    """Main entry point for training pipeline."""
    args = parse_args()
    logger = setup_logging()
    
    base_path = Path(args.output_dir).parent
    setup_directories(base_path)
    
    # Load features
    try:
        df = load_features(Path(args.features_path))
        logger.info(f"Loaded {len(df)} samples from {args.features_path}")
    except Exception as e:
        logger.error(f"Failed to load features: {e}")
        return 1
        
    # Load model selection config
    try:
        model_config = load_model_selection(Path(args.model_selection_path))
        model_type = model_config.get("model_type", "fail")
        logger.info(f"Selected model type: {model_type}")
    except Exception as e:
        logger.error(f"Failed to load model selection: {e}")
        return 1
        
    # Handle failure case
    if model_type == 'fail':
        logger.warning("Model selection failed. Saving failure report.")
        results = {
            "status": "fail",
            "message": model_config.get("reason", "Critical Power Limitation: N < 30"),
            "model_type": "fail"
        }
        save_results(results, Path(args.results_path))
        # Save placeholder model
        with open(args.model_path, 'wb') as f:
            pickle.dump(results, f)
        return 0
        
    # Prepare data
    X_train, X_test, y_train, y_test = prepare_data(df, model_type)
    if X_train is None:
        logger.error("Data preparation failed.")
        return 1
        
    # Train model
    model = train_model(X_train, y_train, model_type)
    
    # Save model
    save_model(model, Path(args.model_path))
    
    # Cross-validation
    cv_results = run_cross_validation(model, X_train, y_train, model_type)
    logger.info(f"CV Results: R2={cv_results.get('mean_r2'):.4f}, MAE={cv_results.get('mean_mae'):.4f}")
    
    # Test evaluation
    test_results = evaluate_model(model, X_test, y_test)
    logger.info(f"Test Results: R2={test_results['r2']:.4f}, MAE={test_results['mae']:.4f}")
    
    # Permutation test
    p_value_perm = calculate_permutation_pvalue(
        model, X_train, y_train, 
        n_permutations=args.n_permutations
    )
    logger.info(f"Permutation test p-value: {p_value_perm:.4f}")
    
    # Calculate null baseline (Mean Predictor)
    dummy_model = DummyRegressor(strategy='mean')
    dummy_model.fit(X_train, y_train)
    y_pred_dummy = dummy_model.predict(X_test)
    baseline_r2 = r2_score(y_test, y_pred_dummy)
    baseline_mae = mean_absolute_error(y_test, y_pred_dummy)
    logger.info(f"Baseline (Mean): R2={baseline_r2:.4f}, MAE={baseline_mae:.4f}")
    
    # Compile final results
    results = {
        "model_type": model_type,
        "n_samples_total": len(df),
        "n_samples_train": len(X_train),
        "n_samples_test": len(X_test),
        "cv_metrics": cv_results,
        "test_metrics": {
            "r2": test_results["r2"],
            "mae": test_results["mae"]
        },
        "baseline_metrics": {
            "r2": baseline_r2,
            "mae": baseline_mae
        },
        "p_value_permutation": p_value_perm,
        "residuals": test_results["residuals"]
    }
    
    # Determine hypothesis status
    # Hypothesis is supported if RF R2 > 0 and significantly better than baseline
    if model_type == 'rf' and test_results["r2"] > 0:
        # Simple check: if model R2 > baseline R2 and p-value is low
        if test_results["r2"] > baseline_r2 and p_value_perm < 0.05:
            results["hypothesis_status"] = "supported"
        else:
            results["hypothesis_status"] = "unsupported"
    else:
        results["hypothesis_status"] = "unsupported"
        
    # Save results
    save_results(results, Path(args.results_path))
    
    # Save residuals to CSV
    residuals_path = Path(args.results_path).parent / "data" / "processed" / "residuals.csv"
    residuals_path.parent.mkdir(parents=True, exist_ok=True)
    residuals_df = pd.DataFrame({
        'sample_id': df.sample(len(X_test)).index.tolist(),  # Approximate mapping
        'y_true': y_test.tolist(),
        'y_pred': model.predict(X_test).tolist(),
        'residual': test_results['residuals']
    })
    residuals_df.to_csv(residuals_path, index=False)
    logger.info(f"Residuals saved to {residuals_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())