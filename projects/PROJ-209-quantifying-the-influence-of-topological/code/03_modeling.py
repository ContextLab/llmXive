import os
import json
import logging
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from scipy.stats import zscore

# Project root and config
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_project_root() -> Path:
    return PROJECT_ROOT

def ensure_output_directories() -> None:
    """Ensure all required output directories exist."""
    dirs = [
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "state",
        PROJECT_ROOT / "figures"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def load_json_file(path: Path) -> Dict:
    with open(path, 'r') as f:
        return json.load(f)

def save_json_file(path: Path, data: Dict) -> None:
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_csv_to_dicts(path: Path) -> List[Dict]:
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        return [row for row in reader]

def save_to_csv(path: Path, data: List[Dict], fieldnames: Optional[List[str]] = None) -> None:
    if not data:
        # Write empty file with headers if provided, or just create file
        with open(path, 'w') as f:
            if fieldnames:
                f.write(','.join(fieldnames) + '\n')
        return
    
    if not fieldnames:
        fieldnames = list(data[0].keys())
    
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def load_pandas_df(path: Path) -> pd.DataFrame:
    """Load a CSV into a pandas DataFrame."""
    return pd.read_csv(path)

def compute_vif(features: pd.DataFrame) -> Dict[str, float]:
    """Compute Variance Inflation Factor for each feature."""
    vif_data = {}
    for i, col in enumerate(features.columns):
        X = features[features.columns.drop(col)]
        y = features[col]
        try:
            r_squared = np.corrcoef(y, X.sum(axis=1))[0, 1] ** 2 if X.shape[1] == 1 else pd.DataFrame(X).apply(lambda x: np.corrcoef(x, y)[0,1], axis=0).mean() ** 2
            # Proper VIF calculation using OLS R2
            from sklearn.linear_model import LinearRegression
            model = LinearRegression().fit(X, y)
            r_squared = model.score(X, y)
            vif = 1 / (1 - r_squared) if (1 - r_squared) > 0 else float('inf')
        except:
            vif = float('inf')
        vif_data[col] = vif
    return vif_data

def train_initial_rf_for_importance(X: pd.DataFrame, y: pd.Series, random_state: int = 42) -> RandomForestRegressor:
    """Train a preliminary RF to estimate feature importance."""
    rf = RandomForestRegressor(n_estimators=100, random_state=random_state, n_jobs=-1)
    rf.fit(X, y)
    return rf

def save_preliminary_importance(path: Path, importance_dict: Dict[str, float]) -> None:
    """Save preliminary importance scores."""
    save_json_file(path, importance_dict)

def handle_collinearity(features: pd.DataFrame, threshold: float = 5.0, max_iterations: int = 10) -> tuple:
    """
    Handle collinearity by removing features with high VIF.
    Returns (remaining_features, log)
    """
    log = {
        "iterations": [],
        "status": "PENDING",
        "final_features": list(features.columns)
    }
    
    current_features = features.copy()
    iteration = 0
    
    while iteration < max_iterations:
        vif_scores = compute_vif(current_features)
        max_vif = max(vif_scores.values())
        max_vif_feature = max(vif_scores, key=vif_scores.get)
        
        iteration_log = {
            "iteration": iteration,
            "max_vif": max_vif,
            "max_vif_feature": max_vif_feature,
            "threshold": threshold
        }
        
        if max_vif <= threshold:
            log["status"] = "SUCCESS"
            break
        
        # Remove feature with highest VIF
        current_features = current_features.drop(columns=[max_vif_feature])
        iteration_log["action"] = "removed"
        
        log["iterations"].append(iteration_log)
        iteration += 1
        
        if iteration >= max_iterations:
            log["status"] = "VIF_FAILURE"
            log["message"] = "Max iterations reached, VIF still > threshold"
            break
    
    log["final_features"] = list(current_features.columns)
    return current_features, log

def run_feature_selection_loop(features_path: Path, output_path: Path, log_path: Path) -> List[str]:
    """Run the full feature selection loop and save results."""
    ensure_output_directories()
    
    df = load_pandas_df(features_path)
    # Assume all columns except 'id' or 'target' are features
    feature_cols = [c for c in df.columns if c not in ['id', 'target', 'defect_type']]
    if not feature_cols:
        # Fallback if schema differs
        feature_cols = [c for c in df.columns if c != 'target']
    
    features_df = df[feature_cols].dropna(axis=1) # Drop features with NaNs
    
    selected_features, log = handle_collinearity(features_df)
    
    save_json_file(log_path, log)
    save_to_csv(output_path, [{"feature": f} for f in selected_features.columns], fieldnames=["feature"])
    
    return list(selected_features.columns)

def train_models_with_loop(
    features_path: Path, 
    targets_path: Path, 
    selected_features_path: Path,
    models_output_path: Path,
    metrics_output_path: Path
) -> Dict[str, Any]:
    """
    Step 3: Model Training.
    Train Random Forest regressors for conductivity, Young's modulus, and fracture strength
    using the final feature set from T020.
    """
    ensure_output_directories()
    
    # Load selected features
    selected_features_data = load_csv_to_dicts(selected_features_path)
    selected_features = [row['feature'] for row in selected_features_data]
    
    # Load features and targets
    features_df = load_pandas_df(features_path)
    targets_df = load_pandas_df(targets_path)
    
    # Filter features to only selected ones
    available_features = [f for f in selected_features if f in features_df.columns]
    if len(available_features) != len(selected_features):
        missing = set(selected_features) - set(available_features)
        logging.warning(f"Missing features in dataset: {missing}. Proceeding with available: {available_features}")
    
    X = features_df[available_features].dropna()
    # Align targets with X
    valid_indices = X.index
    y_dict = {}
    
    # Define target columns based on task description
    target_mapping = {
        "conductivity": "conductivity",
        "youngs_modulus": "youngs_modulus", # Assuming column name in targets
        "fracture_strength": "fracture_strength"
    }
    
    # Adjust target column names if they differ in the actual CSV
    # Common variations: 'target_conductivity', 'y_conductivity', etc.
    # We will try to find the column that matches or contains the key
    actual_targets = {}
    for key, col_guess in target_mapping.items():
        if col_guess in targets_df.columns:
            actual_targets[key] = col_guess
        else:
            # Fuzzy match
            matches = [c for c in targets_df.columns if key in c.lower()]
            if matches:
                actual_targets[key] = matches[0]
            else:
                logging.error(f"Target {key} not found in {targets_df.columns}")
    
    models = {}
    metrics = {}
    
    for prop_key, target_col in actual_targets.items():
        if target_col not in targets_df.columns:
            logging.warning(f"Skipping {prop_key} due to missing target column.")
            continue
        
        y = targets_df.loc[valid_indices, target_col].dropna()
        # Re-align X
        common_indices = X.index.intersection(y.index)
        X_prop = X.loc[common_indices]
        y_prop = y.loc[common_indices]
        
        if len(X_prop) < 10:
            logging.warning(f"Not enough data for {prop_key} ({len(X_prop)} samples). Skipping.")
            continue
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X_prop, y_prop, test_size=0.2, random_state=42
        )
        
        # Train Random Forest
        rf = RandomForestRegressor(
            n_estimators=100, 
            max_depth=None, 
            random_state=42, 
            n_jobs=-1
        )
        rf.fit(X_train, y_train)
        
        # Predictions
        y_pred = rf.predict(X_test)
        
        # Metrics
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        models[prop_key] = rf
        metrics[prop_key] = {
            "r2": float(r2),
            "mae": float(mae),
            "rmse": float(rmse),
            "n_train": len(X_train),
            "n_test": len(X_test),
            "features_used": list(X_train.columns)
        }
        
        logging.info(f"Model trained for {prop_key}: R2={r2:.4f}, MAE={mae:.4f}")
    
    # Save models
    with open(models_output_path, 'wb') as f:
        pickle.dump(models, f)
    
    # Save metrics
    save_json_file(metrics_output_path, metrics)
    
    return metrics

