import os
import json
import logging
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_absolute_percentage_error, r2_score
from sklearn.linear_model import LinearRegression
from typing import Dict, List, Any, Optional, Tuple

# Import shared utilities from infrastructure if available, otherwise define locally
try:
    from infrastructure.path_utils import get_project_root, ensure_dir
except ImportError:
    def get_project_root():
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    def ensure_dir(path: str):
        os.makedirs(path, exist_ok=True)

def load_json_file(path: str) -> Dict:
    with open(path, 'r') as f:
        return json.load(f)

def save_json_file(path: str, data: Dict):
    ensure_dir(os.path.dirname(path))
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_csv_to_dicts(path: str) -> List[Dict]:
    df = pd.read_csv(path)
    return df.to_dict('records')

def save_to_csv(path: str, data: List[Dict]):
    ensure_dir(os.path.dirname(path))
    if not data:
        # Create empty file with headers if needed, or just return
        pd.DataFrame().to_csv(path, index=False)
        return
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)

def compute_vif(features: pd.DataFrame) -> Dict[str, float]:
    """Compute Variance Inflation Factor for each feature."""
    vif_data = {}
    # Add intercept for VIF calculation
    X = features.copy()
    for col in X.columns:
        if X[col].dtype in [np.int64, np.float64]:
            continue
        # One-hot encode if necessary (simplified assumption: numeric only for VIF)
    
    # Simple VIF implementation
    for i, col in enumerate(X.columns):
        if X[col].dtype not in [np.int64, np.float64]:
            continue
        y = X[col]
        X_other = X.drop(columns=[col])
        if X_other.shape[1] == 0:
            vif_data[col] = 1.0
            continue
        try:
            model = LinearRegression()
            model.fit(X_other, y)
            rsq = model.score(X_other, y)
            vif = 1.0 / (1.0 - rsq) if (1.0 - rsq) > 1e-9 else np.inf
            vif_data[col] = vif
        except Exception:
            vif_data[col] = np.inf
    return vif_data

def train_initial_rf_for_importance(X: pd.DataFrame, y: pd.Series, n_estimators: int = 50, random_state: int = 42) -> RandomForestRegressor:
    model = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state, n_jobs=-1)
    model.fit(X, y)
    return model

def save_preliminary_importance(model: RandomForestRegressor, feature_names: List[str], path: str):
    importances = model.feature_importances_
    data = [{"feature": name, "importance": float(imp)} for name, imp in zip(feature_names, importances)]
    save_to_csv(path, data)

def run_preliminary_model_training(features_path: str, targets_path: str, output_model_path: str, importance_path: str):
    features_df = pd.read_csv(features_path)
    targets_df = pd.read_csv(targets_path)
    
    # Assume target column is 'target_value' or similar, adjust based on actual schema
    # For this task, we assume targets.csv has columns like 'conductivity', 'youngs_modulus', 'fracture_strength'
    # But for preliminary, we might pick one or loop. Let's assume we train one generic model or specific ones.
    # The task T021a says "single Random Forest model". Let's pick the first numeric target column.
    target_cols = [c for c in targets_df.columns if c in features_df.columns] # Safety check
    # Actually, targets and features are usually separate. Let's assume a standard target column name.
    # Based on T018, targets are normalized changes. Let's assume column name 'target_value' or similar.
    # If multiple targets, we might need to train separate models. T021a says "single".
    # Let's assume the target column is named 'target' or we iterate.
    # For T022, we need models for 3 properties. T021a is just for importance.
    # Let's assume we train on the first available target column for importance.
    
    target_col = None
    for col in ['conductivity', 'youngs_modulus', 'fracture_strength', 'target_value', 'y']:
        if col in targets_df.columns:
            target_col = col
            break
    
    if target_col is None:
        raise ValueError("No target column found in targets.csv")
        
    X = features_df.dropna(axis=1, how='all')
    y = targets_df[target_col]
    
    # Align indices
    common_idx = X.index.intersection(y.index)
    X = X.loc[common_idx]
    y = y.loc[common_idx]
    
    model = train_initial_rf_for_importance(X, y)
    with open(output_model_path, 'wb') as f:
        pickle.dump(model, f)
    
    save_preliminary_importance(model, X.columns.tolist(), importance_path)
    return model

def handle_collinearity(vif_data: Dict[str, float], threshold: float = 5.0) -> List[str]:
    # Return features to keep (VIF <= threshold)
    return [k for k, v in vif_data.items() if v <= threshold]

def run_feature_selection_loop(features_path: str, targets_path: str, model_path: str, log_path: str, max_iter: int = 10):
    # Load data
    features_df = pd.read_csv(features_path)
    targets_df = pd.read_csv(targets_path)
    
    # Determine target
    target_col = None
    for col in ['conductivity', 'youngs_modulus', 'fracture_strength', 'target_value', 'y']:
        if col in targets_df.columns:
            target_col = col
            break
    if target_col is None:
        raise ValueError("Target column not found")
        
    X = features_df
    y = targets_df[target_col]
    common_idx = X.index.intersection(y.index)
    X = X.loc[common_idx]
    y = y.loc[common_idx]
    
    log_data = []
    current_features = list(X.columns)
    
    for i in range(max_iter):
        vif_data = compute_vif(X[current_features])
        max_vif = max(vif_data.values()) if vif_data else 0
        
        log_entry = {"iteration": i, "features": current_features, "max_vif": max_vif}
        log_data.append(log_entry)
        
        if max_vif <= 5.0:
            break
        
        # Find lowest importance
        # Train quick model on current features
        model = train_initial_rf_for_importance(X[current_features], y, n_estimators=10)
        importances = model.feature_importances_
        feature_importance = list(zip(current_features, importances))
        # Sort by importance ascending
        feature_importance.sort(key=lambda x: x[1])
        
        # Remove lowest
        removed_feature = feature_importance[0][0]
        current_features.remove(removed_feature)
        log_entry["removed_feature"] = removed_feature
        logging.info(f"Removed feature {removed_feature} (VIF: {vif_data.get(removed_feature, 'N/A')}, Importance: {feature_importance[0][1]})")
        
        if len(current_features) <= 1:
            break
    
    save_json_file(log_path, log_data)
    return current_features

