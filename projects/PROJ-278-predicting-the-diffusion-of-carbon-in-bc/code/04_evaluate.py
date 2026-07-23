import os
import sys
import json
import logging
import pickle
from pathlib import Path
import numpy as np
import pandas as pd
import shap
from sklearn.metrics import r2_score
from sklearn.linear_model import LinearRegression
from sklearn.inspection import PartialDependenceDisplay
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI
import matplotlib.pyplot as plt

# Import custom exceptions from the local package
# Note: Using absolute import style compatible with running as script or module
try:
    from logging_config import setup_logger, handle_shap_error, SHAPError
    from config import get_path
except ImportError:
    # Fallback for direct script execution if __init__.py structure is not set up as package
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from logging_config import setup_logger, handle_shap_error, SHAPError
    from config import get_path

def load_best_model(model_path: str):
    """Load the best model from a pickle file."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_cleaned_data(data_path: str):
    """Load the cleaned dataset."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    return pd.read_csv(data_path)

def prepare_features(df, target_col='log_D'):
    """Prepare feature matrix X and target vector y."""
    feature_cols = [
        'atomic_radius_variance', 'VEC', 'electronegativity_spread',
        'mixing_entropy', 'inv_temperature'
    ]
    # Ensure all feature columns exist
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing feature columns: {missing_cols}")
    
    X = df[feature_cols].values
    y = df[target_col].values
    return X, y, feature_cols

def compute_shap_values(model, X_test, feature_names, logger):
    """
    Compute SHAP values for the model.
    Raises SHAPError if computation fails.
    """
    try:
        explainer = shap.Explainer(model, X_test)
        shap_values = explainer(X_test)
        return shap_values
    except Exception as e:
        logger.error(f"SHAP computation failed: {str(e)}")
        # Raise the custom SHAPError to halt execution gracefully as per T020
        raise SHAPError(f"Failed to compute SHAP values: {str(e)}") from e

def rank_features(shap_values, feature_names, logger):
    """Rank features by SHAP magnitude."""
    # Use absolute mean SHAP values for ranking
    if hasattr(shap_values, 'values'):
        shap_vals = shap_values.values
    else:
        shap_vals = shap_values

    mean_abs_shap = np.mean(np.abs(shap_vals), axis=0)
    ranks = np.argsort(mean_abs_shap)[::-1]
    
    ranked_features = []
    for i, idx in enumerate(ranks):
        ranked_features.append({
            "rank": i + 1,
            "feature": feature_names[idx],
            "mean_abs_shap": float(mean_abs_shap[idx])
        })
    
    logger.info(f"Feature ranking completed. Top 2: {[r['feature'] for r in ranked_features[:2]]}")
    return ranked_features

