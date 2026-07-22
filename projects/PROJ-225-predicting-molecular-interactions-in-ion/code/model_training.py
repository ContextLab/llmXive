import pandas as pd
import joblib
import os
import logging
from typing import Tuple, Dict, Any, Optional
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import xgboost as xgb
import optuna
import numpy as np

# Imports
try:
    from config import ModelTrainingError, load_config
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from config import ModelTrainingError, load_config

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.FileHandler('logs/training.log')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def stratified_split(df: pd.DataFrame, target_col: str, structural_family_col: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split data into train/val/test with stratification by structural family.
    Logs dataset sizes and family distribution.
    """
    logger.info(f"Performing stratified split on {structural_family_col}")
    
    # Check for small families
    family_counts = df[structural_family_col].value_counts()
    small_families = family_counts[family_counts < 2].index.tolist()
    if small_families:
        logger.warning(f"Removing small families (<2 samples) from stratification: {small_families}")
        df = df[~df[structural_family_col].isin(small_families)]

    train_val, test = train_test_split(
        df, test_size=0.15, random_state=42, stratify=df[structural_family_col]
    )
    train, val = train_test_split(
        train_val, test_size=0.15/(0.7+0.15), random_state=42, stratify=train_val[structural_family_col]
    )
    
    # Log details
    logger.info(f"Split sizes: Train={len(train)}, Val={len(val)}, Test={len(test)}")
    logger.info(f"Family distribution in Train:\n{train[structural_family_col].value_counts()}")
    
    return train, val, test

def save_splits(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame):
    """Save splits to parquet files."""
    os.makedirs('data/processed', exist_ok=True)
    train_df.to_parquet('data/processed/train.parquet')
    val_df.to_parquet('data/processed/val.parquet')
    test_df.to_parquet('data/processed/test.parquet')
    logger.info("Train/Val/Test splits saved.")

def train_electrostatic_model(train_df: pd.DataFrame, val_df: pd.DataFrame) -> xgb.XGBRegressor:
    """Train XGBoost model for electrostatic energy."""
    logger.info("Training Electrostatic Energy Model...")
    feature_cols = [c for c in train_df.columns if c not in ['cation_id', 'anion_id', 'electrostatic_energy', 'structural_family']]
    
    X_train = train_df[feature_cols]
    y_train = train_df['electrostatic_energy']
    X_val = val_df[feature_cols]
    y_val = val_df['electrostatic_energy']
    
    model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    
    mae = mean_absolute_error(y_val, model.predict(X_val))
    logger.info(f"Electrostatic Model Validation MAE: {mae:.4f}")
    
    return model

def train_dispersion_model(train_df: pd.DataFrame, val_df: pd.DataFrame) -> xgb.XGBRegressor:
    """Train XGBoost model for dispersion energy."""
    logger.info("Training Dispersion Energy Model...")
    feature_cols = [c for c in train_df.columns if c not in ['cation_id', 'anion_id', 'dispersion_energy', 'structural_family']]
    
    X_train = train_df[feature_cols]
    y_train = train_df['dispersion_energy']
    X_val = val_df[feature_cols]
    y_val = val_df['dispersion_energy']
    
    model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    
    mae = mean_absolute_error(y_val, model.predict(X_val))
    logger.info(f"Dispersion Model Validation MAE: {mae:.4f}")
    
    return model

def train_hbond_model(train_df: pd.DataFrame, val_df: pd.DataFrame) -> xgb.XGBRegressor:
    """Train XGBoost model for H-bond energy."""
    logger.info("Training H-Bond Energy Model...")
    feature_cols = [c for c in train_df.columns if c not in ['cation_id', 'anion_id', 'hbond_energy', 'structural_family']]
    
    X_train = train_df[feature_cols]
    y_train = train_df['hbond_energy']
    X_val = val_df[feature_cols]
    y_val = val_df['hbond_energy']
    
    model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    
    mae = mean_absolute_error(y_val, model.predict(X_val))
    logger.info(f"H-Bond Model Validation MAE: {mae:.4f}")
    
    return model

def optuna_objective(trial: optuna.Trial, model_type: str, train_df: pd.DataFrame, val_df: pd.DataFrame) -> float:
    """Optuna objective function for hyperparameter optimization."""
    # Hyperparameter search space
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 50, 500),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'random_state': 42
    }
    
    feature_cols = [c for c in train_df.columns if c not in ['cation_id', 'anion_id', 'structural_family', 'electrostatic_energy', 'dispersion_energy', 'hbond_energy']]
    # Select target based on model_type
    target_map = {'electrostatic': 'electrostatic_energy', 'dispersion': 'dispersion_energy', 'hbond': 'hbond_energy'}
    target = target_map.get(model_type, 'electrostatic_energy')
    
    X_train = train_df[feature_cols]
    y_train = train_df[target]
    X_val = val_df[feature_cols]
    y_val = val_df[target]
    
    model = xgb.XGBRegressor(**params)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    
    mae = mean_absolute_error(y_val, model.predict(X_val))
    return mae

def run_optuna_study():
    """Run Optuna study for hyperparameter optimization."""
    logger.info("Starting Optuna Hyperparameter Study...")
    # Load splits
    train_df = pd.read_parquet('data/processed/train.parquet')
    val_df = pd.read_parquet('data/processed/val.parquet')
    
    study = optuna.create_study(direction='minimize', study_name='energy_prediction')
    study.optimize(lambda trial: optuna_objective(trial, 'electrostatic', train_df, val_df), n_trials=10, timeout=60)
    
    logger.info(f"Best trial: {study.best_trial.params}")
    logger.info(f"Best MAE: {study.best_value}")
    return study

def check_energy_consistency(predictions: Dict[str, np.ndarray], total_sapt_targets: np.ndarray, tolerance: float = 0.1):
    """Check if sum of component predictions matches total energy within tolerance."""
    total_pred = sum(predictions.values())
    diff = np.abs(total_pred - total_sapt_targets)
    compliant = np.mean(diff < tolerance)
    logger.info(f"Energy Consistency Check: {compliant*100:.2f}% within {tolerance} kcal/mol tolerance")
    return compliant

def save_models(models: Dict[str, Any], path_prefix: str):
    """Save trained models."""
    os.makedirs('models', exist_ok=True)
    for name, model in models.items():
        path = f"{path_prefix}_{name}.pkl"
        joblib.dump(model, path)
        logger.info(f"Saved model {name} to {path}")

def main():
    """Main entry point for model training."""
    logger.info("Starting Model Training Pipeline")
    
    # Load unified dataset
    df = pd.read_parquet('data/processed/unified_dataset.parquet')
    
    # Split
    train, val, test = stratified_split(df, 'electrostatic_energy', 'structural_family')
    save_splits(train, val, test)
    
    # Train models
    models = {
        'electrostatic': train_electrostatic_model(train, val),
        'dispersion': train_dispersion_model(train, val),
        'hbond': train_hbond_model(train, val)
    }
    
    # Run Optuna (limited trials for speed)
    run_optuna_study()
    
    # Save models
    save_models(models, 'models/energy_models')
    
    logger.info("Model Training Pipeline Complete.")

if __name__ == "__main__":
    main()
