import pandas as pd
import joblib
import os
import logging
import time
from typing import Tuple, Dict, Any, Optional
import config
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import optuna

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def stratified_split(df: pd.DataFrame, target_col: str, structural_family_col: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split data into train, validation, and test sets using stratification.
    """
    # Handle case where family has < 2 samples
    family_counts = df[structural_family_col].value_counts()
    valid_families = family_counts[family_counts >= 2].index
    df_filtered = df[df[structural_family_col].isin(valid_families)]
    
    if len(valid_families) < len(family_counts):
        logger.warning(f"Stratification failure: Removed {set(family_counts.index) - set(valid_families)} families with < 2 samples.")
    
    train_val, test = train_test_split(
        df_filtered, 
        test_size=config.TEST_RATIO, 
        stratify=df_filtered[structural_family_col],
        random_state=config.SEED
    )
    
    train, val = train_test_split(
        train_val, 
        test_size=config.VAL_RATIO / (1 - config.TRAIN_RATIO), 
        stratify=train_val[structural_family_col],
        random_state=config.SEED
    )
    
    logger.info(f"Split sizes: Train={len(train)}, Val={len(val)}, Test={len(test)}")
    logger.info(f"Family distribution in Train: {train[structural_family_col].value_counts().to_dict()}")
    
    return train, val, test

def save_splits(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame) -> None:
    """Save splits to parquet files."""
    os.makedirs("data/processed", exist_ok=True)
    train_df.to_parquet("data/processed/train.parquet", index=False)
    val_df.to_parquet("data/processed/val.parquet", index=False)
    test_df.to_parquet("data/processed/test.parquet", index=False)
    logger.info("Splits saved.")

def optuna_objective(trial, model_type: str, train_df: pd.DataFrame, val_df: pd.DataFrame) -> float:
    """Optuna objective function for XGBoost hyperparameter optimization."""
    params = {
        'objective': 'reg:squarederror',
        'eval_metric': 'mae',
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'random_state': config.SEED
    }
    
    X_train = train_df.drop(columns=['electrostatic_energy', 'dispersion_energy', 'hbond_energy', 'cation_id', 'anion_id', 'structural_family', 'smiles_cation', 'smiles_anion'])
    y_train = train_df[model_type]
    X_val = val_df.drop(columns=['electrostatic_energy', 'dispersion_energy', 'hbond_energy', 'cation_id', 'anion_id', 'structural_family', 'smiles_cation', 'smiles_anion'])
    y_val = val_df[model_type]
    
    model = XGBRegressor(**params)
    
    try:
        model.fit(X_train, y_train)
        preds = model.predict(X_val)
        mae = ((preds - y_val) ** 2).mean() ** 0.5
        logger.info(f"Trial {trial.number}: MAE = {mae:.4f}")
        return mae
    except Exception as e:
        logger.warning(f"Trial {trial.number} failed: {e}")
        return float('inf')

def run_optuna_study(model_type: str, train_df: pd.DataFrame, val_df: pd.DataFrame) -> optuna.Study:
    """Run Optuna study for a specific model type."""
    study = optuna.create_study(direction='minimize')
    try:
        study.optimize(lambda trial: optuna_objective(trial, model_type, train_df, val_df), 
                       n_trials=config.MAX_TRIALS, 
                       timeout=config.TRIAL_TIMEOUT)
    except Exception as e:
        logger.warning(f"Optuna study interrupted: {e}")
    
    logger.info(f"Study completed. Best MAE: {study.best_value:.4f}")
    return study

def train_electrostatic_model(train_df: pd.DataFrame, val_df: pd.DataFrame) -> XGBRegressor:
    """Train electrostatic energy model."""
    study = run_optuna_study('electrostatic_energy', train_df, val_df)
    model = XGBRegressor(**study.best_params)
    X_train = train_df.drop(columns=['electrostatic_energy', 'dispersion_energy', 'hbond_energy', 'cation_id', 'anion_id', 'structural_family', 'smiles_cation', 'smiles_anion'])
    y_train = train_df['electrostatic_energy']
    model.fit(X_train, y_train)
    return model

def train_dispersion_model(train_df: pd.DataFrame, val_df: pd.DataFrame) -> XGBRegressor:
    """Train dispersion energy model."""
    study = run_optuna_study('dispersion_energy', train_df, val_df)
    model = XGBRegressor(**study.best_params)
    X_train = train_df.drop(columns=['electrostatic_energy', 'dispersion_energy', 'hbond_energy', 'cation_id', 'anion_id', 'structural_family', 'smiles_cation', 'smiles_anion'])
    y_train = train_df['dispersion_energy']
    model.fit(X_train, y_train)
    return model

def train_hbond_model(train_df: pd.DataFrame, val_df: pd.DataFrame) -> XGBRegressor:
    """Train H-bond energy model."""
    study = run_optuna_study('hbond_energy', train_df, val_df)
    model = XGBRegressor(**study.best_params)
    X_train = train_df.drop(columns=['electrostatic_energy', 'dispersion_energy', 'hbond_energy', 'cation_id', 'anion_id', 'structural_family', 'smiles_cation', 'smiles_anion'])
    y_train = train_df['hbond_energy']
    model.fit(X_train, y_train)
    return model

def save_models(models: Dict[str, XGBRegressor], path_prefix: str) -> None:
    """Save trained models."""
    os.makedirs("models", exist_ok=True)
    for name, model in models.items():
        joblib.dump(model, f"{path_prefix}_{name}.pkl")
    logger.info("Models saved.")

def check_energy_consistency(predictions: pd.DataFrame, total_sapt_targets: pd.Series, tolerance: float = 0.1) -> bool:
    """Check if sum of predictions is consistent with total energy."""
    total_pred = predictions.sum(axis=1)
    diff = (total_pred - total_sapt_targets).abs()
    return (diff <= tolerance).all()

def main():
    """Main entry point for model training."""
    # Load data
    train_df = pd.read_parquet("data/processed/train.parquet")
    val_df = pd.read_parquet("data/processed/val.parquet")
    test_df = pd.read_parquet("data/processed/test.parquet")
    
    models = {
        'electrostatic': train_electrostatic_model(train_df, val_df),
        'dispersion': train_dispersion_model(train_df, val_df),
        'hbond': train_hbond_model(train_df, val_df)
    }
    
    save_models(models, "models/xgb_model")
    logger.info("Model training completed.")

if __name__ == "__main__":
    main()
