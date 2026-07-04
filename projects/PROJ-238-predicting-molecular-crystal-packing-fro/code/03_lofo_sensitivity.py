"""
Leave-One-Feature-Out (LOFO) Sensitivity Analysis for Crystal Packing Prediction.

This script performs a rigorous LOFO analysis on the trained Random Forest model
to determine the sensitivity of the model's R² score to the removal of individual
features. It documents the R² variation in a markdown report.

Requirements:
- Trained Random Forest model saved in 'state/projects/PROJ-238.../models/random_forest.pkl'
- Test data available in 'data/processed/test.csv'
- Scikit-learn, pandas, numpy, and config modules available.
"""
import os
import sys
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split

# Add project root to path to resolve imports if run as script
# Note: The agent assumes the script is run from the project root or code/ directory
# based on standard project structure.
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config, setup_logging
from utils.metrics import paired_t_test

def load_test_data(config: Any) -> pd.DataFrame:
    """Load the test dataset."""
    test_path = Path(config.DATA_PATH) / "processed" / "test.csv"
    if not test_path.exists():
        raise FileNotFoundError(f"Test data not found at {test_path}. Run T017 first.")
    return pd.read_csv(test_path)

def load_model(config: Any) -> RandomForestRegressor:
    """Load the trained Random Forest model."""
    # Determine project ID from config or default
    project_id = "PROJ-238-predicting-molecular-crystal-packing-fro"
    model_path = Path("state") / "projects" / project_id / "models" / "random_forest.pkl"
    
    if not model_path.exists():
        # Fallback to a relative path if the project ID structure varies
        model_path = Path(config.DATA_PATH).parent / "state" / "projects" / project_id / "models" / "random_forest.pkl"
    
    if not model_path.exists():
        # Try absolute path from current working directory assumption
        model_path = Path.cwd() / "state" / "projects" / project_id / "models" / "random_forest.pkl"

    if not model_path.exists():
        raise FileNotFoundError(f"Random Forest model not found at {model_path}. Run T022/T023 first.")

    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model

def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """Identify feature columns (exclude ID and target)."""
    target_col = 'packing_coefficient'
    exclude_cols = ['ID', target_col]
    # Also exclude any auxiliary flags like 'dipole_imputed' if present in features
    # but we want to test the core descriptors.
    # Based on T012, features are: Volume, SurfaceArea, Dipole, HBD, HBA, PSA
    core_features = ['Volume', 'SurfaceArea', 'Dipole', 'HBD', 'HBA', 'PSA']
    
    available_cols = [c for c in df.columns if c not in exclude_cols]
    # Filter to only core features if they exist, otherwise use all available
    features = [c for c in core_features if c in available_cols]
    if not features:
        features = available_cols
    return features

def run_lofo_analysis(
    model: RandomForestRegressor,
    X: pd.DataFrame,
    y: pd.Series,
    feature_names: List[str]
) -> Dict[str, float]:
    """
    Perform LOFO analysis.
    
    Returns a dictionary mapping feature name to the R² score of the model
    trained on all features EXCEPT that one.
    """
    results = {}
    base_r2 = r2_score(y, model.predict(X))
    logging.info(f"Base R² (all features): {base_r2:.4f}")

    for feature in feature_names:
        # Create feature subset excluding current feature
        subset_features = [f for f in feature_names if f != feature]
        X_subset = X[subset_features]
        
        # Train a new model on this subset to ensure fair comparison
        # (The original model might rely on interactions involving the removed feature)
        # However, standard LOFO often just checks prediction on the original model 
        # with the feature zeroed out or permuted. 
        # The task asks for "R² variation across feature subsets", implying retraining.
        
        # Split for internal validation if needed, but here we assume we test on the 
        # provided test set X_subset directly using a fresh model trained on 
        # the training portion of X_subset? 
        # Actually, standard LOFO on a held-out test set:
        # 1. Retrain model on TRAIN set (minus feature)
        # 2. Evaluate on TEST set (minus feature)
        
        # Since we only have X (test set) here, we need to assume the 'model' passed
        # is the one trained on the full training set.
        # But we cannot retrain on the test set.
        # Correct approach for this script:
        # We need the training data to retrain. The task description says "Load pre-split data".
        # Let's load train/val/test to do this properly.
        pass

    return results

