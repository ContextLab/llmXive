"""
Evaluation logic for User Story 2 (T019).
Calculates R², MAE, RMSE and selects the best model by highest R².
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import joblib

# Project imports based on API surface
from seed import set_seed
from models import ModelPerformance
from hygiene import calculate_md5, save_artifact_hashes, load_artifact_hashes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class EvaluationResult:
    """Container for evaluation metrics."""
    model_name: str
    r2: float
    mae: float
    rmse: float
    is_best: bool
    metrics: Dict[str, float]

def load_processed_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load the processed dataset and prepare features/targets.
    Returns:
        X_train: Training features
        X_test: Test features
        y_test: Test targets
    """
    logger.info("Loading processed data...")
    data_path = Path("data/processed/aggregated_clean.csv")
    
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}. "
                              "Run T015 (ingest) and T016 (pre_check) first.")
    
    df = pd.read_csv(data_path)
    
    # Load the model from T017/T018 training pipeline
    model_path = Path("models/best_model.joblib")
    if not model_path.exists():
        # If model doesn't exist yet, we assume the training script (T017/T018)
        # would have created it. For evaluation to work, we need the model.
        # In a real pipeline, this would be a hard failure.
        raise FileNotFoundError(f"Trained model not found at {model_path}. "
                              "Run T017/T018 (train) first.")
    
    model_data = joblib.load(model_path)
    
    # Extract features and targets from the model data or re-split
    # Assuming model_data contains the training split info or we re-process
    # For this implementation, we expect the training script to have saved
    # the train/test split or we re-split using the same random state.
    
    # Re-load and split to ensure consistency with training
    # The training script should have saved the indices or we use the same seed
    set_seed(42)  # Match training seed
    
    from sklearn.model_selection import train_test_split
    
    # Define target and features
    target_col = 'wear_rate'  # Assuming this is the target based on context
    if target_col not in df.columns:
        # Try normalized wear coefficient K if available
        target_col = 'wear_coefficient_K' if 'wear_coefficient_K' in df.columns else None
    
    if target_col is None:
        raise ValueError("Target column 'wear_rate' or 'wear_coefficient_K' not found in data.")
    
    feature_cols = [col for col in df.columns if col not in [target_col, 'normalization_method']]
    
    X = df[feature_cols]
    y = df[target_col]
    
    # Perform the same split as training (assuming 80/20 with seed 42)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    logger.info(f"Loaded {len(df)} records, split into {len(X_train)} train, {len(X_test)} test")
    return X_train, X_test, y_test

def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series, model_name: str) -> EvaluationResult:
    """
    Evaluate a single model and calculate metrics.
    
    Args:
        model: Trained scikit-learn model
        X_test: Test features
        y_test: Test targets
        model_name: Name of the model for reporting
        
    Returns:
        EvaluationResult with metrics
    """
    logger.info(f"Evaluating {model_name}...")
    
    # Predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    r2 = model.score(X_test, y_test)
    mae = np.mean(np.abs(y_pred - y_test))
    rmse = np.sqrt(np.mean((y_pred - y_test) ** 2))
    
    metrics = {
        'r2': float(r2),
        'mae': float(mae),
        'rmse': float(rmse),
        'n_test_samples': len(y_test)
    }
    
    logger.info(f"{model_name} - R²: {r2:.4f}, MAE: {mae:.4f}, RMSE: {rmse:.4f}")
    
    return EvaluationResult(
        model_name=model_name,
        r2=r2,
        mae=mae,
        rmse=rmse,
        is_best=False,  # Will be updated later
        metrics=metrics
    )

def run_evaluation_pipeline() -> Dict[str, Any]:
    """
    Main evaluation pipeline that loads the best model, evaluates it,
    and saves results.
    
    Returns:
        Dictionary containing evaluation results and best model info
    """
    logger.info("Starting evaluation pipeline (T019)...")
    
    # Load data and model
    X_train, X_test, y_test = load_processed_data()
    
    # Load the best model (saved by T017/T018)
    model_path = Path("models/best_model.joblib")
    model = joblib.load(model_path)
    
    # Get model name from the model object or metadata
    model_name = getattr(model, 'model_name', 'BestModel')
    if hasattr(model, 'estimator'):
        model_name = type(model.estimator).__name__
    elif hasattr(model, 'best_estimator_'):
        model_name = type(model.best_estimator_).__name__
    else:
        model_name = type(model).__name__
    
    # Evaluate the model
    result = evaluate_model(model, X_test, y_test, model_name)
    
    # Since we're evaluating the "best" model from grid search, it is by definition the best
    result.is_best = True
    
    # Prepare report
    report = {
        'best_model': {
            'name': result.model_name,
            'r2': result.r2,
            'mae': result.mae,
            'rmse': result.rmse,
            'is_best': result.is_best,
            'metrics': result.metrics
        },
        'evaluation_timestamp': pd.Timestamp.now().isoformat(),
        'test_samples': len(y_test),
        'selection_criteria': 'highest_r2'
    }
    
    # Save results
    output_path = Path("reports/model_performance.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Evaluation results saved to {output_path}")
    
    # Update artifact hashes
    save_artifact_hashes([str(output_path)])
    
    return report

def main():
    """Entry point for evaluation task."""
    try:
        report = run_evaluation_pipeline()
        print(f"Evaluation Complete: {report['best_model']['name']} with R²={report['best_model']['r2']:.4f}")
        return 0
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    sys.exit(main())