import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from config import get_project_root, get_validation_dir, get_processed_dir
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_model_artifacts(model_path: Optional[str] = None) -> Dict[str, Any]:
    """Load trained model artifacts (e.g., Random Forest model, feature names)."""
    if model_path is None:
        model_path = os.path.join(get_processed_dir(), "model_run.json")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model artifacts not found at {model_path}")
    
    with open(model_path, 'r') as f:
        return json.load(f)

def load_heldout_data(heldout_path: Optional[str] = None) -> Tuple[Any, Any]:
    """Load held-out dataset for internal validation."""
    if heldout_path is None:
        heldout_path = os.path.join(get_processed_dir(), "electrolyte_heldout.csv")
    
    if not os.path.exists(heldout_path):
        raise FileNotFoundError(f"Held-out data not found at {heldout_path}")
    
    import pandas as pd
    df = pd.read_csv(heldout_path)
    # Assuming the last column is the target
    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]
    return X, y

def load_data_status(status_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the data status JSON file to determine external data availability.
    Sets validation_mode based on external_data_available flag.
    """
    if status_path is None:
        status_path = os.path.join(get_validation_dir(), "data_status.json")
    
    if not os.path.exists(status_path):
        logger.warning(f"Data status file not found at {status_path}. Defaulting to internal fallback.")
        return {
            "external_data_available": False,
            "validation_mode": "internal_fallback",
            "sources_checked": [],
            "error_details": ["File not found"]
        }
    
    with open(status_path, 'r') as f:
        status = json.load(f)
    
    # CRITICAL: Enforce validation_mode logic based on external_data_available
    if not status.get("external_data_available", False):
        status["validation_mode"] = "internal_fallback"
        logger.warning("External data not available. Setting validation_mode to 'internal_fallback'.")
    else:
        status["validation_mode"] = "external_validation"
        logger.info("External data available. Proceeding with external validation.")
    
    return status

def calculate_internal_metrics(model: Any, X: Any, y: Any) -> Dict[str, float]:
    """Calculate R² and MAE on internal held-out data."""
    from sklearn.metrics import r2_score, mean_absolute_error
    
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    
    return {"r2": r2, "mae": mae}

def calculate_external_metrics(predictions: List[float], actuals: List[float]) -> Dict[str, float]:
    """Calculate R² and MAE against external experimental data."""
    from sklearn.metrics import r2_score, mean_absolute_error
    
    r2 = r2_score(actuals, predictions)
    mae = mean_absolute_error(actuals, predictions)
    
    return {"r2": r2, "mae": mae}

def run_internal_validation(model: Any, heldout_data: Tuple[Any, Any]) -> Dict[str, Any]:
    """Perform internal validation using held-out DFT data."""
    X, y = heldout_data
    metrics = calculate_internal_metrics(model, X, y)
    logger.info(f"Internal Validation Metrics: R²={metrics['r2']:.4f}, MAE={metrics['mae']:.4f}")
    return {"mode": "internal_fallback", "metrics": metrics}

def run_external_validation(model: Any, external_data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform external validation using experimental onset potentials."""
    # Placeholder for external data processing logic
    # In a real scenario, this would load experimental data and compare
    logger.warning("External validation requested but no external data provided in this context.")
    return {"mode": "external_validation", "metrics": {"r2": None, "mae": None}}

def run_evaluator_pipeline() -> Dict[str, Any]:
    """
    Main pipeline for evaluation.
    Checks data_status.json to determine validation mode.
    """
    status = load_data_status()
    validation_mode = status.get("validation_mode", "internal_fallback")
    
    result = {
        "validation_mode": validation_mode,
        "external_data_available": status.get("external_data_available", False),
        "metrics": {}
    }
    
    try:
        model_artifacts = load_model_artifacts()
        model = model_artifacts.get("model") # Assuming model is pickled or accessible
        heldout_data = load_heldout_data()
        
        if validation_mode == "internal_fallback":
            # T051 Logic: Proceed with internal validation if external is missing
            result["metrics"] = run_internal_validation(model, heldout_data)
        else:
            # Attempt external validation
            # Note: This path is taken only if T050 found data
            result["metrics"] = run_external_validation(model, {}) 
            
    except FileNotFoundError as e:
        logger.error(f"Critical file missing for evaluation: {e}")
        result["error"] = str(e)
    except Exception as e:
        logger.error(f"Evaluation pipeline failed: {e}")
        result["error"] = str(e)
    
    return result

def main():
    """Entry point for the evaluator module."""
    logger.info("Starting Evaluator Pipeline (T051)")
    result = run_evaluator_pipeline()
    
    # Save result to validation directory
    output_path = os.path.join(get_validation_dir(), "evaluation_result.json")
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Evaluation complete. Result saved to {output_path}")
    return result

if __name__ == "__main__":
    main()