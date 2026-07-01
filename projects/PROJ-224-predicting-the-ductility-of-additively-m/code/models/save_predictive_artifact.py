"""
Save PredictiveModelArtifact with metrics and hyperparameters.

This module implements T034: Save `PredictiveModelArtifact` with metrics and hyperparameters.
It loads the results from the XGBoost training and evaluation (produced by xgboost_model.py),
combines them with the LME comparison results, and saves a structured JSON artifact.
"""

import os
import sys
import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.xgboost_model import load_split_data, prepare_features, tune_and_train, evaluate_model, compute_permutation_importance, load_lme_artifact, compare_with_lme

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def load_training_results() -> Dict[str, Any]:
    """
    Load the training and evaluation results from the XGBoost model.
    
    Returns:
        Dictionary containing metrics, hyperparameters, and feature importance.
    """
    # These would typically be returned by the main() function of xgboost_model.py
    # For this task, we assume they are available or re-run the necessary steps
    # In a real pipeline, this data would be passed directly or loaded from a temporary file
    
    # Placeholder for actual data loading logic
    # In the actual implementation, this would load from a temporary file or return from previous step
    return {
        "metrics": {
            "r2": 0.0,
            "mae": 0.0,
            "rmse": 0.0
        },
        "hyperparameters": {},
        "feature_importance": {},
        "training_time": 0.0
    }

def save_predictive_artifact(
    metrics: Dict[str, float],
    hyperparameters: Dict[str, Any],
    feature_importance: Dict[str, float],
    lme_comparison: Optional[Dict[str, Any]] = None,
    training_time: float = 0.0,
    output_path: str = "artifacts/predictive_model_artifact.json"
) -> str:
    """
    Save the PredictiveModelArtifact as a JSON file.
    
    Args:
        metrics: Dictionary containing R², MAE, RMSE, etc.
        hyperparameters: Dictionary containing the best hyperparameters found.
        feature_importance: Dictionary mapping features to their importance scores.
        lme_comparison: Optional dictionary containing comparison with LME model results.
        training_time: Time taken to train the model in seconds.
        output_path: Path where the artifact will be saved.
        
    Returns:
        Path to the saved artifact.
    """
    artifact = {
        "artifact_type": "PredictiveModelArtifact",
        "model_type": "XGBoostRegressor",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "metrics": metrics,
        "hyperparameters": hyperparameters,
        "feature_importance": feature_importance,
        "training_time_seconds": training_time,
        "lme_comparison": lme_comparison if lme_comparison else {}
    }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(artifact, f, indent=2)
    
    logger.info(f"Saved PredictiveModelArtifact to {output_file}")
    return str(output_file)

def main():
    """
    Main function to save the predictive model artifact.
    
    This function orchestrates the loading of results from the XGBoost model,
    performs the comparison with the LME model, and saves the final artifact.
    """
    logger.info("Starting PredictiveModelArtifact generation...")
    
    # In a real pipeline, these would be loaded from the previous step's outputs
    # For this implementation, we simulate the process by calling the relevant functions
    
    try:
        # Load split data
        data_path = "data/split_data"
        if not os.path.exists(data_path):
            logger.warning(f"Split data not found at {data_path}. Skipping artifact generation.")
            return
        
        train_data, val_data, test_data = load_split_data(data_path)
        
        # Prepare features
        X_train, y_train, X_val, y_val, X_test, y_test, feature_names = prepare_features(
            train_data, val_data, test_data
        )
        
        # Tune and train model
        best_model, best_params, training_time = tune_and_train(
            X_train, y_train, X_val, y_val, feature_names
        )
        
        # Evaluate model
        metrics = evaluate_model(best_model, X_test, y_test)
        
        # Compute permutation importance
        importance = compute_permutation_importance(best_model, X_test, y_test, feature_names)
        
        # Load LME artifact and compare
        lme_artifact_path = "artifacts/lme_model_artifact.json"
        lme_comparison = None
        if os.path.exists(lme_artifact_path):
            lme_comparison = compare_with_lme(importance, lme_artifact_path)
        
        # Save the predictive model artifact
        artifact_path = save_predictive_artifact(
            metrics=metrics,
            hyperparameters=best_params,
            feature_importance=importance,
            lme_comparison=lme_comparison,
            training_time=training_time
        )
        
        logger.info(f"Successfully saved PredictiveModelArtifact to {artifact_path}")
        
    except Exception as e:
        logger.error(f"Failed to save PredictiveModelArtifact: {str(e)}")
        raise

if __name__ == "__main__":
    main()