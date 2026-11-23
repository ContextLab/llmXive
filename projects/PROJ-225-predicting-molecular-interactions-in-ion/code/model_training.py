import pandas as pd
import joblib
import os
import logging
import time
import signal
from typing import Tuple, Dict, Any, Optional
from sklearn.model_selection import train_test_split
import xgboost as xgb
import optuna
from optuna.trial import Trial

# Import from local modules using absolute imports to avoid relative import errors
import config
from utils import setup_logging

# Setup logging
logger = setup_logging(__name__)

# Custom exception classes (defined here to ensure they are available if config is missing them)
class DataIngestionError(Exception):
    pass

class ModelTrainingError(Exception):
    pass

class AnalysisError(Exception):
    pass

# Load configuration
load_config = config.load_config if hasattr(config, 'load_config') else lambda: {}
TRIAL_TIMEOUT = getattr(config, 'TRIAL_TIMEOUT', 300)

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def run_with_timeout(func, timeout=None):
    """
    MEMORY-SAFE TIMEOUT wrapper using signal module.
    Kills the current process if the function exceeds the timeout.
    Does NOT use multiprocessing to avoid memory overhead.
    
    Args:
        func: The function to execute.
        timeout: Timeout in seconds (defaults to config.TRIAL_TIMEOUT).
    
    Returns:
        The result of the function if it completes within the timeout.
    
    Raises:
        TimeoutError: If the function exceeds the timeout.
    """
    if timeout is None:
        timeout = TRIAL_TIMEOUT
    
    # Set the signal handler
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    try:
        result = func()
        # Cancel the alarm if successful
        signal.alarm(0)
        return result
    except TimeoutError:
        signal.alarm(0)
        # Log the specific timeout event for the trial if context allows
        # We catch the error here and re-raise or handle as needed by the caller
        raise TimeoutError(f"Function timed out after {timeout} seconds")

