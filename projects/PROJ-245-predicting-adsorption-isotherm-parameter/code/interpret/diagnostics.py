import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

# Ensure we can import from the project root if run as a script
# Note: In the actual pipeline, this is imported as `from interpret.diagnostics import ...`
# The API surface provided for shap_analysis.py suggests we should add our public names there
# or create a new file. Since the task asks to implement this logic, we create the file.
# We will ensure the main entry point matches the pattern.

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_dirs(output_dir: str = "data/validation") -> Path:
    """Ensure the output directory exists."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path

def load_models(model_dir: str = "data/models") -> Dict[str, Any]:
    """Load trained models from the models directory."""
    model_dir_path = Path(model_dir)
    if not model_dir_path.exists():
        logger.warning(f"Model directory {model_dir} does not exist. Returning empty dict.")
        return {}
    
    models = {}
    # Assuming models are saved as .pkl or similar, but for this diagnostic task
    # we assume the evaluation step has already determined the best model and its metrics.
    # We will load the evaluation results which contain the R2 scores.
    eval_file = model_dir_path / "evaluation_results.json"
    if eval_file.exists():
        with open(eval_file, 'r') as f:
            eval_data = json.load(f)
            models = eval_data.get('models', {})
    return models

def load_test_data(data_path: str = "data/processed/processed_data.csv") -> pd.DataFrame:
    """Load the test dataset."""
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Test data file not found: {data_path}")
    return pd.read_csv(path)

def generate_nonlinear_features(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    """
    Generate polynomial and interaction features to test for non-linear effects.
    Returns a new DataFrame with original features + new features.
    """
    if len(feature_cols) < 1:
        return df
    
    new_features = {}
    
    # Squared terms
    for col in feature_cols:
        new_features[f"{col}_sq"] = df[col] ** 2
    
    # Pairwise interactions (if more than 1 feature)
    if len(feature_cols) > 1:
        for i in range(len(feature_cols)):
            for j in range(i + 1, len(feature_cols)):
                c1, c2 = feature_cols[i], feature_cols[j]
                new_features[f"{c1}_x_{c2}"] = df[c1] * df[c2]
    
    if new_features:
        new_df = pd.DataFrame(new_features)
        return pd.concat([df.reset_index(drop=True), new_df], axis=1)
    return df

def diagnose_nonlinearity(
    X_train: pd.DataFrame, 
    y_train: pd.Series, 
    X_test: pd.DataFrame, 
    y_test: pd.Series,
    base_model_name: str = "RandomForest"
) -> Dict[str, Any]:
    """
    Diagnose if a low R2 (< 0.5) is due to non-linear effects.
    Strategy:
    1. Train a linear model on the original features.
    2. Train a linear model on expanded features (polynomial/interactions).
    3. Compare R2 scores. If the expanded linear model significantly improves R2,
       it suggests the original model failure was due to missing non-linear terms.
    """
    results = {
        "base_r2": None,
        "expanded_r2": None,
        "improvement": None,
        "conclusion": "",
        "recommendations": []
    }

    try:
        # 1. Baseline Linear Regression on original features
        lr_base = LinearRegression()
        lr_base.fit(X_train, y_train)
        y_pred_base = lr_base.predict(X_test)
        base_r2 = r2_score(y_test, y_pred_base)
        results["base_r2"] = float(base_r2)

        # 2. Generate expanded features
        feature_cols = X_train.columns.tolist()
        X_train_exp = generate_nonlinear_features(X_train, feature_cols)
        X_test_exp = generate_nonlinear_features(X_test, feature_cols)

        # 3. Linear Regression on expanded features
        lr_exp = LinearRegression()
        lr_exp.fit(X_train_exp, y_train)
        y_pred_exp = lr_exp.predict(X_test_exp)
        expanded_r2 = r2_score(y_test, y_pred_exp)
        results["expanded_r2"] = float(expanded_r2)

        # 4. Calculate improvement
        improvement = expanded_r2 - base_r2
        results["improvement"] = float(improvement)

        # 5. Conclusion logic
        if base_r2 < 0.5 and improvement > 0.15:
            results["conclusion"] = "Strong evidence of non-linear effects. The linear model with polynomial/interaction terms significantly outperforms the baseline linear model."
            results["recommendations"].append("Consider using non-linear models (e.g., Kernel Ridge, SVM with RBF) or explicitly engineer polynomial features for the pipeline.")
        elif base_r2 < 0.5 and improvement > 0.05:
            results["conclusion"] = "Moderate evidence of non-linear effects. Some improvement seen with expanded features."
            results["recommendations"].append("Review feature engineering to capture known physicochemical non-linearities.")
        elif base_r2 < 0.5:
            results["conclusion"] = "Low R2 observed, but polynomial expansion did not significantly improve performance. The issue may be data scarcity, noise, or missing critical descriptors rather than simple non-linearity."
            results["recommendations"].append("Check for missing descriptors (e.g., specific electronic properties) or data quality issues.")
        else:
            results["conclusion"] = "Base model performance is acceptable (R2 >= 0.5). No non-linearity diagnosis needed."

    except Exception as e:
        logger.error(f"Error during non-linearity diagnosis: {e}")
        results["error"] = str(e)
        results["conclusion"] = "Diagnosis failed due to an error."

    return results

def run_diagnostic_pipeline(
    eval_results_path: str = "data/models/evaluation_results.json",
    data_path: str = "data/processed/processed_data.csv",
    model_dir: str = "data/models",
    output_path: str = "data/validation/nonlinearity_diagnostic_report.json"
) -> None:
    """
    Main pipeline to generate the diagnostic report for low R2 cases.
    This function is intended to be called by the orchestrator (main.py) 
    when the evaluation phase detects R2 < 0.5.
    """
    output_dir = ensure_dirs(Path(output_path).parent)
    
    # Load evaluation results to check R2
    if not Path(eval_results_path).exists():
        logger.warning(f"Evaluation results not found at {eval_results_path}. Skipping diagnosis.")
        return

    with open(eval_results_path, 'r') as f:
        eval_data = json.load(f)
    
    # Find the best model's R2
    best_model_name = eval_data.get('best_model', {})
    best_r2 = best_model_name.get('r2', 1.0) # Default to high if not found
    
    if best_r2 >= 0.5:
        logger.info(f"Best model R2 is {best_r2:.4f} (>= 0.5). No diagnostic report needed.")
        # Still create a report stating this
        report = {
            "status": "passed",
            "best_model_r2": best_r2,
            "conclusion": "No non-linearity diagnosis required as R2 >= 0.5.",
            "recommendations": []
        }
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return

    logger.warning(f"Best model R2 is {best_r2:.4f} (< 0.5). Generating diagnostic report.")

    # Load data
    df = load_test_data(data_path)
    
    # Determine feature columns and target
    # Assuming standard columns from the project spec
    target_col = "langmuir_capacity" # Or "henry_constant" depending on what failed
    if target_col not in df.columns:
        # Fallback to any numeric column that looks like a target
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        target_col = numeric_cols[-1] if len(numeric_cols) > 0 else None
    
    if not target_col:
        logger.error("Could not identify target column.")
        return

    feature_cols = [c for c in df.columns if c != target_col and c not in ['material_id', 'adsorbate_smiles']]
    if not feature_cols:
        logger.error("No feature columns found.")
        return

    X = df[feature_cols]
    y = df[target_col]

    # We need a train/test split to simulate the evaluation context for the diagnosis
    # Since the evaluation already happened, we assume the data passed to this function
    # is the test set, but we need a training set to train the diagnostic models.
    # In a real scenario, we would load the training set or re-split.
    # For this implementation, we will do a simple random split on the loaded data 
    # to demonstrate the diagnostic logic, acknowledging this is a simulation of the
    # diagnostic step on the current dataset.
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Run diagnosis
    diagnosis = diagnose_nonlinearity(X_train, y_train, X_test, y_test)
    
    report = {
        "status": "diagnosed",
        "best_model_r2": best_r2,
        "diagnostic_results": diagnosis,
        "timestamp": str(pd.Timestamp.now())
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Diagnostic report written to {output_path}")

def main():
    """Entry point for running the diagnostic script directly."""
    run_diagnostic_pipeline()

if __name__ == "__main__":
    main()