def run_cross_validation(
    models_path: Path, 
    features_path: Path, 
    targets_path: Path, 
    output_path: Path,
    k_folds: int = 5
) -> Dict:
    """Perform k-fold cross-validation on trained models."""
    from sklearn.model_selection import cross_val_score, KFold
    
    with open(models_path, 'rb') as f:
        models = pickle.load(f)
    
    features_df = load_pandas_df(features_path)
    targets_df = load_pandas_df(targets_path)
    
    cv_results = {}
    
    for prop_key, model in models.items():
        # Find target column
        target_col = None
        for t in targets_df.columns:
            if prop_key in t.lower():
                target_col = t
                break
        
        if not target_col:
            continue
        
        # Prepare data
        X = features_df.dropna()
        y = targets_df.loc[X.index, target_col].dropna()
        common_idx = X.index.intersection(y.index)
        X_cv = X.loc[common_idx]
        y_cv = y.loc[common_idx]
        
        if len(X_cv) < k_folds:
            cv_results[prop_key] = {"error": "Insufficient data for CV"}
            continue
        
        kf = KFold(n_splits=k_folds, shuffle=True, random_state=42)
        r2_scores = cross_val_score(model, X_cv, y_cv, cv=kf, scoring='r2')
        mae_scores = cross_val_score(model, X_cv, y_cv, cv=kf, scoring='neg_mean_absolute_error')
        mae_scores = -mae_scores # Convert to positive
        
        cv_results[prop_key] = {
            "r2_mean": float(np.mean(r2_scores)),
            "r2_std": float(np.std(r2_scores)),
            "mae_mean": float(np.mean(mae_scores)),
            "mae_std": float(np.std(mae_scores)),
            "cv_std": float(np.std(r2_scores)) # Specific flag for high variance
        }
    
    save_json_file(output_path, cv_results)
    return cv_results

