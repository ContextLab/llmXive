import os
import sys
import json
import logging
import pickle
import time
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import cross_val_score, KFold
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_squared_error, r2_score
from utils import set_seed, setup_logging, load_state, update_state, compute_file_hash

# Configure logging
logger = setup_logging(__name__)

def load_data():
    """Load the preprocessed dataset."""
    data_path = Path("data/processed/cleaned_316L.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found at {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Loaded data with shape {df.shape}")
    return df

def train_gradient_boosting(X, y, seed=42):
    """Train a Gradient Boosting Regressor with 5-fold CV."""
    set_seed(seed)
    model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        random_state=seed
    )
    return model

def train_mlp(X, y, seed=42):
    """Train an MLP Regressor with 5-fold CV."""
    set_seed(seed)
    # Hidden layers tuned for small dataset
    model = MLPRegressor(
        hidden_layer_sizes=(64, 32),
        activation='relu',
        solver='adam',
        alpha=0.0001,
        batch_size='auto',
        learning_rate='adaptive',
        learning_rate_init=0.001,
        max_iter=500,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=10,
        random_state=seed,
        verbose=False
    )
    return model

def train_dummy_baseline(X, y, seed=42):
    """Train a dummy baseline regressor (mean strategy)."""
    set_seed(seed)
    model = DummyRegressor(strategy='mean')
    return model

def compute_metrics(model, X, y, cv_folds=5, seed=42):
    """Compute RMSE and R² for each fold and aggregate mean."""
    set_seed(seed)
    kf = KFold(n_splits=cv_folds, shuffle=True, random_state=seed)
    
    rmse_scores = []
    r2_scores = []
    
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        model_clone = type(model)(**model.get_params())
        model_clone.fit(X_train, y_train)
        y_pred = model_clone.predict(X_test)
        
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        rmse_scores.append(rmse)
        r2_scores.append(r2)
    
    return {
        'rmse_per_fold': rmse_scores,
        'r2_per_fold': r2_scores,
        'mean_rmse': np.mean(rmse_scores),
        'mean_r2': np.mean(r2_scores),
        'std_rmse': np.std(rmse_scores),
        'std_r2': np.std(r2_scores)
    }

def save_model(model, model_name, output_path):
    """Save the trained model to a pickle file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)
    
    logger.info(f"Model saved to {output_path}")
    return output_path

def main():
    """Main execution for T025: Save trained models."""
    logger.info("Starting model training and saving (T025)")
    
    # Load data
    df = load_data()
    
    # Define features and target
    # Assuming columns: power, speed, hatch, thickness, porosity (target)
    # Energy density might be derived or present, but we use raw params for model
    feature_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    target_col = 'porosity'
    
    # Validate columns exist
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns: {missing_cols}")
    if target_col not in df.columns:
        raise ValueError(f"Missing target column: {target_col}")
    
    X = df[feature_cols]
    y = df[target_col]
    
    logger.info(f"Features: {feature_cols}, Target: {target_col}")
    
    # Train Gradient Boosting
    logger.info("Training Gradient Boosting model...")
    gb_model = train_gradient_boosting(X, y)
    gb_model.fit(X, y)  # Fit on full data for saving
    
    # Train MLP
    logger.info("Training MLP model...")
    mlp_model = train_mlp(X, y)
    mlp_model.fit(X, y)  # Fit on full data for saving
    
    # Compute metrics for reporting (T026 dependency)
    logger.info("Computing metrics...")
    gb_metrics = compute_metrics(gb_model, X, y)
    mlp_metrics = compute_metrics(mlp_model, X, y)
    
    # Train dummy baseline for comparison (T027b dependency)
    logger.info("Training dummy baseline...")
    dummy_model = train_dummy_baseline(X, y)
    dummy_model.fit(X, y)
    dummy_metrics = compute_metrics(dummy_model, X, y)
    
    # Save models to artifacts directory
    artifacts_dir = Path("models/artifacts")
    
    gb_path = save_model(gb_model, "gradient_boosting", artifacts_dir / "gradient_boosting.pkl")
    mlp_path = save_model(mlp_model, "mlp", artifacts_dir / "mlp.pkl")
    
    # Save metrics to JSON (T026)
    metrics_report = {
        "gradient_boosting": gb_metrics,
        "mlp": mlp_metrics,
        "dummy_baseline": dummy_metrics,
        "best_model": "gradient_boosting" if gb_metrics['mean_r2'] > mlp_metrics['mean_r2'] else "mlp"
    }
    
    metrics_path = Path("results/reports/model_metrics.json")
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics_report, f, indent=2)
    
    logger.info(f"Metrics saved to {metrics_path}")
    
    # Update state.yaml
    state = load_state()
    state['artifacts']['models'] = {
        'gradient_boosting': {
            'path': str(gb_path),
            'hash': compute_file_hash(gb_path)
        },
        'mlp': {
            'path': str(mlp_path),
            'hash': compute_file_hash(mlp_path)
        }
    }
    state['artifacts']['metrics_report'] = {
        'path': str(metrics_path),
        'hash': compute_file_hash(metrics_path)
    }
    update_state(state)
    
    logger.info("T025 completed successfully")
    return True

if __name__ == "__main__":
    main()