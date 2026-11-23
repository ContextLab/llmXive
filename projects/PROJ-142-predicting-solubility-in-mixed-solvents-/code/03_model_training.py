import os
import sys
import json
import time
import pickle
from pathlib import Path
import argparse
import signal
import multiprocessing
from multiprocessing import Process, Value
import psutil

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.constants import DATA_DIR, ARTIFACTS_DIR, PROCESSED_DIR
from utils.watchdog import run_watchdog, log_message, get_process_memory_gb, get_process_disk_gb
from utils.errors import CustomDataError

# Configuration
RAM_LIMIT_GB = 7.0
DISK_LIMIT_GB = 14.0
LOG_FILE = ARTIFACTS_DIR / "resource_monitor.log"

def load_data():
    """Load processed dataset from disk."""
    input_path = PROCESSED_DIR / "solubility_features.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Input data not found at {input_path}. Run T018 first.")
    return input_path

def prepare_features(df, target_col='logS'):
    """Prepare features and target for training."""
    # Assuming 'solute_fp' is a string representation of list or needs parsing
    # For simplicity, we select numeric columns excluding target and SMILES
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    if target_col in numeric_cols:
        numeric_cols.remove(target_col)
    
    # Filter out non-descriptor columns if necessary (e.g., IDs)
    # For now, assume all numeric are features
    X = df[numeric_cols]
    y = df[target_col]
    return X, y, numeric_cols

def train_xgboost(X, y, feature_names):
    """Train XGBoost model."""
    try:
        import xgboost as xgb
        from sklearn.model_selection import cross_val_score, GridSearchCV
        
        dtrain = xgb.DMatrix(X, label=y, feature_names=feature_names)
        
        param = {
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse',
            'max_depth': 6,
            'eta': 0.3,
            'seed': 42
        }
        
        # Simple training with cross-validation for demo
        cv_result = xgb.cv(param, dtrain, num_boost_round=100, nfold=5, seed=42)
        bst = xgb.train(param, dtrain, num_boost_round=100)
        
        return bst, cv_result
    except ImportError:
        raise CustomDataError("xgboost not installed. Please install it in requirements.txt.")

def train_random_forest(X, y, feature_names):
    """Train Random Forest model."""
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import cross_val_score
    
    rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    
    scores = cross_val_score(rf, X, y, cv=5, scoring='r2')
    return rf, scores

def train_abraham_baseline(X, y, feature_names):
    """Train Abraham baseline (Linear Regression)."""
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import cross_val_score
    
    # Check if Abraham parameters exist in features
    abraham_params = [c for c in feature_names if c.startswith('abraham_')]
    
    if not abraham_params:
        # Fallback to simple linear regression on all features
        model = LinearRegression()
    else:
        # Use only Abraham parameters if available
        X_abraham = X[abraham_params]
        model = LinearRegression()
        model.fit(X_abraham, y)
        return model, "Abraham parameters only"
    
    model.fit(X, y)
    scores = cross_val_score(model, X, y, cv=5, scoring='r2')
    return model, scores

def evaluate_models(models, X, y):
    """Evaluate all trained models."""
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
    
    metrics = {}
    for name, model in models.items():
        if isinstance(model, dict) and 'model' in model:
            # Handle wrapped models
            m = model['model']
        else:
            m = model
        
        try:
            if hasattr(m, 'predict'):
                preds = m.predict(X)
            else:
                # XGBoost DMatrix handling
                dmat = xgb.DMatrix(X)
                preds = m.predict(dmat)
            
            rmse = mean_squared_error(y, preds, squared=False)
            r2 = r2_score(y, preds)
            mae = mean_absolute_error(y, preds)
            
            metrics[name] = {
                'rmse': float(rmse),
                'r2': float(r2),
                'mae': float(mae)
            }
        except Exception as e:
            metrics[name] = {'error': str(e)}
    
    return metrics

def save_models(models, metrics):
    """Save trained models and metrics."""
    output_path = ARTIFACTS_DIR / "trained_models.pkl"
    with open(output_path, 'wb') as f:
        pickle.dump({'models': models, 'metrics': metrics}, f)
    return output_path

def save_report(metrics, models_info):
    """Save training report."""
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'metrics': metrics,
        'models_info': models_info
    }
    output_path = ARTIFACTS_DIR / "training_report.json"
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    return output_path

def run_training_with_watchdog():
    """Main training function wrapped with watchdog."""
    # Start watchdog in a separate process
    watchdog_process = Process(
        target=run_watchdog,
        args=(os.getpid(), RAM_LIMIT_GB, DISK_LIMIT_GB, LOG_FILE)
    )
    watchdog_process.start()
    
    try:
        # Load data
        print("Loading data...")
        data_path = load_data()
        import pandas as pd
        df = pd.read_csv(data_path)
        
        # Prepare features
        print("Preparing features...")
        X, y, feature_names = prepare_features(df)
        
        # Train models
        print("Training XGBoost...")
        xgb_model, xgb_cv = train_xgboost(X, y, feature_names)
        
        print("Training Random Forest...")
        rf_model, rf_scores = train_random_forest(X, y, feature_names)
        
        print("Training Abraham Baseline...")
        ab_model, ab_scores = train_abraham_baseline(X, y, feature_names)
        
        # Collect models
        models = {
            'xgboost': xgb_model,
            'random_forest': rf_model,
            'abraham': ab_model
        }
        
        # Evaluate
        print("Evaluating models...")
        metrics = evaluate_models(models, X, y)
        
        # Save results
        print("Saving models and metrics...")
        save_models(models, metrics)
        save_report(metrics, {
            'xgboost_cv': str(xgb_cv),
            'rf_r2_mean': float(rf_scores.mean()),
            'ab_r2_mean': float(ab_scores.mean()) if hasattr(ab_scores, 'mean') else str(ab_scores)
        })
        
        print("Training completed successfully.")
        
    except Exception as e:
        # Log error and re-raise
        log_message(f"Training failed: {str(e)}", level="ERROR", log_file=LOG_FILE)
        raise e
    finally:
        # Terminate watchdog
        if watchdog_process.is_alive():
            watchdog_process.terminate()
            watchdog_process.join(timeout=5)

def main():
    """Entry point for training script."""
    parser = argparse.ArgumentParser(description="Train solubility prediction models")
    parser.add_argument('--watchdog', action='store_true', help='Enable resource monitoring watchdog')
    args = parser.parse_args()
    
    if args.watchdog:
        run_training_with_watchdog()
    else:
        # Run without watchdog for testing
        import pandas as pd
        from utils.constants import PROCESSED_DIR
        data_path = PROCESSED_DIR / "solubility_features.csv"
        if not data_path.exists():
            print(f"Warning: {data_path} not found. Skipping training.")
            return
        
        df = pd.read_csv(data_path)
        X, y, feature_names = prepare_features(df)
        
        xgb_model, _ = train_xgboost(X, y, feature_names)
        rf_model, _ = train_random_forest(X, y, feature_names)
        ab_model, _ = train_abraham_baseline(X, y, feature_names)
        
        models = {'xgboost': xgb_model, 'random_forest': rf_model, 'abraham': ab_model}
        metrics = evaluate_models(models, X, y)
        save_models(models, metrics)
        save_report(metrics, {})
        print("Training completed without watchdog.")

if __name__ == "__main__":
    main()