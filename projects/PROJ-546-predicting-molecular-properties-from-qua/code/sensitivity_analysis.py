"""
Sensitivity Analysis for Molecular Property Prediction.

This module implements User Story 3 (FR-006, FR-009, FR-007, SC-003).
It extracts feature importance from the trained semi-empirical Random Forest model,
identifies top descriptors, and performs a sensitivity sweep over feature subsets.

Inputs:
    - data/model_semi.pkl: Trained Random Forest model (from train_models.py)
    - data/descriptors_semi.csv: Descriptor dataset with feature names in header
    - data/evaluation_results_semi.json: Cross-validation MAE results (optional, for baseline)

Outputs:
    - data/feature_importance_semi.json: Feature names and importance scores
    - data/sensitivity_sweep_results.json: MAE degradation for various feature subsets
    - data/reports/sensitivity_summary.md: Human-readable summary of findings
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_model(model_path: str) -> Any:
    """Load the trained Random Forest model."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    logger.info(f"Loading model from {model_path}")
    return joblib.load(model_path)

def load_data(csv_path: str) -> pd.DataFrame:
    """Load the descriptor dataset."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Data file not found: {csv_path}")
    logger.info(f"Loading data from {csv_path}")
    return pd.read_csv(csv_path)

def extract_feature_importance(
    model: Any, 
    feature_names: List[str]
) -> List[Dict[str, Any]]:
    """
    Extract feature importance from the Random Forest model.
    
    Args:
        model: Trained Random Forest model.
        feature_names: List of feature names corresponding to model columns.
        
    Returns:
        List of dicts with 'feature', 'importance', 'rank'.
    """
    if not hasattr(model, 'feature_importances_'):
        raise AttributeError("Model does not have feature_importances_ attribute.")
    
    importances = model.feature_importances_
    
    # Create list of (feature, importance)
    feature_importance_list = [
        {"feature": name, "importance": float(imp)}
        for name, imp in zip(feature_names, importances)
    ]
    
    # Sort by importance descending
    feature_importance_list.sort(key=lambda x: x["importance"], reverse=True)
    
    # Add rank
    for rank, item in enumerate(feature_importance_list, 1):
        item["rank"] = rank
        
    return feature_importance_list

def identify_top_descriptors(
    feature_importance: List[Dict[str, Any]], 
    n_top: int = 5
) -> List[Dict[str, Any]]:
    """Identify top N descriptors and calculate cumulative importance."""
    top_n = feature_importance[:n_top]
    
    cumulative_sum = 0.0
    for item in top_n:
        cumulative_sum += item["importance"]
        item["cumulative_importance"] = round(cumulative_sum, 6)
        
    return top_n

def prepare_features_target(
    df: pd.DataFrame, 
    target_col: str = "experimental_barrier"
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Prepare features and target from dataframe."""
    feature_cols = [col for col in df.columns if col != target_col]
    X = df[feature_cols].values
    y = df[target_col].values
    return X, y, feature_cols

