import logging
import sys
import os
import json
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.dummy import DummyRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error
import pickle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_data(data_path: str = "data/processed/processed_alloys.csv") -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Load processed alloy data, split into features and target.
    Returns X, y, and the full dataframe for reference.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    
    # Define target and features based on previous tasks (T012-T016)
    target_col = "critical_cooling_rate"
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")
    
    feature_cols = [
        "mixing_enthalpy", 
        "atomic_size_mismatch", 
        "electronegativity_variance"
    ]
    
    # Validate features exist
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns: {missing_cols}")
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    logger.info(f"Loaded {len(df)} samples. Features: {feature_cols}, Target: {target_col}")
    return X, y, df

def train_model(X: np.ndarray, y: np.ndarray, random_state: int = 42) -> Tuple[Any, Dict[str, float]]:
    """
    Train a Random Forest regressor with 5-fold cross-validation.
    Returns the trained model and a dictionary of metrics.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )
    
    rf = RandomForestRegressor(
        n_estimators=100, 
        random_state=random_state, 
        n_jobs=-1
    )
    
    # Cross-validation
    cv_scores = cross_val_score(rf, X_train, y_train, cv=5, scoring='neg_mean_squared_error')
    cv_rmse = np.sqrt(-cv_scores)
    mean_rmse = np.mean(cv_rmse)
    fold_variance = np.var(cv_rmse)
    
    # Train final model
    rf.fit(X_train, y_train)
    
    # Test evaluation
    y_pred = rf.predict(X_test)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    metrics = {
        "mean_rmse": float(mean_rmse),
        "fold_variance": float(fold_variance),
        "test_rmse": float(test_rmse),
        "fold_scores": cv_rmse.tolist()
    }
    
    logger.info(f"Training complete. CV Mean RMSE: {mean_rmse:.4f}, Test RMSE: {test_rmse:.4f}")
    return rf, metrics

def generate_null_distribution(
    X: np.ndarray, 
    y: np.ndarray, 
    n_bootstrap: int = 1000, 
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Generate a null model distribution using a DummyRegressor (mean strategy).
    Performs n_bootstrap bootstrap samples, trains a dummy model on each,
    and records the RMSE distribution.
    
    Returns a dictionary containing the distribution statistics and raw values.
    """
    logger.info(f"Generating null model distribution with {n_bootstrap} bootstrap samples...")
    
    rng = np.random.RandomState(random_state)
    rmse_values = []
    
    n_samples = len(y)
    
    for i in range(n_bootstrap):
        # Bootstrap sampling (sample with replacement)
        indices = rng.choice(n_samples, size=n_samples, replace=True)
        X_boot = X[indices]
        y_boot = y[indices]
        
        # Train Dummy Regressor (mean strategy)
        dummy = DummyRegressor(strategy='mean')
        dummy.fit(X_boot, y_boot)
        
        # Predict on the SAME bootstrap sample (to estimate expected error under null)
        # Note: In bootstrap validation, we usually evaluate on the same sample 
        # to estimate the distribution of the estimator's performance.
        # Alternatively, we could evaluate on out-of-bag samples, but for 
        # a simple null distribution of the "mean" strategy, in-sample is standard.
        y_pred = dummy.predict(X_boot)
        rmse = np.sqrt(mean_squared_error(y_boot, y_pred))
        rmse_values.append(rmse)
    
    rmse_values = np.array(rmse_values)
    
    result = {
        "n_bootstrap": n_bootstrap,
        "strategy": "mean",
        "rmse_mean": float(np.mean(rmse_values)),
        "rmse_std": float(np.std(rmse_values)),
        "rmse_min": float(np.min(rmse_values)),
        "rmse_max": float(np.max(rmse_values)),
        "rmse_percentiles": {
            "25": float(np.percentile(rmse_values, 25)),
            "50": float(np.percentile(rmse_values, 50)),
            "75": float(np.percentile(rmse_values, 75)),
            "95": float(np.percentile(rmse_values, 95))
        },
        "raw_rmse_values": rmse_values.tolist()
    }
    
    logger.info(f"Null distribution generated. Mean RMSE: {result['rmse_mean']:.4f}, Std: {result['rmse_std']:.4f}")
    return result

def run_training(
    data_path: str = "data/processed/processed_alloys.csv",
    model_output_dir: str = "data/models",
    random_state: int = 42
) -> None:
    """
    Main entry point for the training pipeline.
    1. Loads data.
    2. Trains Random Forest model.
    3. Generates null model distribution.
    4. Saves model and metrics.
    """
    # Ensure output directory exists
    os.makedirs(model_output_dir, exist_ok=True)
    
    # Load data
    X, y, df = load_data(data_path)
    
    # Train RF model
    rf_model, rf_metrics = train_model(X, y, random_state)
    
    # Generate null distribution
    null_dist = generate_null_distribution(X, y, n_bootstrap=1000, random_state=random_state)
    
    # Save RF model
    model_path = os.path.join(model_output_dir, "random_forest_model.pkl")
    with open(model_path, 'wb') as f:
        pickle.dump(rf_model, f)
    logger.info(f"Model saved to {model_path}")
    
    # Save RF metrics
    metrics_path = os.path.join(model_output_dir, "model_metrics.json")
    with open(metrics_path, 'w') as f:
        json.dump(rf_metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")
    
    # Save null distribution (Task T024a specific output)
    null_dist_path = os.path.join(model_output_dir, "null_model_distribution.json")
    with open(null_dist_path, 'w') as f:
        json.dump(null_dist, f, indent=2)
    logger.info(f"Null distribution saved to {null_dist_path}")
    
    logger.info("Training pipeline completed successfully.")

if __name__ == "__main__":
    run_training()
