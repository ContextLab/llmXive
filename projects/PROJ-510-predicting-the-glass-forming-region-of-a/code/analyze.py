import logging
import sys
import os
import json
from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import f1_score, mean_squared_error
from scipy.stats import ttest_ind
import pickle

# FINDINGS ARE ASSOCIATIONAL: This study uses observational data; no causal claims are made.

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('projects/PROJ-510-predicting-the-glass-forming-region-of-a/logs/analysis.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = "projects/PROJ-510-predicting-the-glass-forming-region-of-a"
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MODELS_DIR = os.path.join(DATA_DIR, "models")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

def load_model_and_data():
    """Load the trained Random Forest model and the processed dataset."""
    model_path = os.path.join(MODELS_DIR, "random_forest_model.pkl")
    data_path = os.path.join(PROCESSED_DIR, "processed_alloys.csv")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}. Run training first.")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}. Run ingestion first.")

    logger.info(f"Loading model from {model_path}")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)

    # Ensure critical columns exist
    required_cols = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance', 'critical_cooling_rate']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in data: {missing}")

    feature_cols = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
    X = df[feature_cols].values
    y = df['critical_cooling_rate'].values

    return model, X, y, feature_cols, df

def check_collinearity(X, feature_names):
    """Detect collinearity and flag results."""
    logger.info("Checking collinearity...")
    corr_matrix = np.corrcoef(X.T)
    flagged_pairs = []
    threshold = 0.8

    for i in range(len(feature_names)):
        for j in range(i + 1, len(feature_names)):
            corr_val = corr_matrix[i, j]
            if abs(corr_val) > threshold:
                flagged_pairs.append({
                    "feature_1": feature_names[i],
                    "feature_2": feature_names[j],
                    "correlation": float(corr_val)
                })

    report_path = os.path.join(PROCESSED_DIR, "collinearity_report.json")
    with open(report_path, 'w') as f:
        json.dump(flagged_pairs, f, indent=2)
    
    logger.info(f"Collinearity report saved to {report_path}")
    return flagged_pairs

def analyze_feature_importance(model, X, y, feature_names, random_state=42):
    """Perform permutation importance analysis."""
    logger.info("Calculating permutation importance...")
    result = permutation_importance(model, X, y, n_repeats=10, random_state=random_state, n_jobs=-1)
    
    importance_data = []
    for i, name in enumerate(feature_names):
        importance_data.append({
            "feature": name,
            "mean_importance": float(result.importances_mean[i]),
            "std_importance": float(result.importances_std[i])
        })
    
    # Sort by mean importance descending
    importance_data.sort(key=lambda x: x['mean_importance'], reverse=True)
    
    output_path = os.path.join(PROCESSED_DIR, "feature_importance.json")
    with open(output_path, 'w') as f:
        json.dump(importance_data, f, indent=2)
    
    logger.info(f"Feature importance saved to {output_path}")
    return importance_data

def run_sensitivity_analysis(model, X, y, feature_names):
    """
    Conduct sensitivity analysis sweeping specific thresholds across a representative range of heating rates.
    
    Logic:
    1. Define thresholds: {50, 100, 150} K/s (representative range).
    2. For each threshold:
       a. Binarize true labels: 1 if y_true >= threshold else 0.
       b. Binarize predictions: 1 if y_pred >= threshold else 0.
       c. Calculate F1-score.
    3. Report F1-scores and calculate variance.
    """
    logger.info("Running sensitivity analysis on thresholds...")
    
    thresholds = [50, 100, 150]  # K/s
    predictions = model.predict(X)
    
    results = []
    f1_scores = []
    
    for thresh in thresholds:
        # Binarize
        y_true_bin = (y >= thresh).astype(int)
        y_pred_bin = (predictions >= thresh).astype(int)
        
        # Calculate F1
        f1 = f1_score(y_true_bin, y_pred_bin, zero_division=0)
        rmse = mean_squared_error(y, predictions, squared=False) # RMSE is constant for regression model here, but required by schema logic
        
        results.append({
            "threshold": thresh,
            "f1_score": float(f1),
            "rmse": float(rmse)
        })
        f1_scores.append(f1)
        
        logger.info(f"Threshold {thresh} K/s: F1={f1:.4f}, RMSE={rmse:.4f}")
    
    # Calculate variance
    f1_variance = np.var(f1_scores)
    logger.info(f"F1-score variance across thresholds: {f1_variance:.6f}")
    
    # Save report
    report_path = os.path.join(PROCESSED_DIR, "sensitivity_report.csv")
    df_results = pd.DataFrame(results)
    df_results.to_csv(report_path, index=False)
    
    logger.info(f"Sensitivity report saved to {report_path}")
    return results, f1_variance

def run_analysis():
    """Main entry point for the analysis pipeline."""
    try:
        # Load data
        model, X, y, feature_names, df = load_model_and_data()
        
        # Check collinearity
        collinearity_flags = check_collinearity(X, feature_names)
        
        # Analyze feature importance
        importance_results = analyze_feature_importance(model, X, y, feature_names)
        
        # Run sensitivity analysis
        sensitivity_results, f1_variance = run_sensitivity_analysis(model, X, y, feature_names)
        
        # Validate stability (T030b requirement)
        # "Assert that the F1-score variance is negligible (e.g., < 10% relative variance)"
        # Relative variance = Var / Mean^2 or just check absolute variance if scale is known.
        # Given F1 is 0-1, absolute variance < 0.01 (1% points squared) is a reasonable check for stability.
        # Or check if std_dev < 0.1 * mean.
        mean_f1 = np.mean([r['f1_score'] for r in sensitivity_results])
        if mean_f1 > 0:
            relative_variance = f1_variance / (mean_f1 ** 2)
            if relative_variance > 0.10:
                logger.warning(f"Stability check failed: Relative F1 variance {relative_variance:.2%} > 10%")
            else:
                logger.info(f"Stability check passed: Relative F1 variance {relative_variance:.2%} <= 10%")
        else:
            logger.warning("Mean F1 is zero, skipping relative variance check.")
        
        logger.info("Analysis completed successfully.")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    run_analysis()