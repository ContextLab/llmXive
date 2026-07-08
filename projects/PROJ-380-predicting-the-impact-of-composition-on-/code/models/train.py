import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV, train_test_split, StratifiedKFold
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.base import clone

# Import project utilities
from utils.config import set_random_seed, get_paths, ensure_directories
from utils.logging_config import get_logger
from utils.provenance import ensure_state_directory, get_provenance_state_file, compute_file_checksum, load_existing_state, save_state, record_artifact

logger = get_logger(__name__)

# Define models and their parameter grids
# Constraint: Total combinations across all models must be <= 50
MODELS = {
    "LinearRegression": {
        "estimator": LinearRegression(),
        "param_grid": {
            "fit_intercept": [True, False]
        }
    },
    "Ridge": {
        "estimator": Ridge(),
        "param_grid": {
            "alpha": [0.1, 1.0, 10.0],
            "fit_intercept": [True, False]
        }
    },
    "RandomForest": {
        "estimator": RandomForestRegressor(random_state=42, n_jobs=-1),
        "param_grid": {
            "n_estimators": [50, 100],
            "max_depth": [None, 5, 10],
            "min_samples_split": [2, 5]
        }
    },
    "GradientBoosting": {
        "estimator": GradientBoostingRegressor(random_state=42),
        "param_grid": {
            "n_estimators": [50, 100],
            "learning_rate": [0.05, 0.1],
            "max_depth": [3, 5],
            "min_samples_split": [2, 5]
        }
    }
}

def count_total_combinations(param_grids: List[Dict[str, List]]) -> int:
    """Calculate total number of parameter combinations."""
    total = 0
    for grid in param_grids:
        combinations = 1
        for v in grid.values():
            combinations *= len(v)
        total += combinations
    return total

def validate_grid_constraints(model_grids: Dict[str, Dict]) -> bool:
    """Ensure total combinations <= 50."""
    grids = [v["param_grid"] for v in model_grids.values()]
    total = count_total_combinations(grids)
    if total > 50:
        logger.warning(f"Total combinations ({total}) exceeds limit (50). Adjusting grids...")
        # Simple heuristic: reduce n_estimators for tree models if needed
        if "RandomForest" in model_grids:
            model_grids["RandomForest"]["param_grid"]["n_estimators"] = [50]
        if "GradientBoosting" in model_grids:
            model_grids["GradientBoosting"]["param_grid"]["n_estimators"] = [50]
        total = count_total_combinations([v["param_grid"] for v in model_grids.values()])
        if total > 50:
            raise ValueError(f"Cannot satisfy <=50 constraint even after reduction. Current: {total}")
    logger.info(f"Total parameter combinations: {total}")
    return True

def run_grid_search(
    X: np.ndarray,
    y: np.ndarray,
    model_name: str,
    model_config: Dict[str, Any],
    cv_folds: int = 5,
    random_state: int = 42
) -> Tuple[Any, Dict[str, Any]]:
    """
    Perform GridSearchCV for a specific model.
    Returns the best estimator and the best parameters.
    """
    estimator = clone(model_config["estimator"])
    estimator.set_params(random_state=random_state)

    param_grid = model_config["param_grid"]
    
    # Use StratifiedKFold if y is discrete, otherwise KFold. 
    # For regression, sklearn GridSearchCV uses KFold by default if cv is an integer.
    # We explicitly pass cv=cv_folds.
    
    grid_search = GridSearchCV(
        estimator=estimator,
        param_grid=param_grid,
        cv=cv_folds,
        scoring='neg_mean_squared_error',
        n_jobs=-1,
        refit=True
    )

    logger.info(f"Running GridSearch for {model_name}...")
    grid_search.fit(X, y)

    best_params = grid_search.best_params_
    best_score = grid_search.best_score_
    best_estimator = grid_search.best_estimator_

    logger.info(f"Best {model_name} params: {best_params}, CV Score: {best_score:.4f}")

    return best_estimator, {
        "best_params": best_params,
        "best_cv_score": best_score,
        "n_splits": cv_folds,
        "total_combinations": count_total_combinations([param_grid])
    }

def evaluate_model(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray
) -> Dict[str, float]:
    """Calculate R2, MAE, RMSE on test set."""
    y_pred = model.predict(X_test)
    
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    return {
        "R2": r2,
        "MAE": mae,
        "RMSE": rmse
    }