def main():
    """
    Main entry point for Model Training (T021).
    Dependencies: T020 (feature selection), T018 (processed features/targets).
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Define paths
    features_path = PROJECT_ROOT / "data" / "processed" / "features.csv"
    targets_path = PROJECT_ROOT / "data" / "processed" / "targets.csv"
    selected_features_path = PROJECT_ROOT / "data" / "processed" / "final_features.csv"
    models_output_path = PROJECT_ROOT / "data" / "processed" / "final_models.pkl"
    metrics_output_path = PROJECT_ROOT / "data" / "processed" / "training_metrics.json"
    
    # Ensure directories exist
    ensure_output_directories()
    
    try:
        # Check prerequisites
        if not features_path.exists():
            raise FileNotFoundError(f"Features file not found: {features_path}")
        if not targets_path.exists():
            raise FileNotFoundError(f"Targets file not found: {targets_path}")
        if not selected_features_path.exists():
            raise FileNotFoundError(f"Selected features file not found: {selected_features_path}")
        
        logging.info("Starting Model Training (T021)...")
        
        # Run training
        metrics = train_models_with_loop(
            features_path=features_path,
            targets_path=targets_path,
            selected_features_path=selected_features_path,
            models_output_path=models_output_path,
            metrics_output_path=metrics_output_path
        )
        
        logging.info(f"Training complete. Metrics saved to {metrics_output_path}")
        logging.info(f"Models saved to {models_output_path}")
        
    except Exception as e:
        logging.error(f"Model training failed: {e}")
        # Write error state to guarantee output
        save_json_file(metrics_output_path, {"error": str(e)})
        # Create empty pickle to avoid downstream crashes
        with open(models_output_path, 'wb') as f:
            pickle.dump({}, f)
        raise

if __name__ == "__main__":
    main()