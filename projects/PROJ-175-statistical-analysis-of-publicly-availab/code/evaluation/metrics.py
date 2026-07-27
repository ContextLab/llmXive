"""
Metrics Calculation for Recipe Substitution Prediction Models.

Computes AUC, precision, recall, and generates a calibration plot for
the Full and Baseline (Null) models. Outputs results to data/evaluation_metrics.json.

Dependencies:
    - data/final/logistic_results.json (produced by T022)
    - data/split_config.json (produced by T019)
    - data/raw/test_set.parquet (produced by T019)
"""
import os
import sys
import json
import pickle
import warnings
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, precision_score, recall_score, brier_score_loss
from sklearn.calibration import calibration_curve
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt

# Ensure paths are relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
FINAL_DIR = DATA_DIR / "final"

# Ensure output directories exist
FINAL_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "figures").mkdir(parents=True, exist_ok=True)

def load_test_data():
    """Load the test set from the processed split."""
    test_path = DATA_DIR / "raw" / "test_set.parquet"
    if not test_path.exists():
        raise FileNotFoundError(f"Test set not found at {test_path}. Run T019 first.")
    return pd.read_parquet(test_path)

def load_models():
    """
    Load the fitted logistic regression models from T022.
    Expects data/final/logistic_results.json containing serialized model objects.
    """
    results_path = FINAL_DIR / "logistic_results.json"
    if not results_path.exists():
        raise FileNotFoundError(f"Logistic results not found at {results_path}. Run T022 first.")

    with open(results_path, 'r') as f:
        raw_data = json.load(f)

    # The JSON contains pickled model strings or dicts depending on implementation.
    # Assuming T022 saved the model dictionaries directly or pickled strings.
    # If T022 saved pickled bytes as base64 or similar, we would decode here.
    # For this implementation, we assume T022 saved the model coefficients and intercepts
    # in a structured dict, or we load the pickled model if T022 did that.
    # To be robust, we check if 'models' key exists.
    
    models = {}
    # We expect T022 to have saved the model objects or their parameters.
    # If T022 saved a dict like {'full_model': {...}, 'null_model': {...}}, we use that.
    # If T022 saved a pickle file path, we load it.
    # Given the constraints, we assume the JSON contains the model state.
    # If T022 saved actual sklearn objects as pickled bytes in the JSON, we need to unpickle.
    # However, standard JSON doesn't support bytes. So T022 likely saved coefficients.
    # Let's assume T022 saved the models as a dictionary of parameters or we reconstruct them.
    # For safety, if T022 saved a 'model_pickle' key, we load it. Otherwise, we reconstruct.
    
    # Fallback: If the file contains a 'models' section with pickled strings (base64), handle it.
    # But since we can't guarantee T022's exact output format without seeing it, 
    # we will assume the standard output of fit_logistic.py which likely saves coefficients.
    # We will reconstruct the models for prediction.
    
    if 'models' in raw_data:
        # If T022 saved the models as a dictionary of coefficients
        models['full'] = raw_data['models'].get('full_model')
        models['null'] = raw_data['models'].get('null_model')
    else:
        # Fallback if structure is different
        models['full'] = raw_data.get('full_model')
        models['null'] = raw_data.get('null_model')

    if not models['full'] or not models['null']:
        raise ValueError("Models not found in logistic_results.json. Ensure T022 completed successfully.")

    return models

def get_predictions(model_params, X):
    """
    Compute predictions for a logistic regression model given its parameters.
    
    Args:
        model_params (dict): Dictionary containing 'coef' and 'intercept'.
        X (pd.DataFrame): Feature matrix.
        
    Returns:
        np.ndarray: Predicted probabilities.
    """
    if model_params is None:
        raise ValueError("Model parameters are missing.")
    
    coef = np.array(model_params['coef']).flatten()
    intercept = model_params['intercept']
    
    # Ensure X columns match the model's training columns
    # If X has extra columns or is missing some, we must handle it.
    # For this task, we assume X is pre-aligned with the model's features.
    # If not, we align:
    model_cols = model_params.get('feature_names', list(X.columns))
    
    # Create a matrix of only the features the model expects, in order
    try:
        X_model = X[model_cols].values
    except KeyError as e:
        raise KeyError(f"Missing feature {e} in test data. Model expected: {model_cols}")

    # Linear combination: X * coef + intercept
    logits = np.dot(X_model, coef) + intercept
    
    # Sigmoid function
    probs = 1 / (1 + np.exp(-logits))
    return probs

