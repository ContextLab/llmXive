"""
code/03_modeling.py
Implements Random Forest modeling pipeline for 2D material properties.
Handles feature selection, model training, and cross-validation.
"""
import os
import json
import logging
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import pickle
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import r2_score, mean_absolute_percentage_error
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import shared utilities from existing API surface
# Note: Assuming these are available in the project root or code/ as per spec
# If specific imports fail, they should be added to 02_data_processing or path_utils
try:
    from code.infrastructure.path_utils import get_project_root, ensure_dir
except ImportError:
    # Fallback if path_utils is not yet imported or structured differently
    from pathlib import Path
    def get_project_root():
        return Path(__file__).resolve().parent.parent
    def ensure_dir(p):
        os.makedirs(p, exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SEED = 42
VIF_THRESHOLD = 5.0
MAX_ITERATIONS = 10

def load_json_file(path: str) -> Dict:
    with open(path, 'r') as f:
        return json.load(f)

def save_json_file(path: str, data: Dict) -> None:
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_csv_to_dicts(path: str) -> List[Dict]:
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_to_csv(data: List[Dict], path: str) -> None:
    if not data:
        # Write empty file with headers if needed, or just return
        return
    fieldnames = data[0].keys()
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def compute_vif(X: pd.DataFrame) -> pd.Series:
    """Compute Variance Inflation Factor for each feature."""
    vif_data = pd.Series()
    try:
        # Add constant for intercept if not present (statsmodels usually requires it, but VIF calculation often omits it for the matrix)
        # Standard VIF calculation: VIF_i = 1 / (1 - R_i^2) where R_i^2 is from regressing X_i on all other X_j
        # We use the matrix approach
        vif = pd.DataFrame()
        vif["VIF Factor"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
        vif["features"] = X.columns
        return vif.set_index("features")["VIF Factor"]
    except Exception as e:
        logger.error(f"VIF calculation failed: {e}")
        return pd.Series()

def train_initial_rf_for_importance(X: pd.DataFrame, y: pd.Series, n_estimators: int = 50) -> RandomForestRegressor:
    """Train a preliminary Random Forest for feature importance."""
    rf = RandomForestRegressor(n_estimators=n_estimators, random_state=SEED, n_jobs=-1)
    rf.fit(X, y)
    return rf

def save_preliminary_importance(model: RandomForestRegressor, feature_names: List[str], path: str) -> None:
    """Save preliminary model and importance scores."""
    importance_scores = model.feature_importances_
    data = {
        "feature": feature_names,
        "importance": importance_scores.tolist()
    }
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    # Also save the model itself for later use if needed
    with open(path.replace(".csv", "_model.pkl"), "wb") as f:
        pickle.dump(model, f)

def run_preliminary_model_training(features_path: str, targets_path: str, output_path: str) -> None:
    """Step 1 of US2: Preliminary Training for Feature Selection (T021a logic)."""
    logger.info(f"Loading data for preliminary training from {features_path} and {targets_path}")
    if not os.path.exists(features_path) or not os.path.exists(targets_path):
        raise FileNotFoundError("Required processed data files not found for preliminary training.")

    features_df = pd.read_csv(features_path)
    targets_df = pd.read_csv(targets_path)

    # Ensure alignment
    common_ids = set(features_df['id']) & set(targets_df['id'])
    features_df = features_df[features_df['id'].isin(common_ids)]
    targets_df = targets_df[targets_df['id'].isin(common_ids)]
    
    # Sort by ID to ensure alignment
    features_df = features_df.sort_values('id')
    targets_df = targets_df.sort_values('id')

    X = features_df.drop(columns=['id'])
    y = targets_df['target'] # Assuming target column name is 'target' or similar, adjust if needed

    model = train_initial_rf_for_importance(X, y)
    save_preliminary_importance(model, list(X.columns), output_path)
    logger.info(f"Preliminary model saved to {output_path}")

def handle_collinearity(features_path: str, output_path: str, log_path: str) -> Tuple[pd.DataFrame, Dict]:
    """
    Step 2 of US2: Feature Selection Logic (T020 logic).
    Iteratively remove features with lowest importance until VIF < threshold or max iterations.
    """
    logger.info(f"Starting collinearity handling on {features_path}")
    
    # Load initial features
    df = pd.read_csv(features_path)
    feature_cols = [c for c in df.columns if c != 'id']
    
    log_data = {
        "iterations": [],
        "final_vif": 0.0,
        "removed_features": []
    }

    iteration = 0
    current_vif = float('inf')
    
    # We need a model to get importance. If T021a ran, we might load it, but T020 logic implies
    # we might need to re-train or use the preliminary one. The task says "Load preliminary_model.pkl".
    # For this implementation, we will re-train a quick model on the current set if needed, 
    # or load the one saved by T021a if it exists and matches features.
    # To be safe and self-contained for T020 execution:
    # We assume the preliminary model was saved to 'data/processed/preliminary_model.pkl' by T021a.
    
    model_path = os.path.join(os.path.dirname(features_path), "preliminary_model.pkl")
    model = None
    if os.path.exists(model_path):
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        logger.info("Loaded preliminary model for importance.")
    
    while current_vif > VIF_THRESHOLD and iteration < MAX_ITERATIONS:
        iteration += 1
        logger.info(f"Iteration {iteration}: Current VIF = {current_vif}")
        
        # Prepare X for current features
        X_current = df[feature_cols]
        y_current = pd.read_csv(os.path.join(os.path.dirname(features_path), "targets.csv"))['target']
        
        # Calculate VIF
        vif_series = compute_vif(X_current)
        current_vif = vif_series.max() if not vif_series.empty else 0.0
        
        if current_vif <= VIF_THRESHOLD:
            break

        # If no model loaded (or features mismatch), train a quick one
        if model is None or not all(c in model.feature_names_in_ for c in feature_cols):
            model = train_initial_rf_for_importance(X_current, y_current, n_estimators=10)
        
        # Get importance for current features
        # Map model importance to current feature columns
        # Note: model.feature_names_in_ should match X_current columns if trained on same
        try:
            importance = dict(zip(model.feature_names_in_, model.feature_importances_))
        except Exception:
            # Fallback if feature names don't match perfectly (shouldn't happen if logic is correct)
            importance = {c: 0.0 for c in feature_cols}

        # Find feature with lowest importance
        lowest_feat = min(importance, key=importance.get)
        
        log_entry = {
            "iteration": iteration,
            "removed_feature": lowest_feat,
            "importance_score": importance[lowest_feat],
            "current_vif": current_vif
        }
        log_data["iterations"].append(log_entry)
        log_data["removed_features"].append(lowest_feat)
        
        logger.info(f"Removing feature: {lowest_feat} (VIF: {current_vif:.2f})")
        
        # Remove feature
        feature_cols.remove(lowest_feat)
        df = df.drop(columns=[lowest_feat])
        
        # Re-calculate VIF for next check
        if feature_cols:
            vif_series = compute_vif(df[feature_cols])
            current_vif = vif_series.max() if not vif_series.empty else 0.0
        else:
            current_vif = 0.0

    if current_vif > VIF_THRESHOLD:
        log_data["status"] = "VIF_FAILURE"
        logger.warning("VIF still above threshold after max iterations.")
    else:
        log_data["status"] = "SUCCESS"
    
    # Save log
    save_json_file(log_path, log_data)
    
    # Save final features
    final_path = output_path
    df.to_csv(final_path, index=False)
    
    logger.info(f"Feature selection complete. Final VIF: {current_vif}. Saved to {final_path}")
    return df, log_data

def run_feature_selection_loop(features_path: str, output_path: str, log_path: str) -> None:
    """Wrapper to run T020 logic."""
    handle_collinearity(features_path, output_path, log_path)

def train_models_with_loop(features_path: str, targets_path: str, confounding_config_path: str, output_dir: str) -> Dict:
    """
    Step 3 of US2: Model Training & Loop (T021).
    - Read confounding config.
    - Train RFs for conductivity, Young's modulus, fracture strength.
    - Loop: If VIF > 5, re-trigger feature selection (T020) and re-train.
    """
    logger.info("Starting Model Training & Loop (T021)")
    
    # Load data
    features_df = pd.read_csv(features_path)
    targets_df = pd.read_csv(targets_path)
    
    # Load confounding config
    confounding_config = load_json_file(confounding_config_path)
    
    # Determine strategy
    stratify_by = confounding_config.get('stratify_by', None)
    covariates = confounding_config.get('covariates', [])
    
    # Prepare data
    # Assuming targets_df has columns for the three properties or a single 'target' column with a 'property_type'
    # Based on T018, targets.csv likely has 'target' and 'property_type' or separate columns.
    # Let's assume separate columns for simplicity as per standard practice if not specified:
    # If targets.csv has 'conductivity', 'youngs_modulus', 'fracture_strength'
    # If it has 'target' and 'property', we need to split.
    
    # Check structure
    if 'target' in targets_df.columns and 'property_type' in targets_df.columns:
        # Pivot to wide format
        targets_wide = targets_df.pivot(index='id', columns='property_type', values='target')
        # Reset index to merge with features
        targets_wide = targets_wide.reset_index()
    else:
        # Assume wide format already
        targets_wide = targets_df
    
    # Merge features and targets
    merged = pd.merge(features_df, targets_wide, on='id', how='inner')
    
    # Identify target columns
    target_properties = ['conductivity', 'youngs_modulus', 'fracture_strength']
    available_targets = [t for t in target_properties if t in merged.columns]
    
    if not available_targets:
        raise ValueError(f"None of the expected target properties found in {targets_path}. Columns: {merged.columns.tolist()}")
    
    feature_cols = [c for c in merged.columns if c not in ['id'] + available_targets]
    
    # Initial VIF check on ALL features
    X_initial = merged[feature_cols]
    initial_vif = compute_vif(X_initial).max()
    
    final_models = {}
    metrics = {}
    
    # Loop condition: If VIF > 5, re-trigger feature selection
    # Note: The task says "If VIF > 5 after initial training, re-trigger".
    # We interpret this as: Check VIF. If high, run feature selection, then train.
    # If after training (and selection), VIF is still high, we might loop again? 
    # The task says "re-trigger feature selection logic (T020) and re-train".
    # We'll do one pass of selection if VIF is high, then train.
    
    current_features = feature_cols
    current_vif = initial_vif
    
    if current_vif > VIF_THRESHOLD:
        logger.warning(f"Initial VIF ({current_vif:.2f}) > {VIF_THRESHOLD}. Triggering feature selection.")
        
        # Save current features to a temp file for T020 logic
        temp_features_path = os.path.join(output_dir, "temp_features_for_selection.csv")
        merged[feature_cols + ['id']].to_csv(temp_features_path, index=False)
        
        # Run T020 logic
        final_features_path = os.path.join(output_dir, "final_features_selected.csv")
        selection_log_path = os.path.join(output_dir, "feature_selection_log.json")
        
        run_feature_selection_loop(temp_features_path, final_features_path, selection_log_path)
        
        # Load selected features
        selected_df = pd.read_csv(final_features_path)
        selected_cols = [c for c in selected_df.columns if c != 'id']
        
        # Re-merge with targets
        merged = pd.merge(selected_df, targets_wide, on='id', how='inner')
        current_features = selected_cols
        current_vif = compute_vif(merged[current_features]).max()
        logger.info(f"After selection, VIF = {current_vif:.2f}")
    else:
        logger.info(f"Initial VIF ({current_vif:.2f}) <= {VIF_THRESHOLD}. Skipping feature selection.")
    
    # Train models
    X = merged[current_features]
    
    for prop in available_targets:
        y = merged[prop]
        
        # Handle stratification
        if stratify_by and stratify_by in merged.columns:
            # Ensure stratify column is categorical or has enough unique values
            if y.nunique() < 2:
                logger.warning(f"Target {prop} has < 2 unique values. Cannot stratify.")
                stratify = None
            else:
                stratify = merged[stratify_by]
        else:
            stratify = None
        
        # Train-test split
        if stratify is not None:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=SEED, stratify=stratify
            )
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=SEED
            )
        
        # Train RF
        model = RandomForestRegressor(n_estimators=100, random_state=SEED, n_jobs=-1)
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        mape = mean_absolute_percentage_error(y_test, y_pred)
        
        final_models[prop] = model
        metrics[prop] = {
            "R2": r2,
            "MAPE": mape,
            "train_size": len(y_train),
            "test_size": len(y_test)
        }
        
        logger.info(f"Model for {prop}: R2={r2:.4f}, MAPE={mape:.4f}")
    
    # Save models
    for prop, model in final_models.items():
        model_path = os.path.join(output_dir, f"rf_model_{prop}.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
    
    # Save metrics
    metrics_path = os.path.join(output_dir, "training_metrics.json")
    save_json_file(metrics_path, metrics)
    
    # Save final feature list used
    feature_list_path = os.path.join(output_dir, "final_feature_list.json")
    save_json_file(feature_list_path, {"features": current_features, "vif": float(current_vif)})
    
    return metrics

def main():
    """Main entry point for T021."""
    project_root = get_project_root()
    output_dir = os.path.join(project_root, "data", "processed")
    ensure_dir(output_dir)
    
    # Paths
    features_path = os.path.join(output_dir, "final_features.csv") # From T020
    targets_path = os.path.join(output_dir, "targets.csv")
    confounding_config_path = os.path.join(output_dir, "confounding_config.json")
    
    if not os.path.exists(confounding_config_path):
        # Fallback if T027a didn't run or path is different
        # Check common locations
        fallback_path = os.path.join(project_root, "data", "processed", "confounding_config.json")
        if os.path.exists(fallback_path):
            confounding_config_path = fallback_path
        else:
            raise FileNotFoundError(f"Confounding config not found at {confounding_config_path}")
    
    if not os.path.exists(features_path):
        # Check if T020 output is named differently or in a different location
        # T020 outputs 'data/processed/final_features.csv'
        pass # Error will be raised in training function
    
    try:
        metrics = train_models_with_loop(features_path, targets_path, confounding_config_path, output_dir)
        logger.info("T021 completed successfully.")
        logger.info(f"Metrics: {metrics}")
    except Exception as e:
        logger.error(f"T021 failed: {e}")
        raise

if __name__ == "__main__":
    main()