def stratified_split(df, target_col, structural_family_col):
    """
    Splits the dataframe into train, validation, and test sets with stratification.
    Ratios are defined in config.
    """
    try:
        train_ratio = config.TRAIN_RATIO
        val_ratio = config.VAL_RATIO
        test_ratio = config.TEST_RATIO
        
        # First split: train vs (val + test)
        train_df, temp_df = train_test_split(
            df, 
            train_size=train_ratio, 
            stratify=df[structural_family_col], 
            random_state=config.SEED
        )
        
        # Second split: val vs test
        # Calculate relative ratios for the second split
        remaining_ratio = 1.0 - train_ratio
        val_ratio_rel = val_ratio / remaining_ratio
        
        val_df, test_df = train_test_split(
            temp_df, 
            train_size=val_ratio_rel, 
            stratify=temp_df[structural_family_col], 
            random_state=config.SEED
        )
        
        logger.info(f"Stratified split completed. Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
        return train_df, val_df, test_df
    except Exception as e:
        logger.error(f"Stratified split failed: {e}")
        raise ModelTrainingError(f"Stratified split failed: {e}")

def save_splits(train_df, val_df, test_df):
    """Saves the split dataframes to parquet files."""
    os.makedirs('data/processed', exist_ok=True)
    train_df.to_parquet('data/processed/train.parquet')
    val_df.to_parquet('data/processed/val.parquet')
    test_df.to_parquet('data/processed/test.parquet')
    logger.info("Split data saved to data/processed/")

def optuna_objective(trial: Trial, model_type: str, train_df: pd.DataFrame, val_df: pd.DataFrame):
    """
    Optuna objective function for hyperparameter optimization.
    """
    # Define search space based on model type
    param_distributions = {
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'gamma': trial.suggest_float('gamma', 0, 10),
        'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True)
    }
    
    # Prepare data
    # Assuming target column is passed or derived from model_type
    # For this generic objective, we assume the caller passes the correct target column name
    # or we derive it. Since this is a generic objective, we'll assume the target is passed via context
    # or we need to handle it differently. 
    # For now, let's assume the target is passed as part of the model_type or a separate arg.
    # To make this work with the existing signature, we'll assume the target is 'total_energy' for now
    # or we need to refactor. Let's assume the target is passed in the trial's context or we use a global.
    # Actually, the signature is fixed. We need to know the target.
    # Let's assume the target is derived from model_type: e.g., 'electrostatic_energy' for 'electrostatic'
    if model_type == 'electrostatic':
        target_col = 'electrostatic_energy'
    elif model_type == 'dispersion':
        target_col = 'dispersion_energy'
    elif model_type == 'hbond':
        target_col = 'hbond_energy'
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    X_train = train_df.drop(columns=[target_col])
    y_train = train_df[target_col]
    X_val = val_df.drop(columns=[target_col])
    y_val = val_df[target_col]
    
    model = xgb.XGBRegressor(**param_distributions)
    
    try:
        model.fit(X_train, y_train)
        y_pred = model.predict(X_val)
        mae = ((y_pred - y_val) ** 2).mean() ** 0.5
        logger.info(f"Trial {trial.number}: MAE = {mae:.4f}")
        return mae
    except Exception as e:
        logger.warning(f"Trial {trial.number} failed with error: {e}")
        return float('inf')

def run_optuna_study(model_type: str, train_df: pd.DataFrame, val_df: pd.DataFrame):
    """
    Runs an Optuna study for hyperparameter optimization with timeout handling.
    """
    study = optuna.create_study(direction='minimize')
    
    def objective_wrapper(trial):
        return optuna_objective(trial, model_type, train_df, val_df)
    
    # Wrap the study optimization with timeout
    # Note: Optuna's optimize method runs the objective multiple times.
    # We need to handle timeout per trial.
    # Since run_with_timeout wraps a single function call, we can wrap the objective itself
    # but Optuna handles trials internally. 
    # Instead, we can set the timeout in the optimize method.
    # But the task requires using signal.alarm for a memory-safe timeout per trial.
    # We can wrap the objective call inside Optuna's trial handling.
    # However, Optuna's optimize method has a timeout argument for the whole study.
    # To implement per-trial timeout with signal, we need to modify the objective.
    # But signal.alarm is global and can interfere with Optuna's internal timing.
    # A safer approach for per-trial timeout in Optuna is to use the timeout argument in optimize
    # and rely on Optuna's internal handling, but the task specifically asks for signal.
    # Let's try to wrap the objective in a way that respects signal.
    # We can create a custom objective that wraps the original one with run_with_timeout.
    
    def safe_objective(trial):
        try:
            return run_with_timeout(lambda: optuna_objective(trial, model_type, train_df, val_df), timeout=TRIAL_TIMEOUT)
        except TimeoutError:
            logger.warning(f"Trial {trial.number} terminated by timeout after {TRIAL_TIMEOUT} seconds")
            return float('inf')
    
    study.optimize(safe_objective, n_trials=config.MAX_TRIALS, timeout=None)
    
    logger.info(f"Study completed. Best MAE: {study.best_value:.4f}")
    return study

def train_electrostatic_model(train_df: pd.DataFrame, val_df: pd.DataFrame):
    """
    Trains the electrostatic energy model with timeout handling.
    """
    logger.info("Starting training for electrostatic model...")
    try:
        # Wrap the training in a timeout
        def train_func():
            study = run_optuna_study('electrostatic', train_df, val_df)
            best_params = study.best_params
            model = xgb.XGBRegressor(**best_params)
            # Retrain on full train+val set? Or just return the best model from study?
            # Usually, we retrain on the best params on the full training set.
            # But for simplicity, we'll return the study's best trial's model if we stored it.
            # Alternatively, we retrain.
            X_train = train_df.drop(columns=['electrostatic_energy'])
            y_train = train_df['electrostatic_energy']
            model.fit(X_train, y_train)
            return model, study.best_value, best_params
        
        model, best_value, best_params = run_with_timeout(train_func, timeout=TRIAL_TIMEOUT)
        logger.info(f"Electrostatic model trained. Best MAE: {best_value:.4f}")
        return model, best_value, best_params
    except TimeoutError:
        logger.error("Electrostatic model training timed out.")
        raise ModelTrainingError("Electrostatic model training timed out.")

def train_dispersion_model(train_df: pd.DataFrame, val_df: pd.DataFrame):
    """
    Trains the dispersion energy model with timeout handling.
    """
    logger.info("Starting training for dispersion model...")
    try:
        def train_func():
            study = run_optuna_study('dispersion', train_df, val_df)
            best_params = study.best_params
            model = xgb.XGBRegressor(**best_params)
            X_train = train_df.drop(columns=['dispersion_energy'])
            y_train = train_df['dispersion_energy']
            model.fit(X_train, y_train)
            return model, study.best_value, best_params
        
        model, best_value, best_params = run_with_timeout(train_func, timeout=TRIAL_TIMEOUT)
        logger.info(f"Dispersion model trained. Best MAE: {best_value:.4f}")
        return model, best_value, best_params
    except TimeoutError:
        logger.error("Dispersion model training timed out.")
        raise ModelTrainingError("Dispersion model training timed out.")

def train_hbond_model(train_df: pd.DataFrame, val_df: pd.DataFrame):
    """
    Trains the H-bond energy model with timeout handling.
    """
    logger.info("Starting training for H-bond model...")
    try:
        def train_func():
            study = run_optuna_study('hbond', train_df, val_df)
            best_params = study.best_params
            model = xgb.XGBRegressor(**best_params)
            X_train = train_df.drop(columns=['hbond_energy'])
            y_train = train_df['hbond_energy']
            model.fit(X_train, y_train)
            return model, study.best_value, best_params
        
        model, best_value, best_params = run_with_timeout(train_func, timeout=TRIAL_TIMEOUT)
        logger.info(f"H-bond model trained. Best MAE: {best_value:.4f}")
        return model, best_value, best_params
    except TimeoutError:
        logger.error("H-bond model training timed out.")
        raise ModelTrainingError("H-bond model training timed out.")

def save_models(models, path_prefix):
    """Saves the trained models to disk."""
    os.makedirs('models', exist_ok=True)
    for name, model in models.items():
        path = f'{path_prefix}_{name}.pkl'
        joblib.dump(model, path)
        logger.info(f"Saved model {name} to {path}")

def check_energy_consistency(predictions, total_sapt_targets, tolerance=0.1):
    """
    Checks if the sum of predicted energy components is consistent with the total SAPT energy.
    """
    predicted_total = sum(predictions.values())
    error = abs(predicted_total - total_sapt_targets)
    if error > tolerance:
        logger.warning(f"Energy inconsistency detected: {error:.4f} > {tolerance}")
        return False
    return True

def main():
    """
    Main entry point for model training.
    """
    logger.info("Starting model training pipeline...")
    
    # Load data (assuming data is already split and saved)
    try:
        train_df = pd.read_parquet('data/processed/train.parquet')
        val_df = pd.read_parquet('data/processed/val.parquet')
    except FileNotFoundError:
        logger.error("Training data not found. Please run data ingestion first.")
        raise
    
    # Train models
    models = {}
    try:
        models['electrostatic'], _, _ = train_electrostatic_model(train_df, val_df)
        models['dispersion'], _, _ = train_dispersion_model(train_df, val_df)
        models['hbond'], _, _ = train_hbond_model(train_df, val_df)
    except ModelTrainingError as e:
        logger.error(f"Model training failed: {e}")
        raise
    
    # Save models
    save_models(models, 'models/model')
    logger.info("Model training completed successfully.")

if __name__ == '__main__':
    main()