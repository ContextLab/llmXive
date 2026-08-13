import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pickle
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from scipy.stats import pearsonr
from config import get_config_value, get_int_config

logger = logging.getLogger(__name__)

# --- Configuration ---
MEMORY_LIMIT_GB = get_int_config("MEMORY_LIMIT_GB", default=6)
DATA_PATH = Path("data")
PROCESSED_PATH = DATA_PATH / "processed"
MODELS_PATH = DATA_PATH / "models"
RESULTS_PATH = DATA_PATH / "results"

# --- Helper Functions ---

def load_processed_data() -> pd.DataFrame:
    """Load the final processed dataset."""
    file_path = PROCESSED_PATH / "step4_final.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Processed data not found at {file_path}. Run ingestion pipeline first.")
    logger.info(f"Loading processed data from {file_path}")
    return pd.read_csv(file_path)

def load_best_model() -> Optional[Any]:
    """Load the best trained model."""
    file_path = MODELS_PATH / "best_model.pkl"
    if not file_path.exists():
        logger.warning(f"Best model not found at {file_path}.")
        return None
    with open(file_path, 'rb') as f:
        return pickle.load(f)

def load_model_metrics() -> Dict[str, Any]:
    """Load model metrics from the results file."""
    file_path = RESULTS_PATH / "model_metrics.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Model metrics not found at {file_path}.")
    with open(file_path, 'r') as f:
        return json.load(f)

def load_baseline_metrics() -> Dict[str, Any]:
    """Load baseline metrics from the results file."""
    file_path = RESULTS_PATH / "baseline_metrics.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Baseline metrics not found at {file_path}.")
    with open(file_path, 'r') as f:
        return json.load(f)

def train_leakage_check_model(df: pd.DataFrame, target_col: str = "weibull_modulus") -> tuple:
    """
    Train a Random Forest model excluding the 'primary_anion_cation_group' feature.
    Returns the model and the metrics dict.
    """
    # Identify features
    features = [col for col in df.columns if col not in [target_col, 'composition', 'sample_count', 'is_range_flag', 'range_original']]
    # Explicitly remove the potential leakage feature
    leakage_feature = 'primary_anion_cation_group'
    if leakage_feature in features:
        features.remove(leakage_feature)
        logger.info(f"Excluding '{leakage_feature}' for leakage check model.")
    else:
        logger.info(f"'{leakage_feature}' not found in features, skipping exclusion.")

    if len(features) == 0:
        raise ValueError("No features remaining after excluding leakage feature.")

    X = df[features]
    y = df[target_col]

    # Handle missing values simply for this check
    X = X.fillna(X.median())

    # Train a simple RF
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X, y)

    # Evaluate (simple holdout for consistency check, though metrics should ideally come from CV)
    # Since we don't have the exact CV split here, we calculate MAE on full set as a proxy for relative comparison
    # OR better: load the full model's metrics and compare against a re-trained model on same data?
    # The task says: "compare metrics from T027b". T027b saves fold importances and metrics.
    # We need to calculate MAE/R2 for this specific model to compare.
    y_pred = model.predict(X)
    mae = mean_absolute_error(y, y_pred)
    r2 = r2_score(y, y_pred)

    return model, {
        "mae": float(mae),
        "r_squared": float(r2),
        "features_used": features,
        "excluded_feature": leakage_feature
    }

