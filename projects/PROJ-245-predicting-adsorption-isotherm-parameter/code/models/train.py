import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score, GridSearchCV, StratifiedKFold, KFold
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib

from models.entities import Adsorbate, Adsorbent, IsothermParameter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure output directories exist."""
    models_dir = Path("data/models")
    reports_dir = Path("data/reports")
    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    return models_dir, reports_dir

def load_preprocessed_data(file_path: str = "data/processed/curated_dataset.csv") -> pd.DataFrame:
    """Load the preprocessed dataset."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Preprocessed data not found at {file_path}. Run preprocessing first.")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {file_path}")
    return df

def material_level_split(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data by material_id to ensure no material leakage between train and test sets.
    """
    if 'material_id' not in df.columns:
        raise ValueError("DataFrame must contain 'material_id' column for material-level splitting.")
    
    unique_materials = df['material_id'].unique()
    np.random.seed(random_state)
    np.random.shuffle(unique_materials)
    
    split_idx = int(len(unique_materials) * (1 - test_size))
    train_materials = unique_materials[:split_idx]
    test_materials = unique_materials[split_idx:]
    
    train_df = df[df['material_id'].isin(train_materials)].reset_index(drop=True)
    test_df = df[df['material_id'].isin(test_materials)].reset_index(drop=True)
    
    logger.info(f"Material-level split: {len(train_materials)} materials in train, {len(test_materials)} in test.")
    logger.info(f"Train rows: {len(train_df)}, Test rows: {len(test_df)}")
    
    # Verify no overlap
    train_ids = set(train_df['material_id'])
    test_ids = set(test_df['material_id'])
    if train_ids.intersection(test_ids):
        raise ValueError("Material ID leakage detected between train and test sets!")
    
    return train_df, test_df

def train_models(
    train_df: pd.DataFrame, 
    target_cols: List[str], 
    feature_cols: List[str], 
    enable_tuning: bool = True
) -> Dict[str, Any]:
    """
    Train Linear Regression, Random Forest, and Gradient Boosting models.
    Implements 5-fold cross-validation and hyperparameter tuning if enabled.
    """
    X = train_df[feature_cols].values
    results = {}
    
    models_config = {
        "Linear Regression": {
            "model": LinearRegression(),
            "params": {}
        },
        "Random Forest": {
            "model": RandomForestRegressor(random_state=42, n_jobs=-1),
            "params": {
                "n_estimators": [50, 100, 200],
                "max_depth": [None, 10, 20],
                "min_samples_split": [2, 5]
            }
        },
        "Gradient Boosting": {
            "model": GradientBoostingRegressor(random_state=42),
            "params": {
                "n_estimators": [50, 100, 200],
                "max_depth": [3, 5, 7],
                "learning_rate": [0.05, 0.1, 0.2]
            }
        }
    }

    for name, config in models_config.items():
        logger.info(f"Training and tuning {name}...")
        model = config["model"]
        params = config["params"]
        
        # Define CV strategy
        cv = KFold(n_splits=5, shuffle=True, random_state=42)
        
        if enable_tuning and params:
            # Grid Search with Cross Validation
            grid_search = GridSearchCV(
                estimator=model, 
                param_grid=params, 
                cv=cv, 
                scoring='r2', 
                n_jobs=-1, 
                verbose=1
            )
            grid_search.fit(X, train_df[target_cols[0]]) # Assuming single target for tuning simplicity or loop over targets
            
            best_model = grid_search.best_estimator_
            best_params = grid_search.best_params_
            cv_scores = grid_search.cv_results_['mean_test_score']
            logger.info(f"{name} Best Params: {best_params}")
            logger.info(f"{name} Best CV R²: {best_cv_score:.4f}")
        else:
            # Simple Cross Validation without tuning
            if not params:
                model.fit(X, train_df[target_cols[0]])
                best_model = model
                cv_scores = cross_val_score(model, X, train_df[target_cols[0]], cv=cv, scoring='r2')
                best_cv_score = np.mean(cv_scores)
                best_params = {}
                logger.info(f"{name} CV R²: {best_cv_score:.4f}")
            else:
                # If tuning disabled but params exist, use default model
                model.fit(X, train_df[target_cols[0]])
                best_model = model
                cv_scores = cross_val_score(model, X, train_df[target_cols[0]], cv=cv, scoring='r2')
                best_cv_score = np.mean(cv_scores)
                best_params = {}
                logger.info(f"{name} (No Tuning) CV R²: {best_cv_score:.4f}")

        results[name] = {
            "model": best_model,
            "best_params": best_params,
            "cv_mean_r2": best_cv_score,
            "cv_std_r2": np.std(cv_scores) if len(cv_scores) > 1 else 0.0
        }
    
    return results

def evaluate_models(
    models_results: Dict[str, Any], 
    test_df: pd.DataFrame, 
    feature_cols: List[str], 
    target_col: str
) -> pd.DataFrame:
    """
    Evaluate models on the independent test set and calculate metrics.
    """
    X_test = test_df[feature_cols].values
    y_test = test_df[target_col].values
    
    metrics_records = []
    
    for name, res in models_results.items():
        model = res["model"]
        y_pred = model.predict(X_test)
        
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        
        metrics_records.append({
            "model_name": name,
            "r2": r2,
            "rmse": rmse,
            "mae": mae,
            "cv_mean_r2": res["cv_mean_r2"],
            "cv_std_r2": res["cv_std_r2"]
        })
        logger.info(f"{name} Test Set - R²: {r2:.4f}, RMSE: {rmse:.4f}, MAE: {mae:.4f}")
    
    return pd.DataFrame(metrics_records)

def save_models(models_results: Dict[str, Any], reports_df: pd.DataFrame, models_dir: Path, reports_dir: Path):
    """Save trained models and evaluation reports."""
    for name, res in models_results.items():
        model_path = models_dir / f"{name.replace(' ', '_')}_model.joblib"
        joblib.dump(res["model"], model_path)
        logger.info(f"Saved {name} model to {model_path}")
    
    report_path = reports_dir / "model_evaluation_report.csv"
    reports_df.to_csv(report_path, index=False)
    logger.info(f"Saved evaluation report to {report_path}")
    
    # Save best model metadata
    best_model_row = reports_df.loc[reports_df['r2'].idxmax()]
    metadata = {
        "best_model": best_model_row['model_name'],
        "test_r2": best_model_row['r2'],
        "test_rmse": best_model_row['rmse'],
        "test_mae": best_model_row['mae'],
        "cv_r2": best_model_row['cv_mean_r2'],
        "cv_std_r2": best_model_row['cv_std_r2']
    }
    metadata_path = reports_dir / "best_model_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved best model metadata to {metadata_path}")

def run_training_pipeline(
    data_path: str = "data/processed/curated_dataset.csv",
    target_cols: List[str] = None,
    feature_cols: List[str] = None,
    test_size: float = 0.2,
    enable_tuning: bool = True
):
    """
    Orchestrates the full training pipeline: Load -> Split -> Train (with CV/Tuning) -> Evaluate -> Save.
    """
    if target_cols is None:
        target_cols = ["langmuir_capacity"] # Default target, can be overridden
    if feature_cols is None:
        # Default features based on typical descriptor output, excluding metadata
        exclude_cols = ['material_id', 'adsorbate_smiles', 'adsorbent_type', 'isotherm_type', 'langmuir_capacity', 'henry_constant', 'surface_area']
        # We assume the dataframe has been preprocessed to have numeric descriptors
        # In a real scenario, we might pass these explicitly or infer from schema
        pass 

    models_dir, reports_dir = ensure_dirs()
    
    # 1. Load Data
    df = load_preprocessed_data(data_path)
    
    # Auto-detect feature columns if not provided
    if feature_cols is None:
        feature_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in ['float64', 'int64']]
        logger.info(f"Auto-detected feature columns: {feature_cols}")
        if not feature_cols:
            raise ValueError("No feature columns detected. Please specify feature_cols manually.")
    
    target_col = target_cols[0] # Focus on one target for this pipeline step
    
    # 2. Split Data
    train_df, test_df = material_level_split(df, test_size=test_size)
    
    # 3. Train Models (with 5-fold CV and Tuning)
    models_results = train_models(train_df, [target_col], feature_cols, enable_tuning=enable_tuning)
    
    # 4. Evaluate Models
    eval_df = evaluate_models(models_results, test_df, feature_cols, target_col)
    
    # 5. Save Results
    save_models(models_results, eval_df, models_dir, reports_dir)
    
    return models_results, eval_df

def main():
    """Entry point for script execution."""
    logger.info("Starting Model Training Pipeline (T022: 5-Fold CV & Tuning)")
    try:
        # Default configuration
        data_path = "data/processed/curated_dataset.csv"
        target_cols = ["langmuir_capacity"]
        feature_cols = None # Will auto-detect
        test_size = 0.2
        enable_tuning = True
        
        run_training_pipeline(
            data_path=data_path,
            target_cols=target_cols,
            feature_cols=feature_cols,
            test_size=test_size,
            enable_tuning=enable_tuning
        )
        logger.info("Training pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()