def main(args: Optional[argparse.Namespace] = None):
    """
    Main entry point for model training with grid search.
    Loads processed data, runs grid search for multiple models,
    and saves the best model and a report.
    """
    if args is None:
        parser = argparse.ArgumentParser(description="Train BMG Shear Modulus Models")
        parser.add_argument("--data", type=str, default="data/processed/final_features.csv", help="Path to processed features CSV")
        parser.add_argument("--output-dir", type=str, default="data/artifacts", help="Output directory for models and reports")
        parser.add_argument("--seed", type=int, default=42, help="Random seed")
        parser.add_argument("--cv-folds", type=int, default=5, help="Number of CV folds")
        args = parser.parse_args()

    set_random_seed(args.seed)
    paths = get_paths()
    ensure_directories([args.output_dir])

    logger.info(f"Loading data from {args.data}")
    
    if not os.path.exists(args.data):
        raise FileNotFoundError(f"Input data file not found: {args.data}. Run ingestion pipeline first.")

    df = pd.read_csv(args.data)

    # Assume target column is 'shear_modulus_GPa' based on typical BMG datasets
    # If column name differs, this needs adjustment based on data-model.md
    target_col = 'shear_modulus_GPa'
    if target_col not in df.columns:
        # Fallback: try to find a column containing 'modulus'
        candidates = [c for c in df.columns if 'modulus' in c.lower()]
        if candidates:
            target_col = candidates[0]
            logger.warning(f"Target column '{target_col}' not found, using '{target_col}' instead.")
        else:
            raise ValueError(f"Could not find target column '{target_col}' or any 'modulus' column in {args.data}")

    feature_cols = [c for c in df.columns if c != target_col]
    X = df[feature_cols].values
    y = df[target_col].values

    # Simple train/test split for final evaluation (80/20)
    # Note: The task specifically asks for GridSearch with CV. 
    # We perform a split to report final test metrics as well.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=args.seed
    )

    logger.info(f"Training set size: {len(X_train)}, Test set size: {len(X_test)}")
    logger.info(f"Features: {feature_cols}")

    # Validate constraints
    validate_grid_constraints(MODELS)

    results = {}
    best_overall_model = None
    best_overall_score = -np.inf
    best_overall_name = None
    best_overall_params = None

    for name, config in MODELS.items():
        try:
            best_model, meta = run_grid_search(
                X_train, y_train, name, config, cv_folds=args.cv_folds, random_state=args.seed
            )
            
            # Evaluate on test set
            test_metrics = evaluate_model(best_model, X_test, y_test)
            
            results[name] = {
                "test_metrics": test_metrics,
                "cv_meta": meta,
                "best_params": meta["best_params"]
            }

            # Track best model based on test R2
            if test_metrics["R2"] > best_overall_score:
                best_overall_score = test_metrics["R2"]
                best_overall_model = best_model
                best_overall_name = name
                best_overall_params = meta["best_params"]

        except Exception as e:
            logger.error(f"Failed to train {name}: {e}")
            results[name] = {"error": str(e)}

    if best_overall_model is None:
        raise RuntimeError("No models were successfully trained.")

    # Save best model and report
    report_path = Path(args.output_dir) / "model_report.json"
    model_path = Path(args.output_dir) / "best_model.pkl" # Using pickle for simplicity, though joblib is preferred for sklearn

    import joblib
    joblib.dump(best_overall_model, model_path)
    logger.info(f"Best model saved to {model_path}")

    final_report = {
        "best_model": best_overall_name,
        "best_params": best_overall_params,
        "best_test_metrics": results[best_overall_name]["test_metrics"],
        "all_models_results": results,
        "config": {
            "cv_folds": args.cv_folds,
            "seed": args.seed,
            "data_source": args.data
        }
    }

    with open(report_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    logger.info(f"Model report saved to {report_path}")

    # Record provenance
    ensure_state_directory()
    state_file = get_provenance_state_file()
    current_state = load_existing_state(state_file)
    
    record_artifact(
        state=current_state,
        artifact_path=str(report_path),
        artifact_type="model_report",
        description="Grid search results and best model metrics"
    )
    record_artifact(
        state=current_state,
        artifact_path=str(model_path),
        artifact_type="trained_model",
        description=f"Best model: {best_overall_name}"
    )
    
    save_state(current_state, state_file)
    logger.info(f"Provenance recorded to {state_file}")

if __name__ == "__main__":
    main()