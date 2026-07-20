"""
Trainer module for hyperparameter tuning using Optuna.

Implements k-fold stratified cross-validation with Optuna for XGBoost and Random Forest.
Tuned parameters: n_estimators, max_depth, learning_rate.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union, List
import numpy as np
import pandas as pd
import optuna
from optuna.trial import Trial
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import r2_score, make_scorer
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from code.logging_config import get_logger
from code.models.augmented import train_augmented_model

# Initialize logger
logger = get_logger(__name__)

def objective_rf(trial: Trial, X: np.ndarray, y: np.ndarray, cv: StratifiedKFold) -> float:
    """
    Objective function for Random Forest hyperparameter tuning.
    
    Args:
        trial: Optuna trial object.
        X: Feature matrix.
        y: Target vector.
        cv: Cross-validation splitter.
        
    Returns:
        Mean R2 score across CV folds.
    """
    # Suggest hyperparameters
    n_estimators = trial.suggest_int('n_estimators', 50, 500, step=50)
    max_depth = trial.suggest_int('max_depth', 3, 15)
    min_samples_split = trial.suggest_int('min_samples_split', 2, 20)
    min_samples_leaf = trial.suggest_int('min_samples_leaf', 1, 10)
    max_features = trial.suggest_categorical('max_features', ['sqrt', 'log2', None])
    
    # Create model
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        min_samples_leaf=min_samples_leaf,
        max_features=max_features,
        random_state=42,
        n_jobs=-1
    )
    
    # Evaluate using cross-validation
    # Using negative MSE because sklearn's cross_val_score maximizes
    scores = cross_val_score(model, X, y, cv=cv, scoring='r2', n_jobs=-1)
    mean_r2 = np.mean(scores)
    
    return mean_r2

def objective_xgb(trial: Trial, X: np.ndarray, y: np.ndarray, cv: StratifiedKFold) -> float:
    """
    Objective function for XGBoost hyperparameter tuning.
    
    Args:
        trial: Optuna trial object.
        X: Feature matrix.
        y: Target vector.
        cv: Cross-validation splitter.
        
    Returns:
        Mean R2 score across CV folds.
    """
    # Suggest hyperparameters
    n_estimators = trial.suggest_int('n_estimators', 50, 500, step=50)
    max_depth = trial.suggest_int('max_depth', 3, 10)
    learning_rate = trial.suggest_float('learning_rate', 0.01, 0.3, log=True)
    subsample = trial.suggest_float('subsample', 0.6, 1.0)
    colsample_bytree = trial.suggest_float('colsample_bytree', 0.6, 1.0)
    gamma = trial.suggest_float('gamma', 0, 10)
    
    # Create model
    model = xgb.XGBRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=subsample,
        colsample_bytree=colsample_bytree,
        gamma=gamma,
        random_state=42,
        n_jobs=-1,
        verbosity=0
    )
    
    # Evaluate using cross-validation
    scores = cross_val_score(model, X, y, cv=cv, scoring='r2', n_jobs=-1)
    mean_r2 = np.mean(scores)
    
    return mean_r2

def tune_hyperparameters(
    X: np.ndarray,
    y: np.ndarray,
    model_type: str = 'xgb',
    n_trials: int = 50,
    n_splits: int = 5,
    study_name: Optional[str] = None,
    storage: Optional[str] = None
) -> Tuple[Dict[str, Any], optuna.Study]:
    """
    Perform hyperparameter tuning using Optuna with k-fold stratified CV.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        model_type: Type of model to tune ('xgb' or 'rf').
        n_trials: Number of optimization trials.
        n_splits: Number of CV folds.
        study_name: Optional name for the Optuna study.
        storage: Optional storage URI for the study.
        
    Returns:
        Tuple of (best_params, study) where best_params is the dictionary of
        best hyperparameters and study is the Optuna study object.
        
    Raises:
        ValueError: If model_type is not 'xgb' or 'rf'.
    """
    logger.info(f"Starting hyperparameter tuning for {model_type} model with {n_trials} trials")
    
    # Create stratified k-fold splitter
    # For regression, we bin the target variable to create stratified folds
    try:
        # Create bins based on percentiles for stratification
        y_bins = np.digitize(y, np.percentile(y, np.linspace(0, 100, n_splits + 1)[1:-1]))
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    except Exception as e:
        logger.warning(f"Stratified CV failed: {e}, falling back to standard KFold")
        from sklearn.model_selection import KFold
        cv = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        # For non-stratified, we still need to pass y_bins as a dummy for the API
        y_bins = np.zeros_like(y, dtype=int)
    
    # Select objective function
    if model_type == 'xgb':
        objective = objective_xgb
    elif model_type == 'rf':
        objective = objective_rf
    else:
        raise ValueError(f"Unsupported model_type: {model_type}. Use 'xgb' or 'rf'.")
    
    # Create or load study
    if study_name and storage:
        study = optuna.create_study(
            study_name=study_name,
            storage=storage,
            direction='maximize',
            load_if_exists=True
        )
    else:
        study = optuna.create_study(direction='maximize')
    
    # Run optimization
    study.optimize(
        lambda trial: objective(trial, X, y, cv),
        n_trials=n_trials,
        show_progress_bar=True
    )
    
    best_params = study.best_params
    logger.info(f"Best parameters: {best_params}")
    logger.info(f"Best R2 score: {study.best_value:.4f}")
    
    return best_params, study

def train_tuned_model(
    X: np.ndarray,
    y: np.ndarray,
    best_params: Dict[str, Any],
    model_type: str = 'xgb'
) -> Union[xgb.XGBRegressor, RandomForestRegressor]:
    """
    Train a final model using the best hyperparameters found by Optuna.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        best_params: Dictionary of best hyperparameters.
        model_type: Type of model ('xgb' or 'rf').
        
    Returns:
        Trained model instance.
    """
    logger.info(f"Training final {model_type} model with best parameters")
    
    if model_type == 'xgb':
        # Ensure n_jobs is set for final training
        best_params['n_jobs'] = -1
        best_params['random_state'] = 42
        best_params['verbosity'] = 0
        model = xgb.XGBRegressor(**best_params)
    elif model_type == 'rf':
        best_params['n_jobs'] = -1
        best_params['random_state'] = 42
        model = RandomForestRegressor(**best_params)
    else:
        raise ValueError(f"Unsupported model_type: {model_type}")
    
    model.fit(X, y)
    return model

def run_tuning_pipeline(
    data_path: str,
    target_col: str = 'log_da_dN',
    feature_cols: Optional[List[str]] = None,
    model_type: str = 'xgb',
    n_trials: int = 50,
    n_splits: int = 5,
    output_dir: str = 'data/models'
) -> Dict[str, Any]:
    """
    Run the complete hyperparameter tuning pipeline.
    
    Args:
        data_path: Path to the preprocessed dataset CSV.
        target_col: Name of the target column.
        feature_cols: List of feature column names. If None, all numeric columns except target are used.
        model_type: Type of model to tune ('xgb' or 'rf').
        n_trials: Number of optimization trials.
        n_splits: Number of CV folds.
        output_dir: Directory to save results.
        
    Returns:
        Dictionary containing tuning results.
    """
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Prepare features and target
    if feature_cols is None:
        feature_cols = df.select_dtypes(include=[np.number]).columns.drop(target_col).tolist()
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Check for NaNs
    if np.isnan(X).any() or np.isnan(y).any():
        logger.warning("NaN values detected in data. Dropping rows with NaN.")
        mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[mask]
        y = y[mask]
    
    logger.info(f"Training data shape: X={X.shape}, y={y.shape}")
    
    # Run hyperparameter tuning
    best_params, study = tune_hyperparameters(
        X, y, model_type=model_type, n_trials=n_trials, n_splits=n_splits
    )
    
    # Train final model
    final_model = train_tuned_model(X, y, best_params, model_type)
    
    # Evaluate on full data (for reporting purposes)
    y_pred = final_model.predict(X)
    final_r2 = r2_score(y, y_pred)
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Save results
    results = {
        'model_type': model_type,
        'best_params': best_params,
        'best_cv_r2': study.best_value,
        'final_train_r2': final_r2,
        'n_trials': n_trials,
        'n_splits': n_splits,
        'n_features': len(feature_cols),
        'feature_names': feature_cols
    }
    
    # Save study results
    study_path = Path(output_dir) / f"{model_type}_study.pkl"
    import pickle
    with open(study_path, 'wb') as f:
        pickle.dump(study, f)
    
    # Save best params
    import json
    params_path = Path(output_dir) / f"{model_type}_best_params.json"
    with open(params_path, 'w') as f:
        json.dump(best_params, f, indent=2)
    
    logger.info(f"Tuning results saved to {output_dir}")
    
    return results