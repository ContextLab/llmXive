import os
import sys
import json
import pickle
import numpy as np
from pathlib import Path
from scipy import stats

# Project root is one level up from code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = DATA_DIR / "artifacts"
PROCESSED_DIR = DATA_DIR / "processed"

def load_test_data():
    """Load the processed dataset used for evaluation."""
    file_path = PROCESSED_DIR / "solubility_features.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Test data file not found: {file_path}")
    import pandas as pd
    return pd.read_csv(file_path)

def load_models():
    """Load trained models and metrics from the training artifact."""
    file_path = ARTIFACTS_DIR / "trained_models.pkl"
    if not file_path.exists():
        raise FileNotFoundError(f"Model artifact not found: {file_path}")
    with open(file_path, 'rb') as f:
        return pickle.load(f)

def calculate_metrics(models, df):
    """
    Calculate absolute errors for XGBoost and Abraham models.
    Assumes the dataframe has 'logS' (true) and prediction columns.
    """
    # Ensure we have predictions
    if 'logS_pred_xgboost' not in df.columns or 'logS_pred_abraham' not in df.columns:
        raise ValueError("DataFrame must contain prediction columns: logS_pred_xgboost, logS_pred_abraham")
    
    y_true = df['logS'].values
    y_pred_xgb = df['logS_pred_xgboost'].values
    y_pred_abr = df['logS_pred_abraham'].values

    abs_error_xgb = np.abs(y_true - y_pred_xgb)
    abs_error_abr = np.abs(y_true - y_pred_abr)

    return {
        'abs_error_xgboost': abs_error_xgb.tolist(),
        'abs_error_abraham': abs_error_abr.tolist()
    }

def perform_paired_ttest(abs_error_xgb, abs_error_abr, alpha=0.05):
    """
    Perform a paired t-test on absolute errors per Constitution Principle VII.
    Returns p-value, t-statistic, and a boolean indicating if the difference is significant.
    """
    t_stat, p_value = stats.ttest_rel(abs_error_xgb, abs_error_abr)
    significant = p_value < alpha
    return {
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'alpha': alpha,
        'is_significant': significant,
        'method': 'paired_t_test',
        'hypothesis': 'Constitution Principle VII: Paired t-test on absolute errors'
    }

def compute_shap_values():
    """
    Compute SHAP values for the best model using a background sample.
    Reads 'best_model' from trained_models.pkl and samples 100 rows from solubility_features.csv.
    Writes SHAP values to data/artifacts/shap_values.npy.
    """
    try:
        import shap
        import pandas as pd
    except ImportError as e:
        print(f"ERROR: Required library 'shap' not installed. Please install it via requirements.txt.", file=sys.stderr)
        sys.exit(1)

    print("Loading test data for SHAP background sample...")
    df = load_test_data()

    print("Loading trained models...")
    models = load_models()

    if 'best_model' not in models:
        raise KeyError("Key 'best_model' not found in trained_models.pkl. Ensure T021/T022 completed successfully.")

    best_model = models['best_model']

    # Determine feature columns (exclude target and non-feature columns if any)
    # Assuming the dataset has a specific set of feature columns used during training.
    # We need to identify these. Usually, the last column is the target 'logS'.
    feature_cols = [col for col in df.columns if col not in ['logS', 'solute_smiles', 'solvent_smiles']]
    
    if not feature_cols:
        # Fallback: assume all except 'logS' are features
        feature_cols = [col for col in df.columns if col != 'logS']

    X = df[feature_cols].values
    y = df['logS'].values

    # Sample 100 rows for background data as per task requirement
    n_samples = min(100, X.shape[0])
    if n_samples < 10:
        print("WARNING: Dataset too small for meaningful SHAP background sampling.", file=sys.stderr)
        n_samples = X.shape[0]
    
    np.random.seed(42) # Use constant seed for reproducibility
    indices = np.random.choice(X.shape[0], n_samples, replace=False)
    background_data = X[indices]

    print(f"Computing SHAP values for {n_samples} background samples...")
    
    # Initialize SHAP explainer
    # For tree-based models (XGBoost/RF), TreeExplainer is preferred
    try:
        explainer = shap.TreeExplainer(best_model)
        shap_values = explainer.shap_values(X)
    except Exception as e:
        print(f"Error initializing TreeExplainer: {e}. Falling back to KernelExplainer.", file=sys.stderr)
        # Fallback for non-tree models or if TreeExplainer fails
        explainer = shap.KernelExplainer(best_model.predict, background_data)
        shap_values = explainer.shap_values(X, nsamples=100)

    # Handle output format for binary classification (if applicable) vs regression
    # For regression, shap_values is usually (n_samples, n_features)
    if isinstance(shap_values, list):
        # If list (e.g., multi-class), take the first or relevant class
        shap_values = shap_values[0] if len(shap_values) > 0 else np.array([])
    
    shap_values = np.array(shap_values)

    output_path = ARTIFACTS_DIR / "shap_values.npy"
    print(f"Saving SHAP values to {output_path}...")
    np.save(output_path, shap_values)

    print(f"SHAP computation completed. Shape: {shap_values.shape}")
    return shap_values

def evaluate_models():
    """
    Main evaluation function:
    1. Load data and models.
    2. Calculate absolute errors.
    3. Perform paired t-test.
    4. Compute SHAP values (T029).
    5. Save results.
    """
    print("Loading test data...")
    df = load_test_data()
    
    print("Loading trained models...")
    models = load_models()
    
    print("Calculating metrics...")
    metrics = calculate_metrics(models, df)
    
    print("Performing paired t-test (Constitution Principle VII)...")
    ttest_results = perform_paired_ttest(
        metrics['abs_error_xgboost'], 
        metrics['abs_error_abraham']
    )
    
    output_path = ARTIFACTS_DIR / "statistical_test_results.json"
    print(f"Saving statistical test results to {output_path}...")
    
    with open(output_path, 'w') as f:
        json.dump(ttest_results, f, indent=2)
    
    print(f"Results saved. P-value: {ttest_results['p_value']:.4f}, Significant: {ttest_results['is_significant']}")

    # --- T029: SHAP Computation ---
    print("\n--- Starting T029: SHAP Value Computation ---")
    try:
        compute_shap_values()
        print("T029 completed successfully.")
    except Exception as e:
        print(f"ERROR during T029 (SHAP computation): {e}", file=sys.stderr)
        # Do not fail the whole script if SHAP fails, but log it clearly
        # However, per task requirement, we must write the artifact.
        # If it fails to compute, we cannot write a valid artifact.
        # We let the exception propagate or exit if critical.
        sys.exit(1)
    
    return ttest_results

def save_results(results):
    """Helper to save results if called externally."""
    output_path = ARTIFACTS_DIR / "statistical_test_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    """Entry point for the script."""
    try:
        results = evaluate_models()
        print("Evaluation completed successfully.")
        sys.exit(0)
    except Exception as e:
        print(f"Error during evaluation: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()