def generate_partial_dependence_plots(model, X_test, feature_names, output_dir, logger, top_n=2):
    """Generate and save partial dependence plots for top features."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Compute mean absolute SHAP to find top features if not passed
    # Re-calculate here to be safe
    shap_vals = model(X_test) if callable(model) else model
    if hasattr(shap_vals, 'values'):
        vals = shap_vals.values
    else:
        vals = shap_vals
    mean_abs = np.mean(np.abs(vals), axis=0)
    top_indices = np.argsort(mean_abs)[::-1][:top_n]
    
    top_features = [feature_names[i] for i in top_indices]
    
    # Create figure
    fig, axes = plt.subplots(1, len(top_features), figsize=(5 * len(top_features), 5))
    if len(top_features) == 1:
        axes = [axes]
    
    for i, feature in enumerate(top_features):
        col_idx = feature_names.index(feature)
        disp = PartialDependenceDisplay.from_estimator(
            model, X_test, [col_idx], ax=axes[i]
        )
        axes[i].set_title(f"PDP for {feature}")
    
    plt.tight_layout()
    plot_path = os.path.join(output_dir, "partial_dependence_plots.png")
    plt.savefig(plot_path)
    plt.close()
    logger.info(f"Partial dependence plots saved to {plot_path}")
    return plot_path

def calculate_variance_partitioning(model, X_test, y_test, logger):
    """
    Calculate variance partitioning metrics.
    Returns a DataFrame with adjusted R^2, microstructural gap, and residual label.
    """
    # Predict using the model
    y_pred = model.predict(X_test)
    
    # Total variance of the target
    total_variance = np.var(y_test, ddof=1)
    
    # R^2 score
    r2 = r2_score(y_test, y_pred)
    
    # Adjusted R^2 (approximation for small datasets or simple models)
    # n = number of samples, p = number of features
    n = len(y_test)
    p = X_test.shape[1]
    if n > p + 1:
        adj_r2 = 1 - (1 - r2) * (n - 1) / (n - p - 1)
    else:
        adj_r2 = r2  # Fallback if degrees of freedom are insufficient
    
    # Microstructural gap: 1 - adjusted R^2 (per FR-007 and T019)
    microstructural_gap = 1.0 - adj_r2
    
    # Residual variance label (per FR-007)
    residual_label = "noise, measurement error, and missing compositional descriptors"
    
    # Create DataFrame
    df_results = pd.DataFrame([
        {
            "metric": "adjusted_r2",
            "value": float(adj_r2),
            "description": "Fraction of variance explainable by composition"
        },
        {
            "metric": "microstructural_gap",
            "value": float(microstructural_gap),
            "description": "Unexplained variance (gap)"
        },
        {
            "metric": "residual_label",
            "value": residual_label,
            "description": "Source of residual variance"
        }
    ])
    
    logger.info(f"Variance partitioning calculated. Adjusted R^2: {adj_r2:.4f}, Gap: {microstructural_gap:.4f}")
    return df_results

def main():
    logger = setup_logger("04_evaluate")
    logger.info("Starting evaluation phase (T019/T020)")

    # Paths
    config_path = get_path("config.yaml")
    # Load config to get paths if not hardcoded, or use defaults based on plan
    # Assuming standard paths from plan.md
    data_dir = get_path("data/processed")
    output_dir = get_path("data/outputs")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Load data
    try:
        df = load_cleaned_data(os.path.join(data_dir, "dataset_cleaned.csv"))
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        sys.exit(1)

    X, y, feature_names = prepare_features(df)

    # Split data (simple holdout for evaluation, assuming train/test split already done or re-splitting)
    # Note: T015 saves best_model.pkl. We assume the model was trained on a split.
    # For evaluation, we need the test set features.
    # If T015 did not save the test set, we must re-split or assume the model is generalizable to the whole set for demonstration.
    # However, to be rigorous, T015 should have saved the test indices or the model was evaluated on a held-out set.
    # Given the constraints, we will re-split deterministically to get a test set for SHAP if not provided.
    # Ideally, T015 saves the test set X_test, y_test. If not, we do a quick split here.
    
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Load models
    best_model_path = os.path.join(output_dir, "best_model.pkl")
    baseline_model_path = os.path.join(output_dir, "baseline_model.pkl")
    
    try:
        best_model = load_best_model(best_model_path)
        baseline_model = load_best_model(baseline_model_path)
        logger.info("Models loaded successfully.")
    except FileNotFoundError as e:
        logger.error(f"Model loading failed: {e}")
        sys.exit(1)

    # 1. Compute SHAP values (T019)
    # T020: Handle SHAPError by logging and halting
    try:
        shap_values = compute_shap_values(best_model, X_test, feature_names, logger)
    except SHAPError as e:
        handle_shap_error(e, logger)
        # Halting execution gracefully
        sys.exit(1)

    # 2. Rank features (T019)
    ranked_features = rank_features(shap_values, feature_names, logger)
    
    # Save feature importance
    feature_importance_path = os.path.join(output_dir, "feature_importance.json")
    with open(feature_importance_path, 'w') as f:
        json.dump({"ranked_features": ranked_features}, f, indent=2)
    logger.info(f"Feature importance saved to {feature_importance_path}")

    # 3. Generate Partial Dependence Plots (T019)
    try:
        plot_path = generate_partial_dependence_plots(best_model, X_test, feature_names, output_dir, logger)
    except Exception as e:
        logger.error(f"Partial dependence plot generation failed: {e}")
        # Continue, but log error. This is not a fatal SHAPError but a plotting error.

    # 4. Calculate Variance Partitioning (T019)
    variance_df = calculate_variance_partitioning(best_model, X_test, y_test, logger)
    variance_path = os.path.join(output_dir, "variance_partition.csv")
    variance_df.to_csv(variance_path, index=False)
    logger.info(f"Variance partitioning saved to {variance_path}")

    logger.info("Evaluation phase completed successfully.")

if __name__ == "__main__":
    main()