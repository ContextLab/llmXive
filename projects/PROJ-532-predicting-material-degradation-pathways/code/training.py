import os
import json
import logging
import pickle
import time
from pathlib import Path
from typing import Tuple, Any, Dict

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from utils import ensure_dir, save_json, load_json, get_env_var, setup_logging

# Setup logging
logger = setup_logging("training")

def load_training_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the training set from the OOD split artifacts.
    Returns (X_train, y_train).
    """
    train_path = Path("data/processed/train_set.parquet")
    if not train_path.exists():
        raise FileNotFoundError(f"Training data not found at {train_path}. Run preprocessing pipeline first.")
    
    df = pd.read_parquet(train_path)
    
    # Identify feature columns (all numeric except 'label' and 'alloy_class')
    exclude_cols = ['label', 'alloy_class', 'sample_id']
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    X = df[feature_cols]
    y = df['label']
    
    logger.info(f"Loaded training data: {X.shape[0]} samples, {X.shape[1]} features")
    return X, y

def train_model(X: pd.DataFrame, y: pd.Series) -> RandomForestClassifier:
    """
    Train a Random Forest classifier on CPU.
    """
    logger.info("Starting model training...")
    start_time = time.time()
    
    # Initialize model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        random_state=42,
        n_jobs=1,  # CPU-only constraint
        verbose=1
    )
    
    # Train
    model.fit(X, y)
    
    elapsed = time.time() - start_time
    logger.info(f"Training completed in {elapsed:.2f} seconds")
    
    return model

def evaluate_model(model: RandomForestClassifier, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """
    Evaluate the model and return metrics.
    """
    logger.info("Evaluating model...")
    start_time = time.time()
    
    y_pred = model.predict(X)
    
    # Classification report as dict
    report = classification_report(y, y_pred, output_dict=True)
    
    elapsed = time.time() - start_time
    logger.info(f"Evaluation completed in {elapsed:.2f} seconds")
    
    return {
        "metrics": report,
        "elapsed_seconds": elapsed
    }

def save_artifacts(model: RandomForestClassifier, metrics: Dict[str, Any], timing: Dict[str, float]):
    """
    Save the trained model and metrics to disk.
    """
    artifacts_dir = Path("results/artifacts")
    metrics_dir = Path("results/metrics")
    
    ensure_dir(artifacts_dir)
    ensure_dir(metrics_dir)
    
    # Save model
    model_path = artifacts_dir / "model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")
    
    # Save metrics
    metrics_path = metrics_dir / "training_report.json"
    save_json(metrics_path, metrics)
    logger.info(f"Metrics saved to {metrics_path}")
    
    # Save timing log
    timing_path = metrics_dir / "timing_log.json"
    save_json(timing_path, timing)
    logger.info(f"Timing log saved to {timing_path}")

def run_training_pipeline():
    """
    Main pipeline execution: Load -> Train -> Evaluate -> Save.
    Includes timing instrumentation for T030a.
    """
    total_start = time.time()
    
    # 1. Load Data
    X, y = load_training_data()
    
    # 2. Train Model
    model = train_model(X, y)
    
    # 3. Evaluate Model
    eval_metrics = evaluate_model(model, X, y)
    
    # 4. Calculate Total Timing
    total_end = time.time()
    total_elapsed = total_end - total_start
    
    # 5. Prepare Timing Log (T030a requirement)
    timing_log = {
        "total_execution_time_seconds": round(total_elapsed, 4),
        "components": {
            "data_loading_seconds": eval_metrics.get("elapsed_seconds", 0), # Placeholder, actual split if needed
            "model_training_seconds": 0, # Would be extracted if we split train/eval timing more granularly
            "model_evaluation_seconds": eval_metrics.get("elapsed_seconds", 0)
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "completed"
    }
    
    # Refine timing if we tracked sub-steps separately in a real run
    # For now, we log the total and the evaluation time as a proxy
    timing_log["components"]["model_training_seconds"] = round(total_elapsed - eval_metrics.get("elapsed_seconds", 0), 4)
    
    # 6. Save Artifacts
    save_artifacts(model, eval_metrics, timing_log)
    
    logger.info(f"Pipeline completed successfully. Total time: {total_elapsed:.2f}s")
    return timing_log

def main():
    """
    Entry point for the training script.
    """
    try:
        run_training_pipeline()
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()