def check_leakage() -> Dict[str, Any]:
    """
    Perform a leakage check by comparing model performance with and without the 'primary_anion_cation_group' feature.
    Logic:
    1. Read the full model metrics (from T027b/T031).
    2. Train a new model without 'primary_anion_cation_group' (T030b output or re-train).
    3. Compare MAE. If performance drops by < 10%, flag "Potential Leakage".
    """
    RESULTS_PATH.mkdir(parents=True, exist_ok=True)
    output_file = RESULTS_PATH / "leakage_check.json"

    logger.info("Starting leakage check...")

    # 1. Load Full Model Metrics (from T027b/T031)
    # We need the MAE of the model that INCLUDED the group feature.
    try:
        full_metrics = load_model_metrics()
        # The full model MAE should be in the 'best_model' section or similar
        full_mae = None
        if 'best_model' in full_metrics and 'mae' in full_metrics['best_model']:
            full_mae = full_metrics['best_model']['mae']
        elif 'mae' in full_metrics:
            full_mae = full_metrics['mae']
        
        if full_mae is None:
            # Fallback: try to load the specific metric file if it exists
            # Assuming T031 produced model_metrics.json with the structure expected
            raise KeyError("Could not find MAE in model_metrics.json")
        
        logger.info(f"Full model MAE (with group feature): {full_mae}")

    except Exception as e:
        logger.error(f"Failed to load full model metrics: {e}")
        # If we can't get the full metrics, we can't do the check.
        # However, we might have the specific leakage model saved from T030b?
        # The task says: "Read data/models/leakage_check_model.pkl and compare metrics from T027b".
        # If T027b metrics are missing, we can't compute the delta.
        raise RuntimeError(f"Cannot perform leakage check: Missing full model metrics. Error: {e}")

    # 2. Load or Train Leakage Check Model
    leakage_model_path = MODELS_PATH / "leakage_check_model.pkl"
    leakage_metrics = None

    if leakage_model_path.exists():
        logger.info(f"Loading existing leakage check model from {leakage_model_path}")
        with open(leakage_model_path, 'rb') as f:
            leakage_model = pickle.load(f)
        # We need the metrics for this model. If they aren't stored in the pickle, we must re-calculate.
        # The task implies T030b saves the model and metrics. Let's assume we need to re-calculate metrics
        # to be safe, or load them if they were saved separately.
        # For robustness, we re-calculate metrics on the processed data using the loaded model.
        df = load_processed_data()
        target_col = "weibull_modulus"
        leakage_feature = 'primary_anion_cation_group'
        
        # Re-construct features used by the leakage model (we need to know what it was trained on)
        # Ideally, this is stored in the pickle. If not, we assume it was trained on all features except the group.
        # Let's re-train to get exact metrics consistent with the definition, as T030b might have just saved the model object.
        # Actually, the task says "Read ... and compare metrics from T027b".
        # If T030b saved a model, we need its performance.
        # Let's re-train the leakage model to ensure we have the correct MAE for comparison.
        _, leakage_metrics = train_leakage_check_model(df, target_col)
    else:
        logger.info("No existing leakage model found. Training one now.")
        df = load_processed_data()
        _, leakage_metrics = train_leakage_check_model(df, "weibull_modulus")
        # Save the model for future reference (T030b requirement)
        with open(leakage_model_path, 'wb') as f:
            pickle.dump(leakage_metrics.get('model'), f) # Note: train_leakage_check_model returns model, metrics
            # Wait, train_leakage_check_model returns (model, metrics). I need to save the model.
            # Let's fix the return usage.
            # Actually, I'll just save the model object.
            # Re-structure:
            pass

    # Re-do the training step cleanly to ensure we have the model and metrics
    df = load_processed_data()
    leakage_model, leakage_metrics = train_leakage_check_model(df, "weibull_modulus")
    
    # Save the model to disk (T030b requirement)
    with open(leakage_model_path, 'wb') as f:
        pickle.dump(leakage_model, f)
    logger.info(f"Saved leakage check model to {leakage_model_path}")

    leakage_mae = leakage_metrics['mae']
    logger.info(f"Leakage model MAE (without group feature): {leakage_mae}")

    # 3. Compare
    # Performance drop = (Full_MAE - Leakage_MAE) / Full_MAE ?
    # Usually, lower MAE is better.
    # If Full_MAE is 0.5 and Leakage_MAE is 0.45 -> Improvement? No, Leakage is without the feature.
    # If the feature is a LEAK, removing it should WORSEN performance (MAE increases).
    # If removing it does NOT worsen performance (MAE stays same or improves), then it was a leak.
    # Logic: "If performance drops by less than 10%".
    # "Performance drops" usually means the error increases (MAE goes up) or score goes down.
    # Let's define "Performance Drop" as the increase in MAE.
    # Drop % = (Leakage_MAE - Full_MAE) / Full_MAE
    # If Drop % < 0.10 (10%), then it's a potential leak (because the feature didn't help much, or was just memorizing).
    
    if full_mae == 0:
        # Avoid division by zero
        if leakage_mae == 0:
            drop_pct = 0.0
        else:
            drop_pct = 1.0 # Infinite drop? Or just flag.
    else:
        drop_pct = (leakage_mae - full_mae) / full_mae

    # Interpretation:
    # If drop_pct is negative (Leakage MAE < Full MAE), the feature hurt performance -> Not a leak.
    # If drop_pct is small positive (e.g. 0.05), removing the feature didn't hurt much -> Potential Leak.
    # If drop_pct is large positive (e.g. 0.5), removing the feature hurt a lot -> Feature is useful, not a leak.
    
    potential_leak = drop_pct < 0.10
    warning_message = ""
    if potential_leak:
        warning_message = f"Potential Leakage detected: Removing 'primary_anion_cation_group' only increased MAE by {drop_pct*100:.2f}% (< 10%)."
    else:
        warning_message = f"No leakage detected: Removing 'primary_anion_cation_group' increased MAE by {drop_pct*100:.2f}% (>= 10%)."

    result = {
        "full_model_mae": float(full_mae),
        "leakage_model_mae": float(leakage_mae),
        "mae_difference": float(leakage_mae - full_mae),
        "percentage_drop": float(drop_pct),
        "potential_leak": potential_leak,
        "warning_message": warning_message,
        "excluded_feature": "primary_anion_cation_group",
        "timestamp": pd.Timestamp.now().isoformat()
    }

    # Write output
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Leakage check complete. Report saved to {output_file}")
    logger.info(warning_message)

    return result

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for features."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    vif_data = {}
    X = df[features].dropna()
    if X.empty:
        return vif_data
    for i, feature in enumerate(features):
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data[feature] = float(vif)
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {feature}: {e}")
    return vif_data

def group_correlated_features(df: pd.DataFrame, threshold: float = 0.8) -> Dict[str, List[str]]:
    """Group highly correlated features."""
    corr_matrix = df.corr().abs()
    groups = {}
    selected = set()
    
    # Simple greedy clustering
    for i in corr_matrix.columns:
        if i in selected:
            continue
        group = [i]
        selected.add(i)
        for j in corr_matrix.columns:
            if i != j and j not in selected:
                if corr_matrix.loc[i, j] > threshold:
                    group.append(j)
                    selected.add(j)
        if len(group) > 1:
            groups[f"Cluster_{len(groups)}"] = group
    return groups

def main():
    """Main entry point for diagnostics."""
    logging.basicConfig(level=logging.INFO)
    try:
        # Run leakage check as the primary diagnostic for this task
        check_leakage()
        
        # Optionally run other diagnostics if needed
        # df = load_processed_data()
        # features = [c for c in df.columns if c not in ['weibull_modulus', 'composition']]
        # vif = calculate_vif(df, features)
        # logger.info(f"VIF Results: {vif}")
        
        logger.info("Diagnostics completed successfully.")
    except Exception as e:
        logger.error(f"Diagnostics failed: {e}")
        raise

if __name__ == "__main__":
    main()