import logging
import os
import time
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import KFold, cross_val_score, GridSearchCV
from sklearn.metrics import r2_score, mean_absolute_error
from config import DATA_PROCESSED, DATA_MODELS, RANDOM_SEED, setup_logging, ensure_dirs

# Ensure logging is configured
logger = setup_logging()

def load_training_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the processed training data with features and targets.
    Returns:
        X: DataFrame of features
        y: Series of target values (formation_energy_per_atom)
    """
    file_path = DATA_PROCESSED / "heas_train_features.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Training data not found at {file_path}. Run feature_engineering.py first.")

    df = pd.read_csv(file_path)
    
    # Define feature columns based on T021 output
    feature_cols = [
        'mean_atomic_radius', 'var_atomic_radius',
        'mean_electronegativity', 'var_electronegativity',
        'mean_VEC', 'var_VEC',
        'mean_melting_point', 'var_melting_point'
    ]
    
    # Ensure all required columns exist
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing feature columns in {file_path}: {missing_cols}")

    X = df[feature_cols]
    y = df['target_energy']  # Target column defined in T012

    logger.info(f"Loaded training data: {X.shape[0]} samples, {X.shape[1]} features.")
    return X, y

def train_and_evaluate(
    X: pd.DataFrame, 
    y: pd.Series, 
    perform_hyperparameter_tuning: bool = True
) -> Dict[str, Any]:
    """
    Train Random Forest and Gradient Boosting models with k-fold cross-validation.
    Optionally performs hyperparameter tuning via GridSearchCV.
    
    Args:
        X: Feature matrix
        y: Target vector
        perform_hyperparameter_tuning: If True, runs GridSearchCV for best params.
    
    Returns:
        Dictionary containing trained models, best parameters, and CV scores.
    """
    results = {}
    models = {}
    
    # Define models to train
    model_configs = {
        'RandomForest': RandomForestRegressor(random_state=RANDOM_SEED, n_jobs=-1),
        'GradientBoosting': GradientBoostingRegressor(random_state=RANDOM_SEED)
    }

    # Define parameter grids for hyperparameter tuning
    param_grids = {
        'RandomForest': {
            'n_estimators': [100, 200],
            'max_depth': [None, 10, 20],
            'min_samples_split': [2, 5]
        },
        'GradientBoosting': {
            'n_estimators': [100, 200],
            'max_depth': [3, 5, 7],
            'learning_rate': [0.05, 0.1],
            'min_samples_split': [2, 5]
        }
    }

    k_folds = 5
    kf = KFold(n_splits=k_folds, shuffle=True, random_state=RANDOM_SEED)

    for name, model in model_configs.items():
        logger.info(f"Training {name} model...")
        start_time = time.time()

        if perform_hyperparameter_tuning:
            logger.info(f"Performing hyperparameter tuning for {name}...")
            grid_search = GridSearchCV(
                estimator=model,
                param_grid=param_grids[name],
                cv=kf,
                scoring='r2',
                n_jobs=-1,
                verbose=1
            )
            grid_search.fit(X, y)
            
            best_model = grid_search.best_estimator_
            best_params = grid_search.best_params_
            best_cv_score = grid_search.best_score_
            
            logger.info(f"Best {name} params: {best_params}")
            logger.info(f"Best {name} CV R2 score: {best_cv_score:.4f}")
        else:
            # Train with default parameters
            model.fit(X, y)
            best_model = model
            best_params = model.get_params()
            # Calculate CV score for default params
            scores = cross_val_score(best_model, X, y, cv=kf, scoring='r2')
            best_cv_score = scores.mean()
            logger.info(f"{name} CV R2 score (default): {best_cv_score:.4f}")

        # Final evaluation on full training set for baseline comparison
        y_pred_train = best_model.predict(X)
        train_r2 = r2_score(y, y_pred_train)
        train_mae = mean_absolute_error(y, y_pred_train)

        elapsed = time.time() - start_time
        
        models[name] = best_model
        results[name] = {
            'best_params': best_params,
            'cv_r2_mean': best_cv_score,
            'train_r2': train_r2,
            'train_mae': train_mae,
            'training_time_sec': elapsed
        }
        
        logger.info(f"{name} training completed in {elapsed:.2f}s. Train R2: {train_r2:.4f}")

    results['models'] = models
    return results

def save_model(models: Dict[str, Any], output_dir: Optional[Path] = None) -> None:
    """
    Save trained models to disk.
    
    Args:
        models: Dictionary of trained models (from train_and_evaluate result)
        output_dir: Directory to save models. Defaults to DATA_MODELS.
    """
    if output_dir is None:
        output_dir = DATA_MODELS
    
    ensure_dirs(output_dir)
    
    models_to_save = models.get('models', models)
    
    for name, model in models_to_save.items():
        file_path = output_dir / f"{name}_model.pkl"
        with open(file_path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Saved {name} model to {file_path}")

def main():
    """
    Main entry point for model training and hyperparameter tuning.
    """
    logger.info("Starting model training pipeline with hyperparameter tuning.")
    
    try:
        # 1. Load Data
        X, y = load_training_data()
        
        # 2. Train and Tune
        results = train_and_evaluate(X, y, perform_hyperparameter_tuning=True)
        
        # 3. Save Models
        save_model(results)
        
        # 4. Log Summary
        logger.info("Training Pipeline Complete.")
        for name, stats in results.items():
            if name != 'models':
                logger.info(f"Summary for {name}:")
                logger.info(f"  Best Params: {stats['best_params']}")
                logger.info(f"  CV R2: {stats['cv_r2_mean']:.4f}")
                logger.info(f"  Train R2: {stats['train_r2']:.4f}")
                
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()