def calculate_metrics(y_true, y_pred_proba, model_name):
    """
    Calculate AUC, Precision, Recall, and Brier Score.
    """
    # Threshold for binary classification (default 0.5)
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    auc = roc_auc_score(y_true, y_pred_proba)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    brier = brier_score_loss(y_true, y_pred_proba)
    
    return {
        "model": model_name,
        "auc": float(auc),
        "precision": float(precision),
        "recall": float(recall),
        "brier_score": float(brier)
    }

def generate_calibration_plot(y_true, y_pred_proba_full, y_pred_proba_null, output_path):
    """
    Generate a calibration plot for both models.
    """
    plt.figure(figsize=(10, 8))
    
    # Full Model
    prob_true_full, prob_pred_full = calibration_curve(y_true, y_pred_proba_full, n_bins=10)
    plt.plot(prob_pred_full, prob_true_full, marker='o', label='Full Model', linewidth=2)
    
    # Null Model
    prob_true_null, prob_pred_null = calibration_curve(y_true, y_pred_proba_null, n_bins=10)
    plt.plot(prob_pred_null, prob_true_null, marker='s', label='Null Model', linewidth=2)
    
    # Ideal line
    plt.plot([0, 1], [0, 1], 'k--', label='Perfect Calibration')
    
    plt.xlabel('Predicted Probability')
    plt.ylabel('True Probability')
    plt.title('Model Calibration')
    plt.legend()
    plt.grid(True)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def main():
    print("Starting Metrics Calculation (T029)...")
    
    try:
        # 1. Load Data
        print("Loading test data...")
        df_test = load_test_data()
        
        # Identify target column (assumed to be 'compatibility_label' based on T013c)
        target_col = 'compatibility_label'
        if target_col not in df_test.columns:
            # Fallback if column name differs
            target_col = [c for c in df_test.columns if 'label' in c.lower()][0]
        
        y_true = df_test[target_col].values
        
        # 2. Load Models
        print("Loading models...")
        models = load_models()
        
        # 3. Prepare Features for Prediction
        # We need the feature columns used by the models.
        # These are stored in the model_params or in final_predictors.json
        predictors_path = DATA_DIR / "final_predictors.json"
        if predictors_path.exists():
            with open(predictors_path, 'r') as f:
                predictors_config = json.load(f)
            feature_cols = predictors_config.get('predictors', [])
        else:
            # Fallback: try to infer from model params
            feature_cols = models['full'].get('feature_names', [])
        
        X_test = df_test[feature_cols]
        
        # 4. Generate Predictions
        print("Generating predictions...")
        y_pred_full = get_predictions(models['full'], X_test)
        y_pred_null = get_predictions(models['null'], X_test)
        
        # 5. Calculate Metrics
        print("Calculating metrics...")
        metrics_full = calculate_metrics(y_true, y_pred_full, "Full Model")
        metrics_null = calculate_metrics(y_true, y_pred_null, "Null Model")
        
        # 6. Generate Calibration Plot
        print("Generating calibration plot...")
        cal_plot_path = DATA_DIR / "figures" / "calibration_plot.png"
        generate_calibration_plot(y_true, y_pred_full, y_pred_null, cal_plot_path)
        
        # 7. Compile Results
        results = {
            "task_id": "T029",
            "timestamp": pd.Timestamp.now().isoformat(),
            "metrics": {
                "full_model": metrics_full,
                "null_model": metrics_null
            },
            "calibration_plot_path": str(cal_plot_path.relative_to(PROJECT_ROOT))
        }
        
        # 8. Save Output
        output_path = DATA_DIR / "evaluation_metrics.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Metrics calculation complete. Output saved to {output_path}")
        
    except Exception as e:
        print(f"Error during metrics calculation: {e}")
        # Log error but do not fabricate results
        raise

if __name__ == "__main__":
    import argparse
    import numpy as np
    main()