def run_sensitivity_sweep(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    feature_importance: List[Dict[str, Any]],
    percentiles: List[int] = [20, 40, 60, 80, 100],
    n_splits: int = 5
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by training models on subsets of features
    defined by importance percentiles.
    
    Args:
        model: The Random Forest model structure (used for cloning/hyperparams).
        X: Feature matrix.
        y: Target vector.
        feature_names: List of all feature names.
        feature_importance: Full list of feature importance dicts.
        percentiles: List of percentiles to sweep (e.g., top 20%, 40%, ...).
        n_splits: Number of CV folds.
        
    Returns:
        Dictionary with sweep results.
    """
    # We need to retrain models on subsets to get accurate MAE degradation
    # Since we don't want to import sklearn.model_selection here to avoid 
    # tight coupling, we'll simulate the evaluation by using the existing
    # trained model's logic but with masked features.
    # However, for a true sensitivity analysis, we must retrain.
    # We will assume the model passed is an instance of RandomForestRegressor
    # and we can clone it.
    
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import cross_val_score
    
    # Get original model params if possible, else defaults
    try:
        params = model.get_params()
    except AttributeError:
        params = {'n_estimators': 100, 'random_state': 42}
    
    results = []
    sorted_features = [item["feature"] for item in feature_importance]
    feature_to_idx = {name: i for i, name in enumerate(sorted_features)}
    
    logger.info(f"Running sensitivity sweep on {len(percentiles)} percentiles...")
    
    for pct in percentiles:
        # Select top features for this percentile
        n_features = max(1, int(len(sorted_features) * (pct / 100.0)))
        selected_features = sorted_features[:n_features]
        selected_indices = [feature_to_idx[f] for f in selected_features]
        
        # Subset X
        X_subset = X[:, selected_indices]
        
        # Create a new model with same params
        new_model = RandomForestRegressor(**params)
        
        # Cross-validate
        try:
            scores = cross_val_score(
                new_model, X_subset, y, 
                cv=n_splits, 
                scoring='neg_mean_absolute_error',
                n_jobs=-1
            )
            mae_scores = -scores
            mean_mae = float(np.mean(mae_scores))
            std_mae = float(np.std(mae_scores))
            status = "success"
        except Exception as e:
            logger.warning(f"Error in CV for {pct}%: {e}")
            mean_mae = None
            std_mae = None
            status = "failed"
        
        results.append({
            "percentile": pct,
            "n_features": n_features,
            "mean_mae": mean_mae,
            "std_mae": std_mae,
            "status": status,
            "features_used": selected_features
        })
        
        logger.info(f"  {pct}%: {n_features} features, MAE={mean_mae:.4f} ({status})")
        
    return {
        "percentiles": percentiles,
        "sweep_results": results
    }

def generate_summary_report(
    top_descriptors: List[Dict[str, Any]],
    sweep_results: Dict[str, Any],
    output_path: str
) -> None:
    """Generate a markdown summary report."""
    report_lines = [
        "# Sensitivity Analysis Report",
        "",
        "## Feature Importance",
        "",
        "Top 5 Descriptors:",
        ""
    ]
    
    for i, desc in enumerate(top_descriptors, 1):
        report_lines.append(
            f"{i}. **{desc['feature']}**: Importance = {desc['importance']:.4f} "
            f"(Cumulative: {desc['cumulative_importance']:.4f})"
        )
        
    report_lines.extend([
        "",
        "## Sensitivity Sweep Results",
        "",
        "MAE degradation when using subsets of features:",
        "",
        "| Percentile | Features | Mean MAE | Std MAE | Status |",
        "|------------|----------|----------|---------|--------|"
    ])
    
    for res in sweep_results["sweep_results"]:
        if res["mean_mae"] is not None:
            mae_str = f"{res['mean_mae']:.4f}"
        else:
            mae_str = "N/A"
            
        report_lines.append(
            f"| {res['percentile']}% | {res['n_features']} | {mae_str} | "
            f"{res['std_mae']:.4f if res['std_mae'] else 'N/A'} | {res['status']} |"
        )
        
    report_lines.extend([
        "",
        "## Conclusion",
        "",
        "This analysis identifies the most influential descriptors for predicting "
        "molecular barrier heights and evaluates the model's robustness to feature reduction."
    ])
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
        
    logger.info(f"Summary report written to {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Perform sensitivity analysis on semi-empirical RF model."
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default="data/model_semi.pkl",
        help="Path to the trained semi-empirical RF model."
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/descriptors_semi.csv",
        help="Path to the descriptor CSV file."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Directory for output files."
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Number of top descriptors to identify."
    )
    parser.add_argument(
        "--percentiles",
        type=str,
        default="20,40,60,80,100",
        help="Comma-separated list of percentiles for sensitivity sweep."
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    report_dir = os.path.join(args.output_dir, "reports")
    os.makedirs(report_dir, exist_ok=True)
    
    try:
        # Load data and model
        model = load_model(args.model_path)
        df = load_data(args.data_path)
        
        # Prepare features
        X, y, feature_names = prepare_features_target(df)
        
        # Extract importance
        logger.info("Extracting feature importance...")
        feature_importance = extract_feature_importance(model, feature_names)
        
        # Save full importance
        importance_path = os.path.join(args.output_dir, "feature_importance_semi.json")
        with open(importance_path, 'w') as f:
            json.dump(feature_importance, f, indent=2)
        logger.info(f"Feature importance saved to {importance_path}")
        
        # Identify top descriptors
        logger.info(f"Identifying top {args.top_n} descriptors...")
        top_descriptors = identify_top_descriptors(feature_importance, args.top_n)
        
        # Parse percentiles
        percentiles = [int(x.strip()) for x in args.percentiles.split(',')]
        
        # Run sensitivity sweep
        logger.info("Running sensitivity sweep...")
        sweep_results = run_sensitivity_sweep(
            model, X, y, feature_names, feature_importance, percentiles
        )
        
        # Save sweep results
        sweep_path = os.path.join(args.output_dir, "sensitivity_sweep_results.json")
        with open(sweep_path, 'w') as f:
            json.dump(sweep_results, f, indent=2)
        logger.info(f"Sweep results saved to {sweep_path}")
        
        # Generate report
        report_path = os.path.join(report_dir, "sensitivity_summary.md")
        generate_summary_report(top_descriptors, sweep_results, report_path)
        
        logger.info("Sensitivity analysis completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
