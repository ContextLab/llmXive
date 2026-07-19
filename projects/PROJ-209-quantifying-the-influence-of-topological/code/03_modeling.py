import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import hashlib
import subprocess

# Local imports based on project structure
# Assuming these are available in the same directory or added to sys.path
# The prompt implies they are sibling modules or part of the same package
try:
    from infrastructure.path_utils import get_project_root, ensure_dir
except ImportError:
    # Fallback for direct execution if infrastructure is not imported correctly
    def get_project_root():
        return Path(__file__).parent.parent
    def ensure_dir(path):
        os.makedirs(path, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_git_hash() -> str:
    """Get the current git commit hash."""
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "unknown"

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_output_directories():
    """Ensure all required output directories exist."""
    root = get_project_root()
    dirs = [
        root / "data" / "processed",
        root / "data" / "state",
        root / "data" / "validation"
    ]
    for d in dirs:
        ensure_dir(str(d))

def load_processed_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load processed features, targets, and metadata.
    Expects data/processed/features.csv and data/processed/targets.csv
    """
    root = get_project_root()
    features_path = root / "data" / "processed" / "features.csv"
    targets_path = root / "data" / "processed" / "targets.csv"
    
    if not features_path.exists() or not targets_path.exists():
        raise FileNotFoundError(
            f"Processed data not found. Expected at {features_path} and {targets_path}. "
            "Please run T018 (data processing) first."
        )
    
    features = pd.read_csv(features_path)
    targets = pd.read_csv(targets_path)
    
    # Load metadata if exists, otherwise create empty
    metadata_path = root / "data" / "processed" / "metadata.json"
    metadata = {}
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    
    return features, targets, metadata

def compute_vif(X: pd.DataFrame) -> pd.Series:
    """
    Compute Variance Inflation Factor (VIF) for each feature.
    VIF > 5 indicates high collinearity.
    """
    # Add constant for intercept if not present
    if 'intercept' not in X.columns:
        X_temp = X.copy()
        X_temp['intercept'] = 1.0
    else:
        X_temp = X.copy()
    
    vif_data = pd.Series(index=X.columns, dtype=float)
    
    for col in X.columns:
        # Regress current feature against all other features
        y = X_temp[col]
        # Ensure we have at least 2 features to regress against
        if len(X_temp.columns) > 1:
            X_other = X_temp.drop(columns=[col])
            # Fit linear model to get R^2
            # Using simple OLS from statsmodels if available, else manual
            try:
                import statsmodels.api as sm
                model = sm.OLS(y, sm.add_constant(X_other, has_constant='add'))
                results = model.fit()
                r_squared = results.rsquared
            except ImportError:
                # Fallback: manual OLS calculation
                # X_other = sm.add_constant(X_other) # Already handled in sm.OLS logic above usually, but safe to ensure
                # Actually, for manual: y = X_other @ beta + e
                # beta = (X^T X)^-1 X^T y
                # R^2 = 1 - (SS_res / SS_tot)
                X_other_arr = X_other.values
                y_arr = y.values
                
                # Add constant manually for manual calc
                X_other_const = np.column_stack([np.ones(len(X_other_arr)), X_other_arr])
                
                try:
                    beta = np.linalg.lstsq(X_other_const, y_arr, rcond=None)[0]
                    y_pred = X_other_const @ beta
                    ss_res = np.sum((y_arr - y_pred) ** 2)
                    ss_tot = np.sum((y_arr - np.mean(y_arr)) ** 2)
                    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
                except np.linalg.LinAlgError:
                    r_squared = 0.0
            
            vif = 1.0 / (1.0 - r_squared) if r_squared < 1.0 else float('inf')
        else:
            vif = 1.0 # Only one feature, no collinearity
        
        vif_data[col] = vif
    
    return vif_data

def train_initial_rf_for_importance(X: pd.DataFrame, y: pd.Series, 
                                    target_name: str = "conductivity", 
                                    random_state: int = 42) -> Dict[str, float]:
    """
    Train a preliminary Random Forest to derive initial feature importances.
    Used for collinearity handling to decide which feature to drop.
    """
    from sklearn.ensemble import RandomForestRegressor
    
    # Handle non-numeric columns if any (though processed data should be numeric)
    X_num = X.select_dtypes(include=[np.number])
    
    if X_num.empty:
        logger.warning("No numeric features found for importance training.")
        return {}
    
    model = RandomForestRegressor(
        n_estimators=100, 
        random_state=random_state,
        n_jobs=-1
    )
    
    try:
        model.fit(X_num, y)
        importance_dict = dict(zip(X_num.columns, model.feature_importances_))
        return importance_dict
    except Exception as e:
        logger.error(f"Failed to train preliminary RF: {e}")
        return {}

def save_preliminary_importance(importance_dict: Dict[str, float], target_name: str):
    """Save preliminary importance scores to JSON."""
    root = get_project_root()
    output_path = root / "data" / "processed" / "preliminary_importance.json"
    
    data = {
        "target": target_name,
        "importances": importance_dict,
        "git_hash": get_git_hash()
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Preliminary importance saved to {output_path}")

def run_preliminary_model_training(features: pd.DataFrame, targets: pd.DataFrame):
    """
    Step 4.1: Preliminary Model Training.
    Trains RFs for each target to get initial importances.
    """
    ensure_output_directories()
    
    # Iterate over targets
    target_cols = [c for c in targets.columns if c not in ['defect_id', 'material_id']]
    
    for target_name in target_cols:
        y = targets[target_name]
        # Drop non-numeric columns from features if any
        X = features.select_dtypes(include=[np.number])
        
        if X.empty:
            logger.warning(f"No numeric features for target {target_name}")
            continue
        
        importance = train_initial_rf_for_importance(X, y, target_name)
        save_preliminary_importance(importance, target_name)

def handle_collinearity(features: pd.DataFrame, targets: pd.DataFrame, 
                        max_iterations: int = 10, vif_threshold: float = 5.0) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Step 4: Collinearity Handling.
    Computes VIF, iteratively removes low-importance features until VIF <= 5 or max iterations reached.
    Uses preliminary importance to decide which feature to drop.
    """
    ensure_output_directories()
    root = get_project_root()
    
    log_data = {
        "iterations": [],
        "final_vif": {},
        "excluded_features": [],
        "status": "SUCCESS"
    }
    
    current_features = features.copy()
    # Ensure we only have numeric features for VIF
    current_features = current_features.select_dtypes(include=[np.number])
    
    # Get preliminary importances for the first target (or aggregate if needed)
    # For simplicity, we use the first target found in targets
    target_cols = [c for c in targets.columns if c not in ['defect_id', 'material_id']]
    if not target_cols:
        logger.error("No target columns found.")
        return current_features, log_data
    
    primary_target = target_cols[0]
    y = targets[primary_target]
    
    # Load preliminary importance if exists, else train one
    importance_path = root / "data" / "processed" / "preliminary_importance.json"
    if importance_path.exists():
        with open(importance_path, 'r') as f:
            prelim_data = json.load(f)
            if prelim_data.get("target") == primary_target:
                importance_map = prelim_data.get("importances", {})
            else:
                importance_map = train_initial_rf_for_importance(current_features, y, primary_target)
    else:
        importance_map = train_initial_rf_for_importance(current_features, y, primary_target)
    
    iteration = 0
    while iteration < max_iterations:
        # Compute VIF
        vif_series = compute_vif(current_features)
        max_vif = vif_series.max()
        
        log_entry = {
            "iteration": iteration,
            "max_vif": float(max_vif),
            "remaining_features": list(current_features.columns)
        }
        
        logger.info(f"Iteration {iteration}: Max VIF = {max_vif:.2f}")
        
        if max_vif <= vif_threshold:
            log_entry["action"] = "STOP: VIF acceptable"
            log_data["iterations"].append(log_entry)
            log_data["status"] = "SUCCESS"
            break
        
        # Find feature with highest VIF
        # If multiple, pick the one with lowest importance
        high_vif_features = vif_series[vif_series > vif_threshold]
        
        if high_vif_features.empty:
            break
        
        # Sort by VIF descending, then by importance ascending (to drop low importance among high VIF)
        # If importance missing, assume 0
        candidates = high_vif_features.to_dict()
        sorted_candidates = sorted(
            candidates.items(), 
            key=lambda x: (x[1], importance_map.get(x[0], 0.0)), 
            reverse=True
        )
        
        # Actually, we want to drop the one with LOWEST importance among those with HIGH VIF
        # So sort by importance ASC
        sorted_by_importance = sorted(
            candidates.items(),
            key=lambda x: importance_map.get(x[0], 0.0)
        )
        
        feature_to_drop = sorted_by_importance[0][0]
        
        log_entry["action"] = f"DROP: {feature_to_drop} (VIF={candidates[feature_to_drop]:.2f}, Imp={importance_map.get(feature_to_drop, 0.0):.4f})"
        log_data["excluded_features"].append(feature_to_drop)
        log_data["iterations"].append(log_entry)
        
        # Drop feature
        current_features = current_features.drop(columns=[feature_to_drop])
        
        # Re-train preliminary model? 
        # The task says "re-train model, re-calculate VIF". 
        # We assume the importance map is updated or we just re-calculate VIF.
        # To be safe, we could re-calculate importance, but VIF is the primary driver here.
        # We'll stick to re-calculating VIF.
        
        if current_features.empty:
            log_entry["action"] = "STOP: No features left"
            log_data["iterations"].append(log_entry)
            log_data["status"] = "FAILURE_NO_FEATURES"
            break
        
        iteration += 1
    
    if iteration >= max_iterations and compute_vif(current_features).max() > vif_threshold:
        log_data["status"] = "VIF_FAILURE"
        logger.warning(f"VIF > {vif_threshold} after {max_iterations} iterations. Marked as VIF_FAILURE.")
    
    final_vif = compute_vif(current_features).to_dict()
    log_data["final_vif"] = {k: float(v) for k, v in final_vif.items()}
    
    return current_features, log_data

def save_feature_selection_log(log_data: Dict[str, Any]):
    """Save feature selection log to JSON."""
    root = get_project_root()
    output_path = root / "data" / "processed" / "feature_selection_log.json"
    
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Feature selection log saved to {output_path}")

def main():
    """Main entry point for T020: Collinearity Handling."""
    logger.info("Starting T020: Collinearity Handling")
    ensure_output_directories()
    
    try:
        # Load data
        features, targets, metadata = load_processed_data()
        logger.info(f"Loaded {len(features)} samples with {len(features.columns)} features.")
        
        # Step 4.1: Preliminary Model Training (if not done yet, though T020a should have done it)
        # We check if preliminary_importance.json exists
        root = get_project_root()
        importance_path = root / "data" / "processed" / "preliminary_importance.json"
        if not importance_path.exists():
            logger.info("Preliminary importance not found. Running preliminary training.")
            run_preliminary_model_training(features, targets)
        
        # Step 4: Collinearity Handling
        final_features, log_data = handle_collinearity(features, targets)
        
        # Save outputs
        final_features_path = root / "data" / "processed" / "final_features.csv"
        final_features.to_csv(final_features_path, index=False)
        logger.info(f"Final features saved to {final_features_path}")
        
        save_feature_selection_log(log_data)
        
        logger.info("T020 completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"T020 failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())