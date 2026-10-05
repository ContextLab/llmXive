import os
import sys
import logging
import json
import time
import random
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.preprocessing import StandardScaler
from scipy.stats import variance_of_the_mean
import joblib
from utils.logging import get_logger, log_memory_usage
from utils.resource_guard import check_cpu_only, enforce_resource_limits

# Ensure imports from sibling modules work correctly in the project context
# Assuming the script is run from the 'code' directory or PYTHONPATH is set
try:
    from utils.logging import setup_logging
except ImportError:
    pass

logger = get_logger(__name__)

def load_preprocessed_data():
    """Load the rarefied and preprocessed data."""
    data_path = Path("data/processed/rarefied_genus_table.parquet")
    if not data_path.exists():
        raise FileNotFoundError(f"Preprocessed data not found at {data_path}")
    df = pd.read_parquet(data_path)
    return df

def prepare_features_target(df):
    """Separate features (genera) and target (cognitive score)."""
    # Assuming 'cognitive_score' is the target column and others are genera
    target_col = 'cognitive_score'
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data.")
    
    X = df.drop(columns=[target_col])
    y = df[target_col]
    return X, y

def nested_cv_random_forest(X, y, n_outer_folds=5, n_inner_folds=3, random_state=42):
    """
    Perform nested cross-validation for Random Forest.
    Outer loop: evaluation
    Inner loop: hyperparameter tuning
    """
    check_cpu_only()
    logger.info("Starting Nested Cross-Validation for Random Forest")
    
    # Hyperparameter grid
    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [5, 10, None],
        'min_samples_split': [2, 5]
    }
    
    outer_cv = StratifiedKFold(n_splits=n_outer_folds, shuffle=True, random_state=random_state)
    inner_cv = StratifiedKFold(n_splits=n_inner_folds, shuffle=True, random_state=random_state)
    
    outer_scores = []
    best_models = []
    
    for train_idx, test_idx in outer_cv.split(X, y):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Scale features if necessary (RF doesn't strictly need it, but good practice)
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        rf = RandomForestRegressor(random_state=random_state)
        
        # Inner loop: Grid Search
        grid_search = GridSearchCV(
            rf, param_grid, cv=inner_cv, scoring='r2', n_jobs=-1
        )
        grid_search.fit(X_train_scaled, y_train)
        
        best_model = grid_search.best_estimator_
        best_models.append(best_model)
        
        # Outer loop evaluation
        y_pred = best_model.predict(X_test_scaled)
        r2 = r2_score(y_test, y_pred)
        outer_scores.append(r2)
        logger.info(f"Outer Fold R2: {r2:.4f}")
        
        # Memory check
        log_memory_usage()
        if not enforce_resource_limits():
            raise RuntimeError("Resource limit exceeded during nested CV.")
    
    mean_r2 = np.mean(outer_scores)
    std_r2 = np.std(outer_scores)
    logger.info(f"Nested CV Mean R2: {mean_r2:.4f} (+/- {std_r2:.4f})")
    
    return mean_r2, std_r2, best_models

def run_permutation_test(X, y, best_models, n_permutations=1000, random_state=42):
    """
    Run permutation test to generate null distribution of R2 scores.
    """
    logger.info(f"Starting Permutation Test with {n_permutations} shuffles")
    null_scores = []
    
    # Use the best model from the last fold or retrain a single model for speed if needed
    # For robustness, we use the structure of the last best_model
    model_template = best_models[-1]
    
    for i in range(n_permutations):
        log_memory_usage()
        if not enforce_resource_limits():
            logger.warning("Approaching memory limit during permutation test.")
            # Optionally reduce n_permutations or sample features
            break
        
        # Shuffle y
        y_shuffled = y.sample(frac=1, random_state=random_state + i).reset_index(drop=True)
        
        # Simple train/test split for permutation (using full data to estimate null distribution)
        # Or use a single CV fold for speed if n_permutations is high
        # Here we use a single split for efficiency in the null distribution generation
        from sklearn.model_selection import train_test_split
        X_tr, X_te, y_tr, y_te = train_test_split(X, y_shuffled, test_size=0.2, random_state=random_state + i)
        
        # Retrain model with best params found in CV (simplified for null distribution)
        rf_perm = RandomForestRegressor(
            n_estimators=model_template.n_estimators,
            max_depth=model_template.max_depth,
            min_samples_split=model_template.min_samples_split,
            random_state=random_state
        )
        rf_perm.fit(X_tr, y_tr)
        y_pred_perm = rf_perm.predict(X_te)
        r2_perm = r2_score(y_te, y_pred_perm)
        null_scores.append(r2_perm)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Permutation {i+1}/{n_permutations} completed")
    
    null_threshold = np.percentile(null_scores, 95)
    logger.info(f"95th Percentile Null Threshold: {null_threshold:.4f}")
    
    return null_scores, null_threshold

def identify_top_taxa(best_models, X, top_n=10):
    """Identify top predictive taxa based on feature importance."""
    # Aggregate feature importance from the best models
    # Assuming all models have the same structure
    feature_importances = np.zeros(X.shape[1])
    for model in best_models:
        feature_importances += model.feature_importances_
    feature_importances /= len(best_models)
    
    top_indices = np.argsort(feature_importances)[::-1][:top_n]
    top_taxa = X.columns[top_indices].tolist()
    top_importances = feature_importances[top_indices].tolist()
    
    logger.info(f"Top {top_n} taxa identified: {top_taxa}")
    return top_taxa, top_importances

def calculate_vif(X, taxa_list):
    """Calculate Variance Inflation Factor for top taxa."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    X_subset = X[taxa_list]
    vif_data = []
    for i, col in enumerate(X_subset.columns):
        vif = variance_inflation_factor(X_subset.values, i)
        vif_data.append({"taxon": col, "vif": vif})
        if vif > 5:
            logger.warning(f"High collinearity detected for {col}: VIF = {vif}")
    
    return vif_data

def calculate_shap_values(best_models, X):
    """Calculate SHAP values for interpretability."""
    try:
        import shap
        logger.info("Calculating SHAP values...")
        # Use the first best model
        explainer = shap.TreeExplainer(best_models[0])
        shap_values = explainer.shap_values(X)
        return shap_values
    except ImportError:
        logger.warning("SHAP library not installed. Skipping SHAP calculation.")
        return None

def save_results(mean_r2, std_r2, null_threshold, top_taxa, vif_data, shap_values=None):
    """Save all results to data/processed/ and data/models/."""
    results_dir = Path("data/processed")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Save significance
    significance_data = {
        "mean_r2": mean_r2,
        "std_r2": std_r2,
        "null_threshold_95": null_threshold,
        "is_significant": mean_r2 > null_threshold
    }
    with open(results_dir / "model_significance.json", "w") as f:
        json.dump(significance_data, f, indent=2)
    
    # Save top taxa
    with open(results_dir / "top_taxa.json", "w") as f:
        json.dump({"taxa": top_taxa}, f, indent=2)
    
    # Save collinearity review
    with open(results_dir / "collinearity_review_log.json", "w") as f:
        json.dump(vif_data, f, indent=2)
    
    # Save models
    models_dir = Path("data/models")
    models_dir.mkdir(parents=True, exist_ok=True)
    for i, model in enumerate(best_models):
        joblib.dump(model, models_dir / f"rf_model_fold_{i}.joblib")
    
    logger.info("Results saved successfully.")

def run_modeling_pipeline():
    """Run the full predictive modeling pipeline."""
    logger.info("Starting Predictive Modeling Pipeline")
    
    # Load data
    df = load_preprocessed_data()
    X, y = prepare_features_target(df)
    
    # Nested CV
    mean_r2, std_r2, best_models = nested_cv_random_forest(X, y)
    
    # Permutation test
    null_scores, null_threshold = run_permutation_test(X, y, best_models)
    
    # Identify top taxa
    top_taxa, top_importances = identify_top_taxa(best_models, X)
    
    # VIF
    vif_data = calculate_vif(X, top_taxa)
    
    # SHAP
    shap_values = calculate_shap_values(best_models, X)
    
    # Save results
    save_results(mean_r2, std_r2, null_threshold, top_taxa, vif_data, shap_values)
    
    logger.info("Pipeline completed.")

def main():
    setup_logging()
    run_modeling_pipeline()

if __name__ == "__main__":
    main()
