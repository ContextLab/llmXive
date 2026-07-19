import pandas as pd
import joblib
import os
import logging
from typing import Tuple, Dict, Any, Optional
from sklearn.model_selection import train_test_split
import xgboost as xgb
import optuna
from .config import ModelTrainingError, load_config
from .utils import setup_logging

# Ensure logging is configured
logger = setup_logging("training")

def stratified_split(
    df: pd.DataFrame,
    target_col: str,
    structural_family_col: str,
    ratios: Tuple[float, float, float] = (0.7, 0.15, 0.15)
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform a stratified split of the dataset based on structural family.
    
    Args:
        df: Input DataFrame
        target_col: Name of the target column (not used for stratification but kept for API)
        structural_family_col: Name of the column to stratify by
        ratios: Tuple of (train_ratio, val_ratio, test_ratio)
    
    Returns:
        Tuple of (train_df, val_df, test_df)
    
    Raises:
        ModelTrainingError: If stratification fails due to empty groups
    """
    train_ratio, val_ratio, test_ratio = ratios
    
    # First split: train vs (val + test)
    train_df, temp_df = train_test_split(
        df,
        train_size=train_ratio,
        stratify=df[structural_family_col],
        random_state=42
    )
    
    # Second split: val vs test from the remaining
    val_ratio_adjusted = val_ratio / (val_ratio + test_ratio)
    val_df, test_df = train_test_split(
        temp_df,
        train_size=val_ratio_adjusted,
        stratify=temp_df[structural_family_col],
        random_state=42
    )
    
    # LOGGING FOR T049: Dataset size and per-family counts
    total_samples = len(df)
    logger.info(f"Total dataset size: {total_samples} IonPairs")
    
    # Count samples per structural family in the full dataset
    family_counts_full = df[structural_family_col].value_counts().to_dict()
    logger.info("Full dataset distribution by Structural Family:")
    for family, count in sorted(family_counts_full.items()):
        logger.info(f"  - {family}: {count} samples")
    
    # Count samples per structural family in the test set (critical for validation)
    family_counts_test = test_df[structural_family_col].value_counts().to_dict()
    logger.info("Test set distribution by Structural Family:")
    for family, count in sorted(family_counts_test.items()):
        logger.info(f"  - {family}: {count} samples")
    
    # Verify no family is empty in the test set
    missing_families = set(family_counts_full.keys()) - set(family_counts_test.keys())
    if missing_families:
        error_msg = f"Stratification failed: The following families are missing from the test set: {missing_families}"
        logger.error(error_msg)
        raise ModelTrainingError(error_msg)
    
    logger.info(f"Split successful: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    
    return train_df, val_df, test_df

def save_splits(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame
) -> None:
    """
    Save the split datasets to parquet files.
    
    Args:
        train_df: Training DataFrame
        val_df: Validation DataFrame
        test_df: Test DataFrame
    """
    os.makedirs("data/processed", exist_ok=True)
    
    train_path = "data/processed/train.parquet"
    val_path = "data/processed/val.parquet"
    test_path = "data/processed/test.parquet"
    
    train_df.to_parquet(train_path, index=False)
    val_df.to_parquet(val_path, index=False)
    test_df.to_parquet(test_path, index=False)
    
    logger.info(f"Saved splits to: {train_path}, {val_path}, {test_path}")

def train_electrostatic_model(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame
) -> xgb.XGBRegressor:
    """
    Train XGBoost model for electrostatic energy prediction.
    
    Args:
        train_df: Training DataFrame
        val_df: Validation DataFrame
    
    Returns:
        Trained XGBRegressor
    """
    feature_cols = [col for col in train_df.columns if col not in 
                   ['cation_id', 'anion_id', 'electrostatic_energy', 'total_energy']]
    
    X_train = train_df[feature_cols]
    y_train = train_df['electrostatic_energy']
    X_val = val_df[feature_cols]
    y_val = val_df['electrostatic_energy']
    
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=100,
        learning_rate=0.1,
        max_depth=6,
        random_state=42
    )
    
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    
    val_mae = model.evaluate(X_val, y_val)
    logger.info(f"Electrostatic model validation MAE: {val_mae}")
    
    return model

def train_dispersion_model(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame
) -> xgb.XGBRegressor:
    """
    Train XGBoost model for dispersion energy prediction.
    
    Args:
        train_df: Training DataFrame
        val_df: Validation DataFrame
    
    Returns:
        Trained XGBRegressor
    """
    feature_cols = [col for col in train_df.columns if col not in 
                   ['cation_id', 'anion_id', 'dispersion_energy', 'total_energy']]
    
    X_train = train_df[feature_cols]
    y_train = train_df['dispersion_energy']
    X_val = val_df[feature_cols]
    y_val = val_df['dispersion_energy']
    
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=100,
        learning_rate=0.1,
        max_depth=6,
        random_state=42
    )
    
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    
    val_mae = model.evaluate(X_val, y_val)
    logger.info(f"Dispersion model validation MAE: {val_mae}")
    
    return model

def train_hbond_model(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame
) -> xgb.XGBRegressor:
    """
    Train XGBoost model for H-bond energy prediction.
    
    Args:
        train_df: Training DataFrame
        val_df: Validation DataFrame
    
    Returns:
        Trained XGBRegressor
    """
    feature_cols = [col for col in train_df.columns if col not in 
                   ['cation_id', 'anion_id', 'hbond_energy', 'total_energy']]
    
    X_train = train_df[feature_cols]
    y_train = train_df['hbond_energy']
    X_val = val_df[feature_cols]
    y_val = val_df['hbond_energy']
    
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=100,
        learning_rate=0.1,
        max_depth=6,
        random_state=42
    )
    
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    
    val_mae = model.evaluate(X_val, y_val)
    logger.info(f"H-bond model validation MAE: {val_mae}")
    
    return model

def optuna_objective(
    trial: optuna.Trial,
    model_type: str,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame
) -> float:
    """
    Optuna objective function for hyperparameter optimization.
    
    Args:
        trial: Optuna trial object
        model_type: Type of model ('electrostatic', 'dispersion', 'hbond')
        train_df: Training DataFrame
        val_df: Validation DataFrame
    
    Returns:
        Validation loss (MAE)
    """
    # Define search space
    params = {
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'n_estimators': trial.suggest_int('n_estimators', 50, 200),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'gamma': trial.suggest_float('gamma', 0, 10),
        'random_state': 42
    }
    
    # Select target column based on model type
    target_map = {
        'electrostatic': 'electrostatic_energy',
        'dispersion': 'dispersion_energy',
        'hbond': 'hbond_energy'
    }
    target_col = target_map[model_type]
    
    feature_cols = [col for col in train_df.columns if col not in 
                   ['cation_id', 'anion_id', target_col, 'total_energy']]
    
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_val = val_df[feature_cols]
    y_val = val_df[target_col]
    
    model = xgb.XGBRegressor(**params, objective='reg:squarederror')
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    
    val_mae = model.evaluate(X_val, y_val)
    return val_mae

def run_optuna_study() -> Dict[str, Any]:
    """
    Run Optuna hyperparameter optimization study.
    
    Returns:
        Dictionary containing best parameters and study results
    """
    config = load_config()
    n_trials = config.get('MAX_TRIALS', 60)
    timeout = config.get('TRIAL_TIMEOUT', 300)
    
    # Load data
    unified_df = pd.read_parquet("data/processed/unified_dataset.parquet")
    train_df, val_df, _ = stratified_split(
        unified_df,
        target_col='total_energy',
        structural_family_col='structural_family'
    )
    
    results = {}
    
    for model_type in ['electrostatic', 'dispersion', 'hbond']:
        logger.info(f"Starting Optuna study for {model_type} model")
        study = optuna.create_study(direction='minimize')
        
        study.optimize(
            lambda trial: optuna_objective(trial, model_type, train_df, val_df),
            n_trials=n_trials,
            timeout=timeout
        )
        
        results[model_type] = {
            'best_params': study.best_params,
            'best_value': study.best_value,
            'n_trials': len(study.trials)
        }
        
        logger.info(f"{model_type} - Best MAE: {study.best_value}")
        logger.info(f"{model_type} - Best params: {study.best_params}")
    
    # Save best parameters
    os.makedirs("models", exist_ok=True)
    with open("models/hyperparams.json", "w") as f:
        import json
        json.dump(results, f, indent=2)
    
    logger.info("Optuna study completed and saved to models/hyperparams.json")
    return results

def save_models(
    models: Dict[str, Any],
    path_prefix: str = "models"
) -> None:
    """
    Save trained models to disk.
    
    Args:
        models: Dictionary of model names to model objects
        path_prefix: Directory path prefix for saving
    """
    os.makedirs(path_prefix, exist_ok=True)
    
    for name, model in models.items():
        model_path = os.path.join(path_prefix, f"{name}.pkl")
        joblib.dump(model, model_path)
        logger.info(f"Saved {name} model to {model_path}")

def check_energy_consistency(
    predictions: pd.Series,
    total_sapt_targets: pd.Series,
    tolerance: float = 0.1
) -> Dict[str, Any]:
    """
    Check if sum of component predictions approximates total energy target.
    
    Args:
        predictions: Series of component predictions (should be summed before calling)
        total_sapt_targets: Series of total energy targets
        tolerance: Tolerance in kcal/mol
    
    Returns:
        Dictionary with pass/fail status and details
    """
    # predictions should already be the sum of components
    mae = (predictions - total_sapt_targets).abs().mean()
    passed = mae <= tolerance
    
    result = {
        'mae': float(mae),
        'tolerance': tolerance,
        'passed': passed,
        'status': 'PASS' if passed else 'FAIL'
    }
    
    os.makedirs("models", exist_ok=True)
    with open("models/consistency_log.json", "w") as f:
        import json
        json.dump(result, f, indent=2)
    
    logger.info(f"Energy consistency check: {result['status']} (MAE={mae:.4f})")
    return result