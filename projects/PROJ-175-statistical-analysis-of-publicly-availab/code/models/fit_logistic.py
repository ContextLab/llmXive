"""
Fit Logistic Regression Models for Ingredient Compatibility Prediction.

This module implements the fitting of:
1. Null Model: Compatibility ~ Frequency (log)
2. Full Model: Compatibility ~ Frequency (log) + Flavor Similarity + Functional Role

Using L2 regularization (Ridge) as specified in FR-006.
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score
from sklearn.preprocessing import StandardScaler
from scipy.stats import chi2
import joblib

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data.split import load_subset_size, create_train_test_split
from utils.memory_monitor import check_memory_limit

def load_processed_data(data_path: Path) -> pd.DataFrame:
    """
    Load the pre-processed dataset from the final data directory.
    Expects the output of the preprocessing pipeline (T018).
    """
    # The preprocessing pipeline outputs to data/final/processed_data.csv (standard convention)
    # or specifically the file defined in the pipeline output.
    # We assume the standard output path based on T018 description.
    file_path = data_path / "final" / "processed_data.csv"
    
    if not file_path.exists():
        # Fallback to common alternative if strict path not found
        alt_path = data_path / "final" / "ingredient_pairs.csv"
        if alt_path.exists():
            file_path = alt_path
        else:
            raise FileNotFoundError(
                f"Processed data file not found at {file_path} or {alt_path}. "
                "Ensure T018 (preprocess) has been run successfully."
            )
    
    df = pd.read_csv(file_path)
    return df

def prepare_features(df: pd.DataFrame) -> tuple:
    """
    Prepare X and y for logistic regression.
    
    Features:
    - log_frequency: from 'log_frequency' column (T015)
    - flavor_similarity: from 'flavor_similarity' column (T016)
    - functional_role: from 'functional_role' column (T017b) -> One-Hot Encoded
    
    Target:
    - compatibility: from 'compatibility' column (Counterfactual labels)
    """
    # Check memory
    check_memory_limit()
    
    # Target
    y = df['compatibility'].values.astype(int)
    
    # Features - Null Model (Frequency only)
    X_null = df[['log_frequency']].values
    
    # Features - Full Model (Frequency + Similarity + Role)
    X_full_base = df[['log_frequency', 'flavor_similarity']].values
    
    # Handle Functional Role (Categorical)
    # T017b produces categorical labels: Primary, Secondary, Garnish, Unknown
    role_dummies = pd.get_dummies(df['functional_role'], prefix='role')
    role_cols = role_dummies.columns
    X_role = role_dummies.values.astype(float)
    
    X_full = np.hstack([X_full_base, X_role])
    
    feature_names_full = ['log_frequency', 'flavor_similarity'] + list(role_cols)
    
    return X_null, X_full, y, feature_names_full

def fit_logistic_models(
    X_null: np.ndarray, 
    X_full: np.ndarray, 
    y: np.ndarray,
    feature_names: list
) -> dict:
    """
    Fit Null and Full Logistic Regression models with L2 regularization.
    
    Returns a dictionary containing model coefficients, metrics, and artifacts.
    """
    check_memory_limit()
    
    # Scale features (StandardScaler)
    scaler = StandardScaler()
    X_null_scaled = scaler.fit_transform(X_null)
    X_full_scaled = scaler.fit_transform(X_full)
    
    # Split data (stratified) - using the split logic from T019 if available, 
    # otherwise doing a local split here to ensure we have train/test for metrics.
    # Note: T019 creates the split, but we need to re-split the arrays for training 
    # if the split file only contains indices. Assuming we train on the provided subset.
    # For this task, we perform a local 80/20 split to calculate metrics.
    X_train_null, X_test_null, y_train, y_test = train_test_split(
        X_null_scaled, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train_full, X_test_full, _, _ = train_test_split(
        X_full_scaled, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Fit Null Model
    # C=1.0 is default L2 penalty strength in sklearn
    null_model = LogisticRegression(
        penalty='l2', 
        C=1.0, 
        solver='lbfgs', 
        max_iter=1000, 
        random_state=42
    )
    null_model.fit(X_train_null, y_train)
    
    # Fit Full Model
    full_model = LogisticRegression(
        penalty='l2', 
        C=1.0, 
        solver='lbfgs', 
        max_iter=1000, 
        random_state=42
    )
    full_model.fit(X_train_full, y_train)
    
    # Calculate Metrics
    # Null Model
    y_pred_null = null_model.predict(X_test_null)
    y_prob_null = null_model.predict_proba(X_test_null)[:, 1]
    auc_null = roc_auc_score(y_test, y_prob_null)
    acc_null = accuracy_score(y_test, y_pred_null)
    
    # Full Model
    y_pred_full = full_model.predict(X_test_full)
    y_prob_full = full_model.predict_proba(X_test_full)[:, 1]
    auc_full = roc_auc_score(y_test, y_prob_full)
    acc_full = accuracy_score(y_test, y_pred_full)
    
    # Likelihood Ratio Test (Approximation using AIC/BIC or Coefficients)
    # Since sklearn doesn't expose log-likelihood directly for LRT p-value,
    # we calculate the difference in deviance.
    # Deviance = -2 * log_likelihood
    # LRT Statistic = Deviance_null - Deviance_full
    # Degrees of freedom = df_full - df_null
    
    # We approximate log-likelihood from the model scores if available, 
    # or use the AIC/BIC difference as a proxy for model improvement.
    # A more robust way for LRT with sklearn is to use the `statsmodels` API,
    # but the task specifies using the existing API surface which implies sklearn usage
    # unless statsmodels is explicitly imported. However, T024 handles the LRT formally.
    # Here we just return the metrics and coefficients.
    
    results = {
        "null_model": {
            "coefficients": null_model.coef_[0].tolist(),
            "intercept": float(null_model.intercept_[0]),
            "auc": float(auc_null),
            "accuracy": float(acc_null),
            "feature_names": ["log_frequency"]
        },
        "full_model": {
            "coefficients": full_model.coef_[0].tolist(),
            "intercept": float(full_model.intercept_[0]),
            "auc": float(auc_full),
            "accuracy": float(acc_full),
            "feature_names": feature_names
        },
        "metrics": {
            "auc_delta": float(auc_full - auc_null),
            "accuracy_delta": float(acc_full - acc_null)
        }
    }
    
    return results, null_model, full_model, scaler

def save_models_and_results(
    results: dict, 
    null_model: LogisticRegression, 
    full_model: LogisticRegression, 
    scaler: StandardScaler,
    output_dir: Path
):
    """
    Save model artifacts and results JSON.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON results
    results_path = output_dir / "logistic_regression_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save Scikit-Learn models
    joblib.dump(null_model, output_dir / "null_model.pkl")
    joblib.dump(full_model, output_dir / "full_model.pkl")
    joblib.dump(scaler, output_dir / "scaler.pkl")
    
    print(f"Models and results saved to {output_dir}")
    print(f"Null Model AUC: {results['null_model']['auc']:.4f}")
    print(f"Full Model AUC: {results['full_model']['auc']:.4f}")
    print(f"AUC Delta: {results['metrics']['auc_delta']:.4f}")

def main():
    """
    Main execution function for T022.
    """
    print("Starting T022: Fit Logistic Regression Models...")
    
    # Load subset size from T008a
    subset_size = load_subset_size("logistic")
    print(f"Using subset size N_logistic: {subset_size}")
    
    # Load data
    data_path = Path("data")
    df = load_processed_data(data_path)
    
    # Apply subset if necessary (T019 should have done this, but ensure it)
    if len(df) > subset_size:
        df = df.sample(n=subset_size, random_state=42)
        print(f"Downsampled to {subset_size} rows.")
    
    # Prepare features
    X_null, X_full, y, feature_names = prepare_features(df)
    
    # Fit models
    results, null_model, full_model, scaler = fit_logistic_models(
        X_null, X_full, y, feature_names
    )
    
    # Save outputs
    output_dir = Path("data/final")
    save_models_and_results(results, null_model, full_model, scaler, output_dir)
    
    print("T022 completed successfully.")

if __name__ == "__main__":
    main()