"""
T026: Control Analysis - Train models excluding Volume and Surface Area descriptors.

This script trains Random Forest and Gradient Boosting models on the test set
but explicitly excludes the 'Volume' and 'SurfaceArea' features to probe the
contribution of interaction-related features vs purely geometric size features.

Deliverable: results/control_analysis_metrics.json
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import numpy as np

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config, setup_logging, log_event
from utils.metrics import paired_t_test, bonferroni_correct

def setup_logger():
    """Setup logger for this script."""
    logger = logging.getLogger("control_analysis")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_test_data():
    """Load the pre-split test data from data/processed/test.csv."""
    config = get_config()
    test_path = Path(config.DATA_PATH) / "processed" / "test.csv"
    
    if not test_path.exists():
        raise FileNotFoundError(f"Test data file not found: {test_path}")
    
    df = pd.read_csv(test_path)
    return df

def get_control_features(df):
    """
    Get feature columns excluding 'Volume' and 'SurfaceArea'.
    Assumes target is 'packing_coefficient'.
    """
    target_col = 'packing_coefficient'
    all_features = [col for col in df.columns if col not in [target_col, 'ID', 'dipole_imputed']]
    
    # Features to exclude for control analysis
    exclude_features = ['Volume', 'SurfaceArea']
    control_features = [f for f in all_features if f not in exclude_features]
    
    return control_features

def train_and_evaluate_model(X_train, y_train, X_test, y_test, model, model_name, logger):
    """Train a model and return evaluation metrics."""
    logger.info(f"Training {model_name}...")
    model.fit(X_train, y_train)
    
    logger.info(f"Evaluating {model_name} on test set...")
    y_pred = model.predict(X_test)
    
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    metrics = {
        "model_name": model_name,
        "features_used": list(X_train.columns),
        "num_features": len(X_train.columns),
        "R2": float(r2),
        "MAE": float(mae),
        "RMSE": float(rmse)
    }
    
    logger.info(f"{model_name} Results -> R2: {r2:.4f}, MAE: {mae:.4f}, RMSE: {rmse:.4f}")
    return metrics

def main():
    logger = setup_logger()
    log_event("control_analysis_start", {"task": "T026"})
    
    try:
        # Load test data
        logger.info("Loading test data...")
        df = load_test_data()
        
        # Identify target and features
        target_col = 'packing_coefficient'
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in data")
        
        # Get control features (excluding Volume and SurfaceArea)
        control_features = get_control_features(df)
        
        if len(control_features) == 0:
            raise ValueError("No control features available after excluding Volume and SurfaceArea")
        
        logger.info(f"Using {len(control_features)} control features: {control_features}")
        
        # Split into features and target
        X = df[control_features]
        y = df[target_col]
        
        # Since we are using the test set for evaluation of the control analysis
        # (as per the task description to "probe contribution"), we evaluate directly.
        # In a real pipeline, we would train on train/val and eval on test.
        # Assuming the data loaded is the test set as per T022/T026 context.
        # If the file is the full test set, we use it directly for evaluation
        # after training on the same data (as a probe) or we assume the file
        # contains the split. The task says "Evaluate all models on the test set".
        # We will assume the loaded 'test.csv' is the hold-out test set.
        # To properly evaluate, we need a training set. 
        # However, the task T026 is a "Control Analysis" often done on the 
        # test set performance of models trained on the training set.
        # Since T022/T023/T024 load train/val/test, T026 should likely 
        # load the TRAIN set to train the control models, then evaluate on TEST.
        
        # Re-load train and test separately to be correct
        config = get_config()
        train_path = Path(config.DATA_PATH) / "processed" / "train.csv"
        test_path = Path(config.DATA_PATH) / "processed" / "test.csv"
        
        if not train_path.exists() or not test_path.exists():
            raise FileNotFoundError("Train or Test CSV files not found in data/processed/")
        
        df_train = pd.read_csv(train_path)
        df_test = pd.read_csv(test_path)
        
        # Ensure target exists
        if target_col not in df_train.columns or target_col not in df_test.columns:
            raise ValueError(f"Target column '{target_col}' missing in train/test data")
        
        # Filter features
        X_train = df_train[control_features]
        y_train = df_train[target_col]
        X_test = df_test[control_features]
        y_test = df_test[target_col]
        
        logger.info(f"Train shape: {X_train.shape}, Test shape: {X_test.shape}")
        
        # Initialize models with same seeds as T023/T024
        rf_model = RandomForestRegressor(random_state=42, n_jobs=-1)
        gb_model = GradientBoostingRegressor(random_state=42)
        
        results = []
        
        # Train and Evaluate Random Forest (Control)
        rf_metrics = train_and_evaluate_model(
            X_train, y_train, X_test, y_test, rf_model, "RandomForest_Control", logger
        )
        results.append(rf_metrics)
        
        # Train and Evaluate Gradient Boosting (Control)
        gb_metrics = train_and_evaluate_model(
            X_train, y_train, X_test, y_test, gb_model, "GradientBoosting_Control", logger
        )
        results.append(gb_metrics)
        
        # Save results to results/control_analysis_metrics.json
        output_dir = Path("results")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "control_analysis_metrics.json"
        
        output_data = {
            "task": "T026",
            "description": "Control Analysis excluding Volume and SurfaceArea",
            "excluded_features": ["Volume", "SurfaceArea"],
            "models": results
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Control analysis results saved to {output_path}")
        log_event("control_analysis_complete", {"output_file": str(output_path)})
        
    except Exception as e:
        logger.error(f"Error during control analysis: {str(e)}")
        log_event("control_analysis_failed", {"error": str(e)})
        raise

if __name__ == "__main__":
    main()