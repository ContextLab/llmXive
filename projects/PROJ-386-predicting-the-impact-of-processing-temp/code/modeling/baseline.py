import os
import sys
import json
import logging
import argparse
import warnings
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import StratifiedGroupKFold, cross_validate
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Import project config
from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_and_prepare_data(data_path: str) -> pd.DataFrame:
    """
    Load preprocessed data and ensure required columns exist.
    Expects 'Alloy Series' for grouping and residuals as target.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Preprocessed data not found at {data_path}")
    
    df = pd.read_csv(data_path)
    
    required_cols = ['Alloy Series', 'residual_grain_size']
    feature_cols = [c for c in df.columns if c not in required_cols + ['index']]
    
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for baseline modeling: {missing}")
    
    logger.info(f"Loaded data with {len(df)} rows. Features: {len(feature_cols)}")
    return df

def stratified_group_kfold_cv(
    df: pd.DataFrame,
    feature_cols: list,
    target_col: str,
    group_col: str = 'Alloy Series',
    n_splits: int = 5,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Perform StratifiedGroupKFold cross-validation.
    
    This implements Constitution Principle VII by ensuring that all samples 
    belonging to the same 'Alloy Series' (study/source) are kept together 
    in either the training or test set, preventing data leakage.
    
    Args:
        df: Preprocessed DataFrame
        feature_cols: List of feature column names
        target_col: Target column name
        group_col: Column name for grouping variable (Alloy Series)
        n_splits: Number of CV folds
        random_state: Random seed for reproducability
        
    Returns:
        Dictionary with CV results (scores, fold details)
    """
    X = df[feature_cols].values
    y = df[target_col].values
    groups = df[group_col].values
    
    # Initialize StratifiedGroupKFold
    # Note: StratifiedGroupKFold attempts to maintain class balance across groups
    # if the target is discretized, but primarily ensures groups are not split.
    sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    
    # Prepare arrays for cross_validate
    # We use a dummy pipeline to pass data through, but manually compute metrics 
    # to ensure we are evaluating the correct model on the correct splits.
    
    r2_scores = []
    mae_scores = []
    fold_info = []
    
    logger.info(f"Starting {n_splits}-fold StratifiedGroupKFold cross-validation...")
    
    for fold_idx, (train_idx, test_idx) in enumerate(sgkf.split(X, y, groups)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Fit model
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # Predict and Score
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        
        r2_scores.append(r2)
        mae_scores.append(mae)
        
        fold_info.append({
            "fold": fold_idx + 1,
            "train_size": len(train_idx),
            "test_size": len(test_idx),
            "r2": float(r2),
            "mae": float(mae)
        })
        
        logger.info(f"Fold {fold_idx + 1}: R²={r2:.4f}, MAE={mae:.4f}")
    
    return {
        "r2_scores": r2_scores,
        "mae_scores": mae_scores,
        "mean_r2": float(np.mean(r2_scores)),
        "std_r2": float(np.std(r2_scores)),
        "mean_mae": float(np.mean(mae_scores)),
        "std_mae": float(np.std(mae_scores)),
        "fold_details": fold_info,
        "n_splits": n_splits,
        "group_col": group_col
    }

def train_baseline_model(
    df: pd.DataFrame,
    feature_cols: list,
    target_col: str
) -> Tuple[LinearRegression, Dict[str, Any]]:
    """
    Train a final baseline Linear Regression model on the full dataset
    and perform cross-validation to assess generalization.
    
    Returns:
        Tuple of (trained_model, cv_results)
    """
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Train on full data for final coefficients
    model = LinearRegression()
    model.fit(X, y)
    
    # Perform Stratified Group K-Fold CV
    cv_results = stratified_group_kfold_cv(
        df, feature_cols, target_col, 
        group_col='Alloy Series'
    )
    
    return model, cv_results

def extract_coefficients_and_report(
    model: LinearRegression,
    feature_cols: list,
    cv_results: Dict[str, Any],
    collinearity_report_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract model coefficients and generate a detailed report.
    Checks collinearity report to flag potentially spurious coefficients.
    """
    coefficients = dict(zip(feature_cols, model.coef_.tolist()))
    intercept = float(model.intercept_)
    
    report = {
        "intercept": intercept,
        "coefficients": coefficients,
        "cv_metrics": {
            "mean_r2": cv_results["mean_r2"],
            "std_r2": cv_results["std_r2"],
            "mean_mae": cv_results["mean_mae"],
            "std_mae": cv_results["std_mae"]
        },
        "fold_details": cv_results["fold_details"],
        "model_type": "LinearRegression",
        "validation_method": "StratifiedGroupKFold",
        "groups_preserved": "Alloy Series"
    }
    
    # Check collinearity report if available
    if collinearity_report_path and os.path.exists(collinearity_report_path):
        try:
            with open(collinearity_report_path, 'r') as f:
                collinearity_data = json.load(f)
            
            flagged_pairs = collinearity_data.get('flagged_pairs', [])
            
            # Flatten pairs for easier checking
            flagged_features = set()
            for pair in flagged_pairs:
                if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                    flagged_features.add(pair[0])
                    flagged_features.add(pair[1])
            
            flagged_coeffs = {k: v for k, v in coefficients.items() if k in flagged_features}
            
            if flagged_coeffs:
                report["collinearity_warning"] = True
                report["flagged_features"] = list(flagged_features)
                report["interpretation_note"] = (
                    "Some features show high collinearity (r > 0.8). "
                    "Coefficients for these features should be interpreted as joint effects "
                    "rather than independent contributions."
                )
            else:
                report["collinearity_warning"] = False
                report["interpretation_note"] = "No significant collinearity detected among features."
                
        except Exception as e:
            logger.warning(f"Could not load collinearity report: {e}")
            report["collinearity_warning"] = None
            report["interpretation_note"] = "Collinearity check skipped due to error."
    else:
        report["interpretation_note"] = "No collinearity report found. Interpret with caution."
        
    return report

def save_model_artifacts(
    model_report: Dict[str, Any],
    output_path: str
):
    """Save model report to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(model_report, f, indent=2)
    logger.info(f"Model artifacts saved to {output_path}")

def run_baseline_pipeline(
    input_data_path: str,
    output_report_path: str,
    collinearity_report_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the full baseline modeling pipeline:
    1. Load data
    2. Identify features and target
    3. Train model with StratifiedGroupKFold CV
    4. Extract coefficients and report
    5. Save artifacts
    """
    logger.info("Starting Baseline Modeling Pipeline")
    
    # 1. Load Data
    df = load_and_prepare_data(input_data_path)
    
    # Identify columns
    required_cols = ['Alloy Series', 'residual_grain_size']
    feature_cols = [c for c in df.columns if c not in required_cols + ['index']]
    target_col = 'residual_grain_size'
    
    if not feature_cols:
        raise ValueError("No feature columns found in preprocessed data.")
    
    logger.info(f"Features to model: {feature_cols}")
    
    # 2. Train Model & CV
    model, cv_results = train_baseline_model(df, feature_cols, target_col)
    
    # 3. Extract Report
    model_report = extract_coefficients_and_report(
        model, feature_cols, cv_results, collinearity_report_path
    )
    
    # 4. Save Artifacts
    save_model_artifacts(model_report, output_report_path)
    
    logger.info("Baseline Modeling Pipeline Completed")
    return model_report

def main():
    parser = argparse.ArgumentParser(description="Baseline Modeling Pipeline")
    parser.add_argument(
        "--input-data", 
        type=str, 
        required=True,
        help="Path to preprocessed CSV data"
    )
    parser.add_argument(
        "--output-report",
        type=str,
        default="data/artifacts/baseline_model_report.json",
        help="Path to output JSON report"
    )
    parser.add_argument(
        "--collinearity-report",
        type=str,
        default=None,
        help="Path to collinearity report JSON (optional)"
    )
    
    args = parser.parse_args()
    
    # Determine collinearity path
    coll_path = args.collinearity_report
    if coll_path is None:
        # Default location if not specified
        coll_path = "data/artifacts/collinearity_report.json"
        if not os.path.exists(coll_path):
            coll_path = None
    
    try:
        result = run_baseline_pipeline(
            args.input_data,
            args.output_report,
            coll_path
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()