def main():
    """Execute the LOFO sensitivity analysis and generate the report."""
    config = get_config()
    logger = setup_logging()
    logger.info("Starting LOFO Sensitivity Analysis (T034)")

    # 1. Load Data
    # We need training data to retrain models for each subset
    # and test data to evaluate.
    data_path = Path(config.DATA_PATH)
    train_path = data_path / "processed" / "train.csv"
    test_path = data_path / "processed" / "test.csv"

    if not train_path.exists() or not test_path.exists():
        logger.error("Training or Test data missing. Run T017 first.")
        sys.exit(1)

    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    # Define features and target
    target = 'packing_coefficient'
    features = ['Volume', 'SurfaceArea', 'Dipole', 'HBD', 'HBA', 'PSA']
    
    # Ensure features exist
    missing = [f for f in features if f not in train_df.columns]
    if missing:
        logger.error(f"Missing required features: {missing}")
        sys.exit(1)

    X_train = train_df[features]
    y_train = train_df[target]
    X_test = test_df[features]
    y_test = test_df[target]

    # 2. Load the original model to get the baseline R²
    # Note: We assume the model was trained on 'features'.
    # We will retrain a fresh model for the baseline to ensure consistency.
    base_model = RandomForestRegressor(random_state=42, n_estimators=100)
    base_model.fit(X_train, y_train)
    baseline_r2 = r2_score(y_test, base_model.predict(X_test))
    
    logger.info(f"Baseline R² (All features): {baseline_r2:.4f}")

    # 3. Perform LOFO
    lofo_results = []
    for feature in features:
        subset_features = [f for f in features if f != feature]
        X_train_sub = X_train[subset_features]
        X_test_sub = X_test[subset_features]

        # Retrain model on subset
        sub_model = RandomForestRegressor(random_state=42, n_estimators=100)
        sub_model.fit(X_train_sub, y_train)
        
        # Evaluate
        r2_sub = r2_score(y_test, sub_model.predict(X_test_sub))
        delta = r2_sub - baseline_r2
        
        lofo_results.append({
            'feature': feature,
            'r2': r2_sub,
            'delta': delta
        })
        logger.info(f"LOFO: Removed '{feature}' -> R²: {r2_sub:.4f} (Δ: {delta:.4f})")

    # 4. Generate Report
    report_path = Path("results") / "sensitivity_report.md"
    report_path.parent.mkdir(exist_ok=True)

    # Check requirement: "removing the top 5 features changes R² by no more than ±0.02"
    # We sort by absolute delta to find the most impactful features.
    sorted_results = sorted(lofo_results, key=lambda x: abs(x['delta']), reverse=True)
    top_5_max_delta = max(abs(r['delta']) for r in sorted_results[:5])
    
    status = "PASS" if top_5_max_delta <= 0.02 else "WARN"
    # Note: The requirement "changes R² by no more than ±0.02" might be a target for 
    # the model to be robust, or a check on the data. We report the value.

    with open(report_path, 'w') as f:
        f.write("# Leave-One-Feature-Out (LOFO) Sensitivity Analysis\n\n")
        f.write(f"**Date**: {pd.Timestamp.now()}\n")
        f.write(f"**Baseline R²**: {baseline_r2:.4f}\n\n")
        
        f.write("## Summary\n")
        f.write(f"This analysis evaluates the impact of removing individual features on the model's predictive performance (R²).\n")
        f.write(f"The maximum R² change observed when removing any of the top 5 most critical features is **{top_5_max_delta:.4f}**.\n\n")
        
        f.write(f"### Verification Status\n")
        f.write(f"- **Threshold**: ±0.02\n")
        f.write(f"- **Observed Max Delta**: {top_5_max_delta:.4f}\n")
        f.write(f"- **Result**: {'PASS' if top_5_max_delta <= 0.02 else 'FAIL (Delta > 0.02)'}\n\n")

        f.write("## Detailed Results\n\n")
        f.write("| Feature | R² (Subset) | Δ R² |\n")
        f.write("| :--- | :--- | :--- |\n")
        
        for res in sorted_results:
            f.write(f"| {res['feature']} | {res['r2']:.4f} | {res['delta']:+.4f} |\n")

        f.write("\n## Conclusion\n")
        f.write("The model shows ")
        if top_5_max_delta < 0.01:
            f.write("high robustness to feature removal.\n")
        elif top_5_max_delta < 0.02:
            f.write("moderate robustness, with some features being critical.\n")
        else:
            f.write("sensitivity to specific feature removals.\n")

    logger.info(f"LOFO report generated at {report_path}")

if __name__ == "__main__":
    main()
