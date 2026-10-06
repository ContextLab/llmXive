"""
Model training module with resource constraints enforcement.

Implements Random Forest and Gradient Boosting models with host-identity splitting
and strict CPU/RAM monitoring.
"""
import os
import json
import logging
import time
import tracemalloc
import threading
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.base import clone

# Import from project utilities
from utils.logger import get_logger
from utils.performance_optimizer import (
    get_current_ram_gb, 
    check_ram_constraint, 
    check_runtime_constraint,
    enforce_cpu_only,
    monitor_resources,
    optimize_sklearn_params,
    MAX_RAM_GB,
    MAX_RUNTIME_SECONDS
)

logger = get_logger(__name__)

class ResourceMonitor:
    """Background monitor for RAM and runtime constraints."""
    
    def __init__(self, start_time: float, check_interval: float = 30.0):
        self.start_time = start_time
        self.check_interval = check_interval
        self.monitor_thread = None
        self.should_stop = threading.Event()
        
    def start(self):
        """Start the monitoring thread."""
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"Resource monitor started (interval: {self.check_interval}s)")
        
    def stop(self):
        """Stop the monitoring thread."""
        self.should_stop.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
            
    def _monitor_loop(self):
        """Background loop to check constraints."""
        while not self.should_stop.is_set():
            try:
                # Check RAM
                current_ram = get_current_ram_gb()
                if current_ram > MAX_RAM_GB:
                    logger.error(f"CRITICAL: RAM limit exceeded: {current_ram:.2f}GB > {MAX_RAM_GB}GB")
                    raise RuntimeError(f"RAM limit exceeded: {current_ram:.2f}GB > {MAX_RAM_GB}GB")
                
                # Check runtime
                elapsed = time.time() - self.start_time
                if elapsed > MAX_RUNTIME_SECONDS:
                    logger.error(f"CRITICAL: Runtime limit exceeded: {elapsed:.0f}s > {MAX_RUNTIME_SECONDS}s")
                    raise RuntimeError(f"Runtime limit exceeded: {elapsed:.0f}s > {MAX_RUNTIME_SECONDS}s")
                
                time.sleep(self.check_interval)
            except RuntimeError:
                raise
            except Exception as e:
                logger.warning(f"Monitor check failed: {e}")
                time.sleep(self.check_interval)