def train_models_with_loop(features_path: str, targets_path: str, output_dir: str, max_iter: int = 10):
    # This function implements the full training loop with VIF check
    # It trains separate models for conductivity, youngs_modulus, fracture_strength
    features_df = pd.read_csv(features_path)
    targets_df = pd.read_csv(targets_path)
    
    target_cols = ['conductivity', 'youngs_modulus', 'fracture_strength']
    models = {}
    
    for target in target_cols:
        if target not in targets_df.columns:
            logging.warning(f"Target {target} not found, skipping.")
            continue
            
        y = targets_df[target]
        X = features_df
        common_idx = X.index.intersection(y.index)
        X = X.loc[common_idx]
        y = y.loc[common_idx]
        
        current_features = list(X.columns)
        
        for i in range(max_iter):
            vif_data = compute_vif(X[current_features])
            max_vif = max(vif_data.values()) if vif_data else 0
            
            if max_vif <= 5.0:
                break
            
            # Train quick model
            model_temp = train_initial_rf_for_importance(X[current_features], y, n_estimators=10)
            importances = model_temp.feature_importances_
            feature_importance = list(zip(current_features, importances))
            feature_importance.sort(key=lambda x: x[1])
            
            removed_feature = feature_importance[0][0]
            current_features.remove(removed_feature)
            
            if len(current_features) <= 1:
                break
        
        # Train final model
        X_final = X[current_features]
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X_final, y)
        models[target] = {"model": model, "features": current_features}
        
        with open(os.path.join(output_dir, f"model_{target}.pkl"), 'wb') as f:
            pickle.dump(models[target], f)
            
    return models

def run_cross_validation(models_dir: str, features_path: str, targets_path: str, output_path: str):
    """
    Perform k-fold cross-validation (k=5) on the models trained in T021.
    Compute mean R², MAPE, and standard deviation of R² (cv_std).
    Flag as HIGH_VARIANCE if cv_std > 0.1.
    """
    import os
    import json
    import pickle
    import pandas as pd
    import numpy as np
    from sklearn.model_selection import cross_val_score, KFold
    from sklearn.metrics import mean_absolute_percentage_error, r2_score
    from typing import Dict, List, Any

    # Load features and targets
    features_df = pd.read_csv(features_path)
    targets_df = pd.read_csv(targets_path)

    target_names = ['conductivity', 'youngs_modulus', 'fracture_strength']
    results = {}

    for target in target_names:
        model_path = os.path.join(models_dir, f"model_{target}.pkl")
        if not os.path.exists(model_path):
            logging.warning(f"Model for {target} not found at {model_path}. Skipping.")
            continue

        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        model = model_data['model']
        used_features = model_data['features']

        X = features_df[used_features]
        y = targets_df[target]

        # Align indices
        common_idx = X.index.intersection(y.index)
        X = X.loc[common_idx]
        y = y.loc[common_idx]

        # Perform 5-fold CV
        kfold = KFold(n_splits=5, shuffle=True, random_state=42)
        
        # Compute R2 scores for each fold
        r2_scores = cross_val_score(model, X, y, cv=kfold, scoring='r2')
        
        # Compute MAPE for each fold (requires manual loop or custom scorer)
        # cross_val_score doesn't support MAPE directly without custom scorer
        mape_scores = []
        for train_idx, test_idx in kfold.split(X):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            model_fold = RandomForestRegressor(n_estimators=model.n_estimators, random_state=42, n_jobs=-1)
            model_fold.fit(X_train, y_train)
            y_pred = model_fold.predict(X_test)
            
            # Avoid division by zero in MAPE
            mape = mean_absolute_percentage_error(y_test, y_pred)
            mape_scores.append(mape)

        mean_r2 = np.mean(r2_scores)
        std_r2 = np.std(r2_scores)
        mean_mape = np.mean(mape_scores)
        
        high_variance = std_r2 > 0.1

        results[target] = {
            "mean_r2": float(mean_r2),
            "std_r2": float(std_r2),
            "mean_mape": float(mean_mape),
            "high_variance": high_variance,
            "fold_r2_scores": r2_scores.tolist(),
            "fold_mape_scores": mape_scores
        }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logging.info(f"Cross-validation results saved to {output_path}")
    return results

def main():
    logging.basicConfig(level=logging.INFO)
    project_root = get_project_root()
    
    # Paths
    features_path = os.path.join(project_root, "data", "processed", "final_features.csv")
    targets_path = os.path.join(project_root, "data", "processed", "targets.csv")
    models_dir = os.path.join(project_root, "data", "processed")
    output_path = os.path.join(project_root, "data", "processed", "cv_results.json")
    
    if not os.path.exists(features_path) or not os.path.exists(targets_path):
        logging.error("Processed data files not found. Run T018 and T020 first.")
        return
        
    if not os.path.exists(os.path.join(models_dir, "model_conductivity.pkl")):
        logging.error("Models not found. Run T021 first.")
        return

    results = run_cross_validation(models_dir, features_path, targets_path, output_path)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()