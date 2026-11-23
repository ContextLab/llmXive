import json
import os
import sys
import pickle
import time
import warnings
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import mean_absolute_error, r2_score

# Import config utilities
from config import get_project_root, get_config_value, get_n_estimators, get_random_seed

def load_final_dataset() -> pd.DataFrame:
    """Load the final engineered dataset."""
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "final_dataset.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Final dataset not found at {input_path}. "
                                "Run T025 (finalize_dataset) first.")
    
    df = pd.read_csv(input_path)
    
    # Size constraint check
    if len(df) > 10000:
        raise ValueError(f"Dataset size ({len(df)}) exceeds 10,000 rows. "
                         "Size constraint violated.")
    
    return df

def split_data(df: pd.DataFrame, test_size: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    """
    Split data into train and test sets.
    Returns X_train, X_test, and split indices for reproducibility.
    """
    # Feature columns (exclude target)
    feature_cols = [col for col in df.columns if col != 'time_to_peak_min']
    target_col = 'time_to_peak_min'
    
    X = df[feature_cols]
    y = df[target_col]
    
    # Simple split for now (Stratified logic handled in T028 if needed, 
    # but T028 saves indices. We load them here if they exist)
    split_indices_path = get_project_root() / "data" / "split_indices.npy"
    
    if split_indices_path.exists():
        try:
            indices = np.load(split_indices_path, allow_pickle=True).item()
            train_idx = indices['train']
            test_idx = indices['test']
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            return X_train, X_test, y_train, y_test, indices
        except Exception as e:
            warnings.warn(f"Failed to load split indices: {e}. Using random split.")
    
    # Fallback to random split if indices missing
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=get_random_seed()
    )
    
    # Create indices for saving
    indices = {
        'train': X_train.index,
        'test': X_test.index
    }
    np.save(split_indices_path, indices)
    
    return X_train, X_test, y_train, y_test, indices

def detect_pure_aluminum(df: pd.DataFrame) -> bool:
    """
    Check if standard deviation of all composition columns is effectively zero.
    """
    composition_cols = ['Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt']
    # Ensure columns exist
    if not all(col in df.columns for col in composition_cols):
        # If columns missing, assume not pure aluminum (or raise error?)
        # Assuming data integrity from previous steps
        return False
    
    stds = df[composition_cols].std()
    # Check if all stds are < 1e-9
    is_pure = all(std < 1e-9 for std in stds)
    return is_pure

def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestRegressor:
    """Train the Random Forest Regressor (Interaction Model)."""
    n_estimators = get_n_estimators()
    seed = get_random_seed()
    
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=None,
        random_state=seed,
        n_jobs=-1  # Use all available CPU cores
    )
    
    start_time = time.time()
    model.fit(X_train, y_train)
    duration = time.time() - start_time
    
    print(f"Model trained in {duration:.2f} seconds.")
    return model

def cross_validate_model(model: RandomForestRegressor, X: pd.DataFrame, y: pd.Series) -> Tuple[float, float]:
    """Perform 5-fold cross-validation."""
    # Use StratifiedKFold if target is discrete, but here it's continuous.
    # Using KFold for regression.
    kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=get_random_seed())
    # Note: StratifiedKFold requires discrete y. For continuous y, use KFold.
    # Let's switch to KFold for regression to avoid errors on continuous targets.
    from sklearn.model_selection import KFold
    kfold = KFold(n_splits=5, shuffle=True, random_state=get_random_seed())
    
    scores = cross_val_score(model, X, y, cv=kfold, scoring='r2')
    return scores.mean(), scores.std()

def evaluate_model(model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> Tuple[float, float]:
    """Evaluate model on held-out test set."""
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    return mae, r2

def save_model(model: RandomForestRegressor, path: Path):
    """Save the trained model using pickle protocol 4."""
    with open(path, 'wb') as f:
        pickle.dump(model, f, protocol=4)

def load_baseline_stats() -> float:
    """Load baseline mean from T012 artifact."""
    project_root = get_project_root()
    stats_path = project_root / "artifacts" / "reports" / "baseline_stats.json"
    
    if not stats_path.exists():
        raise FileNotFoundError(f"Baseline stats not found at {stats_path}. "
                                "Run T012 (calculate_baseline_stats) first.")
    
    with open(stats_path, 'r') as f:
        data = json.load(f)
    
    if 'baseline_mean' not in data:
        raise ValueError("baseline_stats.json missing 'baseline_mean' key.")
    
    return float(data['baseline_mean'])

def save_metrics(metrics: Dict[str, Any], path: Path):
    """Save training metrics to JSON."""
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)

def run_training_pipeline():
    """Execute the full training pipeline for T029."""
    project_root = get_project_root()
    
    # 1. Load Data
    print("Loading final dataset...")
    df = load_final_dataset()
    
    # 2. Detect Pure Aluminum
    is_pure_aluminum = detect_pure_aluminum(df)
    if is_pure_aluminum:
        warnings.warn("Pure Aluminum detected (std < 1e-9 for all composition columns). "
                      "Setting pure_aluminum_flag: true.")
    
    # 3. Split Data
    print("Splitting data...")
    X_train, X_test, y_train, y_test, split_indices = split_data(df)
    
    # 4. Train Model
    print("Training Random Forest Regressor (Interaction Model)...")
    model = train_model(X_train, y_train)
    
    # 5. Cross-Validation
    print("Performing 5-fold Cross-Validation...")
    cv_r2_mean, cv_r2_std = cross_validate_model(model, X_train, y_train)
    
    # 6. Test Evaluation
    print("Evaluating on Test Set...")
    test_mae, test_r2 = evaluate_model(model, X_test, y_test)
    
    # 7. Load Baseline for Threshold Check (SC-006)
    baseline_mean = load_baseline_stats()
    mae_threshold = baseline_mean * 0.5  # Example threshold logic from SC-006 context
    
    # 8. Save Model
    model_path = project_root / "artifacts" / "models" / "kinetic_model.pkl"
    save_model(model, model_path)
    print(f"Model saved to {model_path}")
    
    # 9. Save Metrics
    metrics = {
        "cv_r2_mean": float(cv_r2_mean),
        "cv_r2_std": float(cv_r2_std),
        "test_mae": float(test_mae),
        "test_r2": float(test_r2),
        "baseline_mean": float(baseline_mean),
        "mae_threshold": float(mae_threshold),
        "pure_aluminum_flag": is_pure_aluminum,
        "n_estimators": get_n_estimators(),
        "seed": get_random_seed()
    }
    
    metrics_path = project_root / "artifacts" / "reports" / "training_metrics.json"
    save_metrics(metrics, metrics_path)
    print(f"Metrics saved to {metrics_path}")
    
    # Summary
    print("\n--- Training Summary ---")
    print(f"CV R² (Mean): {cv_r2_mean:.4f} (+/- {cv_r2_std:.4f})")
    print(f"Test MAE: {test_mae:.4f}")
    print(f"Test R²: {test_r2:.4f}")
    print(f"Pure Aluminum Flag: {is_pure_aluminum}")
    print(f"MAE Threshold (50% of baseline): {mae_threshold:.4f}")
    print(f"MAE vs Threshold: {'PASS' if test_mae < mae_threshold else 'FAIL'}")

def main():
    """Main entry point for T029."""
    try:
        run_training_pipeline()
    except Exception as e:
        print(f"Error during training pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()