def load_preprocessed_data() -> pd.DataFrame:
    """Load the preprocessed dataset."""
    data_path = Path("data/processed/halide_binding_data.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"Preprocessed data not found at {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} records from {data_path}")
    return df

def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """Extract feature columns from the dataset."""
    exclude_cols = ['host_id', 'halide', 'log_K', 'smiles', 'inchi']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    logger.info(f"Using {len(feature_cols)} features: {feature_cols[:5]}...")
    return feature_cols

class HostIdentityKFold:
    """Stratified K-Fold split ensuring no host appears in both train and val."""
    
    def __init__(self, n_splits: int = 5):
        self.n_splits = n_splits
        
    def split(self, df: pd.DataFrame, features: List[str], target: str = 'log_K'):
        """Generate train/val indices ensuring host separation."""
        # Group by host_id
        hosts = df['host_id'].unique()
        np.random.seed(42)
        np.random.shuffle(hosts)
        
        # Split hosts into folds
        fold_size = len(hosts) // self.n_splits
        folds = []
        
        for i in range(self.n_splits):
            start_idx = i * fold_size
            end_idx = start_idx + fold_size if i < self.n_splits - 1 else len(hosts)
            val_hosts = set(hosts[start_idx:end_idx])
            train_hosts = set(hosts) - val_hosts
            
            train_indices = df[df['host_id'].isin(train_hosts)].index.tolist()
            val_indices = df[df['host_id'].isin(val_hosts)].index.tolist()
            
            folds.append((train_indices, val_indices))
            
        return iter(folds)

def train_and_evaluate_model(
    df: pd.DataFrame, 
    model, 
    features: List[str], 
    target: str = 'log_K',
    n_splits: int = 5
) -> Dict[str, Any]:
    """Train model with host-identity split and evaluate."""
    splitter = HostIdentityKFold(n_splits=n_splits)
    
    r2_scores = []
    rmse_scores = []
    feature_importances = None
    
    for fold_idx, (train_idx, val_idx) in enumerate(splitter.split(df, features)):
        logger.info(f"Training fold {fold_idx + 1}/{n_splits}")
        
        X_train = df.loc[train_idx, features]
        y_train = df.loc[train_idx, target]
        X_val = df.loc[val_idx, features]
        y_val = df.loc[val_idx, target]
        
        # Train
        model_fold = clone(model)
        model_fold.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model_fold.predict(X_val)
        r2 = r2_score(y_val, y_pred)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        
        r2_scores.append(r2)
        rmse_scores.append(rmse)
        
        # Collect feature importances (if available)
        if hasattr(model_fold, 'feature_importances_'):
            if feature_importances is None:
                feature_importances = model_fold.feature_importances_.copy()
            else:
                feature_importances += model_fold.feature_importances_
    
    # Average feature importances
    if feature_importances is not None:
        feature_importances /= n_splits
    
    return {
        'r2_scores': r2_scores,
        'rmse_scores': rmse_scores,
        'mean_r2': np.mean(r2_scores),
        'mean_rmse': np.mean(rmse_scores),
        'feature_importances': feature_importances.tolist() if feature_importances is not None else None
    }

def run_random_forest_training(df: pd.DataFrame, features: List[str]) -> Tuple[Any, Dict[str, Any]]:
    """Train Random Forest with resource monitoring."""
    start_time = time.time()
    tracemalloc.start()
    
    # Start resource monitor
    monitor = ResourceMonitor(start_time, check_interval=30.0)
    monitor.start()
    
    try:
        # Optimize parameters
        base_params = {
            'n_estimators': 100,
            'max_depth': 20,
            'random_state': 42
        }
        optimized_params = optimize_sklearn_params(base_params)
        optimized_params['n_jobs'] = 1  # Force single-threaded
        
        model = RandomForestRegressor(**optimized_params)
        
        logger.info("Training Random Forest model...")
        results = train_and_evaluate_model(df, model, features)
        
        # Check final constraints
        current_ram = get_current_ram_gb()
        elapsed = time.time() - start_time
        
        ram_ok, ram_msg = check_ram_constraint(current_ram)
        time_ok, time_msg = check_runtime_constraint(start_time)
        
        logger.info(ram_msg)
        logger.info(time_msg)
        
        if not ram_ok or not time_ok:
            raise RuntimeError(f"Resource limits exceeded: {ram_msg}, {time_msg}")
        
        return model, results
        
    finally:
        monitor.stop()
        tracemalloc.stop()

def run_gradient_boosting_training(df: pd.DataFrame, features: List[str]) -> Tuple[Any, Dict[str, Any]]:
    """Train Gradient Boosting with resource monitoring."""
    start_time = time.time()
    tracemalloc.start()
    
    # Start resource monitor
    monitor = ResourceMonitor(start_time, check_interval=30.0)
    monitor.start()
    
    try:
        # Optimize parameters
        base_params = {
            'n_estimators': 100,
            'max_depth': 5,
            'learning_rate': 0.1,
            'random_state': 42
        }
        optimized_params = optimize_sklearn_params(base_params)
        optimized_params['n_jobs'] = 1  # Force single-threaded
        
        model = GradientBoostingRegressor(**optimized_params)
        
        logger.info("Training Gradient Boosting model...")
        results = train_and_evaluate_model(df, model, features)
        
        # Check final constraints
        current_ram = get_current_ram_gb()
        elapsed = time.time() - start_time
        
        ram_ok, ram_msg = check_ram_constraint(current_ram)
        time_ok, time_msg = check_runtime_constraint(start_time)
        
        logger.info(ram_msg)
        logger.info(time_msg)
        
        if not ram_ok or not time_ok:
            raise RuntimeError(f"Resource limits exceeded: {ram_msg}, {time_msg}")
        
        return model, results
        
    finally:
        monitor.stop()
        tracemalloc.stop()

def save_model_artifacts(
    model_name: str, 
    model: Any, 
    metrics: Dict[str, Any], 
    output_dir: Path
):
    """Save model and metrics to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = output_dir / f"{model_name}_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Saved model to {model_path}")
    
    # Save metrics
    metrics_path = output_dir.parent / 'metrics' / f"{model_name}_metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {metrics_path}")

def write_resource_failure_report(reason: str, output_path: Path):
    """Write failure report when resource limits are exceeded."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        'status': 'resource_limit_exceeded',
        'reason': reason,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.error(f"Resource failure report written to {output_path}")

def main():
    """Main entry point for model training."""
    logger.info("Starting model training pipeline...")
    
    try:
        # Load data
        df = load_preprocessed_data()
        features = get_feature_columns(df)
        
        # Train Random Forest
        rf_model, rf_metrics = run_random_forest_training(df, features)
        save_model_artifacts('random_forest', rf_model, rf_metrics, Path('data/processed/models'))
        
        # Train Gradient Boosting
        gb_model, gb_metrics = run_gradient_boosting_training(df, features)
        save_model_artifacts('gradient_boosting', gb_model, gb_metrics, Path('data/processed/models'))
        
        logger.info("Model training completed successfully")
        
    except RuntimeError as e:
        logger.error(f"Training failed: {e}")
        write_resource_failure_report(str(e), Path('data/processed/failure_flag.json'))
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == '__main__':
    main()