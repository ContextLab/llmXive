"""
Model Training Module for Glass Forming Ability Prediction.
Handles splitting, training, and evaluation of ML models.
"""

import logging
import os
import sys
import json
import pickle
import pandas as pd
from typing import Dict, Any, Tuple, List
from sklearn.ensemble import RandomForestRegressor, DummyRegressor
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import mean_squared_error
from scipy.stats import ttest_rel
from utils import get_logger, ensure_dir

logger = get_logger("train")
DATA_DIR = "data/processed"
MODEL_DIR = "data/models"
LOG_DIR = "data/logs"

def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load processed data and split into features (X) and target (y).
    """
    data_path = os.path.join(DATA_DIR, "processed_alloys.csv")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data not found at {data_path}. Run ingestion.py first.")
    
    df = pd.read_csv(data_path)
    
    # Define features and target
    feature_cols = ["mixing_enthalpy", "atomic_size_mismatch", "electronegativity_variance"]
    target_col = "critical_cooling_rate"
    
    # Check variance
    if df[target_col].var() == 0:
        raise ValueError("Target variable has zero variance; cannot train regression model.")
    
    X = df[feature_cols]
    y = df[target_col]
    
    return X, y, df

def train_model(X: pd.DataFrame, y: pd.Series, random_state: int = 42) -> Any:
    """
    Train a Random Forest Regressor.
    """
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X, y)
    return model

def run_cross_validation(model: Any, X: pd.DataFrame, y: pd.Series, n_splits: int = 5) -> List[float]:
    """
    Perform k-fold cross-validation.
    """
    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=kfold, scoring='neg_root_mean_squared_error')
    return -scores # Convert back to positive RMSE

def evaluate_on_test(model: Any, X_test: pd.DataFrame, y_test: pd.Series) -> float:
    """
    Evaluate model on test set and return RMSE.
    """
    y_pred = model.predict(X_test)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    return rmse

def save_model(model: Any, path: str):
    """
    Save model to disk.
    """
    ensure_dir(os.path.dirname(path))
    with open(path, 'wb') as f:
        pickle.dump(model, f)

def train_and_evaluate_null_model(X_train: pd.DataFrame, y_train: pd.Series, X_test: pd.DataFrame, y_test: pd.Series, cv_folds: List) -> Dict[str, Any]:
    """
    Train a DummyRegressor and evaluate it.
    """
    # Train dummy model
    dummy = DummyRegressor(strategy='mean')
    dummy.fit(X_train, y_train)
    
    # Evaluate on test set
    test_rmse = evaluate_on_test(dummy, X_test, y_test)
    
    # Cross validation on dummy (using same folds)
    dummy_scores = run_cross_validation(dummy, X_train, y_train, n_splits=5)
    
    return {
        "test_rmse": test_rmse,
        "cv_scores": dummy_scores,
        "mean_cv_rmse": sum(dummy_scores)/len(dummy_scores),
        "std_cv_rmse": (sum((s - sum(dummy_scores)/len(dummy_scores))**2 for s in dummy_scores)/len(dummy_scores))**0.5
    }

def run_training():
    """
    Main entry point for training pipeline.
    """
    logger.info("Starting training pipeline")
    ensure_dir(MODEL_DIR)
    ensure_dir(LOG_DIR)
    
    try:
        # Load Data
        X, y, df_full = load_data()
        
        # Validate total size (SC-001)
        n_total = len(df_full)
        if n_total < 500:
            raise ValueError(f"SC-001 Violation: Total dataset size < 500. Minimum N >= 500 required by FR-001.")
        
        with open(os.path.join(LOG_DIR, "training_set_validation.json"), 'w') as f:
            json.dump({"status": "pass", "n_total": n_total}, f, indent=2)
        
        # Split Data
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Save splits
        train_indices = df_full.index[X_train.index].tolist()
        test_indices = df_full.index[X_test.index].tolist()
        
        with open(os.path.join(MODEL_DIR, "split_indices.json"), 'w') as f:
            json.dump({"train": train_indices, "test": test_indices}, f, indent=2)
        
        # Save train/test sets
        df_train = df_full.loc[train_indices]
        df_test = df_full.loc[test_indices]
        df_train.to_csv(os.path.join(DATA_DIR, "train_set.csv"), index=False)
        df_test.to_csv(os.path.join(DATA_DIR, "test_set.csv"), index=False)
        
        # Train Main Model
        logger.info("Training Random Forest model...")
        model = train_model(X_train, y_train)
        
        # Cross Validation
        cv_scores = run_cross_validation(model, X_train, y_train, n_splits=5)
        mean_rmse = sum(cv_scores)/len(cv_scores)
        std_rmse = (sum((s - mean_rmse)**2 for s in cv_scores)/len(cv_scores))**0.5
        
        cv_metrics = {
            "fold_scores": cv_scores,
            "mean_rmse": mean_rmse,
            "std_rmse": std_rmse
        }
        
        with open(os.path.join(MODEL_DIR, "cv_metrics.json"), 'w') as f:
            json.dump(cv_metrics, f, indent=2)
        
        # Save Model
        save_model(model, os.path.join(MODEL_DIR, "random_forest_model.pkl"))
        
        # Train & Evaluate Null Model
        logger.info("Training and evaluating Null Model...")
        null_results = train_and_evaluate_null_model(X_train, y_train, X_test, y_test, [])
        
        with open(os.path.join(MODEL_DIR, "null_model_cv_scores.json"), 'w') as f:
            json.dump({
                "fold_scores": null_results["cv_scores"],
                "mean_rmse": null_results["mean_cv_rmse"],
                "std_rmse": null_results["std_cv_rmse"]
            }, f, indent=2)
        
        with open(os.path.join(MODEL_DIR, "null_model_rmse.json"), 'w') as f:
            json.dump({"test_rmse": null_results["test_rmse"]}, f, indent=2)
        
        # Save Null Model
        from sklearn.dummy import DummyRegressor
        dummy_model = DummyRegressor(strategy='mean')
        dummy_model.fit(X_train, y_train)
        save_model(dummy_model, os.path.join(MODEL_DIR, "null_model.pkl"))
        
        # Statistical Test (T024a)
        logger.info("Performing statistical test...")
        t_stat, p_value = ttest_rel(cv_scores, null_results["cv_scores"])
        sc002_met = p_value < 0.05
        
        stat_comparison = {
            "p_value": p_value,
            "t_statistic": t_stat,
            "sc002_met": sc002_met
        }
        
        with open(os.path.join(MODEL_DIR, "statistical_comparison.json"), 'w') as f:
            json.dump(stat_comparison, f, indent=2)
        
        # Gate Check (T024c)
        sc002_status = "PASSED" if sc002_met else "FAILED"
        with open(os.path.join(MODEL_DIR, "sc002_status.json"), 'w') as f:
            json.dump({"status": sc002_status}, f, indent=2)
        
        # Test Metrics
        test_rmse = evaluate_on_test(model, X_test, y_test)
        with open(os.path.join(MODEL_DIR, "test_metrics.json"), 'w') as f:
            json.dump({"test_rmse": test_rmse}, f, indent=2)
        
        logger.info("Training pipeline completed successfully.")
        return model

    except Exception as e:
        logger.error(f"Training pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_training()