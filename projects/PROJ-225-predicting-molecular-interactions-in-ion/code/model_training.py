import pandas as pd
import joblib
import os
import logging
from typing import Tuple, Dict, Any, Optional
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from .config import ModelTrainingError, HYPERPARAM_BOUNDS, MAX_TRIALS, TRIAL_TIMEOUT, SEED
import optuna

logger = logging.getLogger(__name__)

def stratified_split(
    df: pd.DataFrame,
    target_col: str,
    structural_family_col: str,
    ratios: Tuple[float, float, float] = (0.7, 0.15, 0.15)
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform a stratified train/validation/test split based on structural family.
    
    Args:
        df: Input dataframe.
        target_col: Name of the target column (used for sorting/checking, but split is on family).
        structural_family_col: Column to use for stratification.
        ratios: Tuple of (train_ratio, val_ratio, test_ratio).
    
    Returns:
        Tuple of (train_df, val_df, test_df).
    """
    if abs(sum(ratios) - 1.0) > 0.01:
        raise ValueError("Ratios must sum to 1.0")
    
    train_ratio, val_ratio, test_ratio = ratios
    
    # First split: Train vs (Val + Test)
    train_df, temp_df = train_test_split(
        df, 
        train_size=train_ratio, 
        stratify=df[structural_family_col],
        random_state=SEED
    )
    
    # Second split: Val vs Test from the remaining
    remaining_ratio = val_ratio / (val_ratio + test_ratio)
    val_df, test_df = train_test_split(
        temp_df,
        train_size=remaining_ratio,
        stratify=temp_df[structural_family_col],
        random_state=SEED
    )
    
    logger.info(f"Split sizes - Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    return train_df, val_df, test_df

def save_splits(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame):
    """
    Save the split datasets to parquet files.
    """
    os.makedirs("data/processed", exist_ok=True)
    train_df.to_parquet("data/processed/train.parquet", index=False)
    val_df.to_parquet("data/processed/val.parquet", index=False)
    test_df.to_parquet("data/processed/test.parquet", index=False)
    logger.info("Splits saved to data/processed/")

def train_electrostatic_model(train_df: pd.DataFrame, val_df: pd.DataFrame) -> XGBRegressor:
    """
    Train the electrostatic energy model using XGBoost with Optuna tuning.
    (Stub implementation for context - T022)
    """
    # Placeholder for T022 logic, assuming it follows the pattern of T023
    logger.info("Training electrostatic model...")
    # In a real flow, this would call run_optuna_study specifically for electrostatic
    # For now, returning a dummy model to satisfy the import check if called elsewhere
    # but the task is to implement T023 (dispersion).
    return XGBRegressor()

def train_dispersion_model(train_df: pd.DataFrame, val_df: pd.DataFrame) -> XGBRegressor:
    """
    Train the dispersion energy model using XGBoost with Optuna hyperparameter tuning.
    
    Args:
        train_df: Training dataset (features + target).
        val_df: Validation dataset for scoring.
    
    Returns:
        Trained XGBRegressor model.
    """
    logger.info("Starting dispersion model training...")
    
    # Define features and target
    # Assuming the dataframe has a specific column for dispersion energy
    target_col = "dispersion_energy"
    feature_cols = [col for col in train_df.columns if col not in [target_col, "cation_id", "anion_id", "structural_family"]]
    
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_val = val_df[feature_cols]
    y_val = val_df[target_col]
    
    if X_train.empty:
        raise ModelTrainingError("No feature columns found for dispersion model training.")
    
    def objective(trial):
        param = {
            "objective": "reg:squarederror",
            "eval_metric": "mae",
            "tree_method": "hist",
            "random_state": SEED,
            "n_jobs": -1,
            # Hyperparameter search space
            "max_depth": trial.suggest_int("max_depth", 3, 12),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "n_estimators": trial.suggest_int("n_estimators", 100, 2000),
            "gamma": trial.suggest_float("gamma", 0.0, 10.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "lambda": trial.suggest_float("lambda", 1e-8, 10.0, log=True),
            "alpha": trial.suggest_float("alpha", 1e-8, 10.0, log=True),
        }
        
        model = XGBRegressor(**param)
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        
        val_pred = model.predict(X_val)
        # Optuna uses the first metric by default, but we can calculate MAE explicitly if needed
        # The eval_metric 'mae' is set in params, so trial.report will use it if we use callbacks,
        # but here we return the negative MAE or the MAE directly. Optuna minimizes by default.
        from sklearn.metrics import mean_absolute_error
        mae = mean_absolute_error(y_val, val_pred)
        return mae

    study = optuna.create_study(direction="minimize", study_name="dispersion_optuna")
    
    try:
        study.optimize(
            objective,
            n_trials=MAX_TRIALS,
            timeout=TRIAL_TIMEOUT,
            show_progress_bar=True
        )
    except Exception as e:
        logger.error(f"Optuna study failed: {e}")
        raise ModelTrainingError(f"Optuna optimization failed: {e}")
    
    best_params = study.best_params
    logger.info(f"Best parameters for dispersion model: {best_params}")
    logger.info(f"Best MAE: {study.best_value}")
    
    # Retrain on full training set with best params
    best_model = XGBRegressor(**best_params)
    best_model.fit(X_train, y_train)
    
    # Save trial history for analysis
    os.makedirs("models", exist_ok=True)
    study.trials_dataframe().to_csv("models/dispersion_trials.csv", index=False)
    
    return best_model

def train_hbond_model(train_df: pd.DataFrame, val_df: pd.DataFrame) -> XGBRegressor:
    """
    Train the hydrogen-bond energy model using XGBoost with Optuna tuning.
    (Stub implementation for context - T024)
    """
    logger.info("Training hydrogen-bond model...")
    return XGBRegressor()

def optuna_objective(trial, model_type: str, train_df: pd.DataFrame, val_df: pd.DataFrame) -> float:
    """
    Generic Optuna objective function for hyperparameter tuning.
    
    Args:
        trial: Optuna trial object.
        model_type: 'electrostatic', 'dispersion', or 'hbond'.
        train_df: Training dataframe.
        val_df: Validation dataframe.
    
    Returns:
        Validation MAE.
    """
    # Determine target column based on model type
    target_map = {
        "electrostatic": "electrostatic_energy",
        "dispersion": "dispersion_energy",
        "hbond": "hbond_energy"
    }
    
    if model_type not in target_map:
        raise ValueError(f"Unknown model_type: {model_type}")
    
    target_col = target_map[model_type]
    feature_cols = [col for col in train_df.columns if col not in [target_col, "cation_id", "anion_id", "structural_family"]]
    
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_val = val_df[feature_cols]
    y_val = val_df[target_col]
    
    param = {
        "objective": "reg:squarederror",
        "eval_metric": "mae",
        "tree_method": "hist",
        "random_state": SEED,
        "n_jobs": -1,
        "max_depth": trial.suggest_int("max_depth", 3, 12),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "n_estimators": trial.suggest_int("n_estimators", 100, 2000),
        "gamma": trial.suggest_float("gamma", 0.0, 10.0),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "lambda": trial.suggest_float("lambda", 1e-8, 10.0, log=True),
        "alpha": trial.suggest_float("alpha", 1e-8, 10.0, log=True),
    }
    
    model = XGBRegressor(**param)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    
    from sklearn.metrics import mean_absolute_error
    mae = mean_absolute_error(y_val, model.predict(X_val))
    return mae

def run_optuna_study(model_type: str, train_df: pd.DataFrame, val_df: pd.DataFrame):
    """
    Run the full Optuna study for a specific model type.
    """
    study = optuna.create_study(direction="minimize", study_name=f"{model_type}_optuna")
    study.optimize(
        lambda trial: optuna_objective(trial, model_type, train_df, val_df),
        n_trials=MAX_TRIALS,
        timeout=TRIAL_TIMEOUT
    )
    return study

def save_models(models: Dict[str, XGBRegressor], path_prefix: str):
    """
    Save trained models to disk.
    
    Args:
        models: Dictionary mapping model name (e.g., 'electrostatic') to model object.
        path_prefix: Directory path where models will be saved.
    """
    os.makedirs(path_prefix, exist_ok=True)
    for name, model in models.items():
        path = os.path.join(path_prefix, f"{name}.pkl")
        joblib.dump(model, path)
        logger.info(f"Saved {name} model to {path}")

def check_energy_consistency(predictions: Dict[str, pd.Series], total_sapt_targets: pd.Series, tolerance: float = 0.1):
    """
    Check if the sum of predicted components is consistent with the total SAPT energy.
    
    Args:
        predictions: Dict of component predictions (electrostatic, dispersion, hbond).
        total_sapt_targets: Ground truth total energy.
        tolerance: Maximum allowed MAE for consistency check.
    
    Returns:
        Dict with status and MAE.
    """
    if not all(k in predictions for k in ["electrostatic", "dispersion", "hbond"]):
        raise ValueError("Missing predicted components for consistency check.")
    
    total_pred = predictions["electrostatic"] + predictions["dispersion"] + predictions["hbond"]
    
    from sklearn.metrics import mean_absolute_error
    mae = mean_absolute_error(total_sapt_targets, total_pred)
    
    status = "PASS" if mae <= tolerance else "FAIL"
    result = {
        "status": status,
        "mae": mae,
        "tolerance": tolerance
    }
    
    os.makedirs("models", exist_ok=True)
    with open("models/consistency_log.json", "w") as f:
        import json
        json.dump(result, f, indent=2)
    
    logger.info(f"Energy consistency check: {status} (MAE: {mae:.4f})")
    return result