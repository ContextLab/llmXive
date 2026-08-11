import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score

# Import project config utilities
try:
    from config import get_project_root, get_processed_dir, get_validation_dir
except ImportError:
    # Fallback for direct execution context if needed, though standard is via project root
    from pathlib import Path
    import sys
    # Adjust path if running from code/
    if 'code' in str(Path.cwd()):
        sys.path.insert(0, str(Path.cwd().parent))
    from config import get_project_root, get_processed_dir, get_validation_dir

# Import logging utilities
try:
    from utils.logging_config import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)

def load_model_artifacts() -> Dict[str, Any]:
    """
    Load the model artifacts saved in T026.
    Expects: data/processed/model_run.json
    Returns: Dictionary containing model parameters, feature names, and training metadata.
    """
    model_path = get_processed_dir() / "model_run.json"
    if not model_path.exists():
        raise FileNotFoundError(f"Model artifact not found at {model_path}. "
                                "Please ensure T026 has been completed successfully.")
    
    logger.info(f"Loading model artifacts from {model_path}")
    with open(model_path, 'r') as f:
        return json.load(f)

def load_heldout_data() -> pd.DataFrame:
    """
    Load the held-out dataset generated in T018.
    Expects: data/processed/electrolyte_heldout.csv
    Returns: DataFrame with features and target (E_decomp).
    """
    heldout_path = get_processed_dir() / "electrolyte_heldout.csv"
    if not heldout_path.exists():
        raise FileNotFoundError(f"Held-out data not found at {heldout_path}. "
                                "Please ensure T018 has been completed successfully.")
    
    logger.info(f"Loading held-out data from {heldout_path}")
    df = pd.read_csv(heldout_path)
    
    # Verify required columns
    required_cols = ['E_decomp']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Held-out data missing required columns: {missing}")
    
    return df

def calculate_internal_metrics(model_artifacts: Dict[str, Any], 
                               heldout_data: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate MAE and R² for the internal validation set.
    
    Deviation Note:
    - Metric labeled as 'Internal Consistency MAE' to reflect that this is 
      DFT-to-DFT validation, not experimental validation.
    - SC-003 (Experimental MAE) is unmet due to data gap (no experimental onset potentials).
    
    Args:
        model_artifacts: Dictionary from load_model_artifacts containing 'feature_names' and potentially 'model_params'
        heldout_data: DataFrame containing features and 'E_decomp' target
    
    Returns:
        Dictionary with 'mae' and 'r2' scores.
    """
    feature_names = model_artifacts.get('feature_names', [])
    if not feature_names:
        # Fallback: try to infer from dataframe columns excluding target
        feature_names = [c for c in heldout_data.columns if c != 'E_decomp']
    
    # Filter for existing features in case of slight mismatch
    available_features = [f for f in feature_names if f in heldout_data.columns]
    if len(available_features) != len(feature_names):
        missing_features = set(feature_names) - set(available_features)
        logger.warning(f"Missing features in heldout data: {missing_features}. Using available: {available_features}")
    
    X = heldout_data[available_features]
    y = heldout_data['E_decomp']
    
    # Reconstruct model or use stored predictions if available
    # T026 saves model artifacts. We assume the model object is pickled or 
    # we need to reconstruct. Since we don't have the pickle path here, 
    # we assume the 'model_run.json' might contain predictions or we need to reload the model.
    # However, T026 description says "Save model artifacts... to model_run.json". 
    # Usually, sklearn models are pickled. Let's assume the JSON contains metadata 
    # and we need to load the actual model from a pickle if it exists, 
    # OR we rely on the JSON containing the predictions if T026 did that.
    
    # Check if predictions are stored in the JSON (common in lightweight pipelines)
    if 'predictions' in model_artifacts:
        y_pred = np.array(model_artifacts['predictions'])
        if len(y_pred) != len(y):
            raise ValueError(f"Prediction length mismatch: {len(y_pred)} vs {len(y)}")
    else:
        # Try to load the actual model from a pickle file if T026 saved one
        # Convention: data/processed/model.pkl or similar
        # Since T026 only mentions model_run.json, we might need to reconstruct the model 
        # or assume the JSON has the necessary info. 
        # Let's attempt to load a standard pickle if it exists.
        import pickle
        model_path = get_processed_dir() / "model.pkl"
        if model_path.exists():
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            y_pred = model.predict(X)
        else:
            # If no model pickle and no predictions in JSON, we cannot calculate metrics.
            # This implies T026 might have failed to save the model object, only metadata.
            # We raise an error to force a fix in T026 or this task.
            raise FileNotFoundError(
                "Model artifact (model.pkl) not found and predictions not in model_run.json. "
                "T026 must save the trained model object or its predictions."
            )
    
    mae = mean_absolute_error(y, y_pred)
    r2 = r2_score(y, y_pred)
    
    logger.info(f"Internal Validation Metrics - MAE: {mae:.4f}, R²: {r2:.4f}")
    
    return {
        "mae": float(mae),
        "r2": float(r2),
        "metric_label": "Internal Consistency MAE",
        "deviation_note": "SC-003 (Experimental MAE) unmet due to data gap. Using DFT-to-DFT internal validation."
    }

def run_internal_validation() -> Dict[str, Any]:
    """
    Orchestrates the internal validation process for T030.
    """
    logger.info("Starting internal validation (T030)...")
    
    try:
        # 1. Load artifacts
        model_artifacts = load_model_artifacts()
        heldout_data = load_heldout_data()
        
        # 2. Calculate metrics
        metrics = calculate_internal_metrics(model_artifacts, heldout_data)
        
        # 3. Log deviation warning
        logger.warning(metrics.get('deviation_note', ''))
        
        # 4. Save results to a specific output file for T030
        # T030 requirement: "Implement calculation of MAE and R²... Dependency: Read model artifact"
        # We save the results to data/validation/internal_validation_metrics.json
        output_dir = get_validation_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "internal_validation_metrics.json"
        
        result_payload = {
            "task_id": "T030",
            "description": "Internal Consistency Validation",
            "metrics": metrics,
            "sample_size": len(heldout_data),
            "timestamp": pd.Timestamp.now().isoformat()
        }
        
        with open(output_path, 'w') as f:
            json.dump(result_payload, f, indent=2)
        
        logger.info(f"Internal validation metrics saved to {output_path}")
        return result_payload
        
    except Exception as e:
        logger.error(f"Internal validation failed: {str(e)}", exc_info=True)
        raise

def run_evaluator_pipeline() -> Dict[str, Any]:
    """
    Main entry point for the evaluator module.
    Currently focuses on T030 (Internal Validation).
    Can be extended for sensitivity analysis (T031) later.
    """
    return run_internal_validation()

if __name__ == "__main__":
    # Run when executed directly
    result = run_evaluator_pipeline()
    print(json.dumps(result, indent=2))
