import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd

# Import project configuration
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_processed_dir, get_validation_dir, get_project_root

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def load_model_artifacts() -> Dict[str, Any]:
    """
    Loads the model artifacts from data/processed/model_run.json.
    
    Returns:
        Dict containing model parameters, CV scores, and bin importance data.
    """
    processed_dir = get_processed_dir()
    model_run_path = processed_dir / "model_run.json"
    
    if not model_run_path.exists():
        raise FileNotFoundError(f"Model artifacts not found at {model_run_path}. "
                                "Ensure T026 (Model Saver) has been executed.")
    
    with open(model_run_path, 'r') as f:
        return json.load(f)

def load_heldout_data() -> pd.DataFrame:
    """
    Loads the held-out dataset from data/processed/electrolyte_heldout.csv.
    
    Returns:
        DataFrame containing features and targets for the held-out set.
    """
    processed_dir = get_processed_dir()
    heldout_path = processed_dir / "electrolyte_heldout.csv"
    
    if not heldout_path.exists():
        raise FileNotFoundError(f"Held-out data not found at {heldout_path}. "
                                "Ensure T018 (Data Split) has been executed.")
    
    return pd.read_csv(heldout_path)

def calculate_internal_metrics(model_artifacts: Dict[str, Any], 
                               heldout_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculates MAE and R² for the internal validation set (held-out DFT data).
    
    **Deviation Note**: 
    This metric is labeled 'Internal Consistency MAE' and 'Internal Consistency R²'.
    SC-003 (Experimental MAE) and FR-006 (External Validation) are unmet due to 
    the unavailability of experimental onset potential datasets. This function
    performs validation against the held-out DFT set as a fallback.
    
    Args:
        model_artifacts: Dict loaded from model_run.json (contains model params).
        heldout_data: DataFrame with features and 'target' column.
        
    Returns:
        Dict with calculated metrics.
    """
    # We need to reconstruct the prediction logic or load predictions if stored.
    # Since the model artifacts in T026 are a summary (JSON) and not the sklearn object,
    # and the task T030 asks to calculate metrics based on the artifact, we assume
    # the 'cv_score' in the artifact is the primary metric, but we must calculate
    # specific MAE/R2 on the held-out set.
    
    # However, without the actual sklearn model object (pkl), we cannot predict 
    # on the held-out set unless we re-train or the artifacts store predictions.
    # Looking at T026 description: "Save model artifacts, R² scores... to model_run.json".
    # The provided model_run.json in the prompt is a summary, not a full model dump.
    # To satisfy the requirement "Read model artifact... Implement calculation of MAE/R2",
    # we must assume the pipeline re-trains or the artifact includes the model.
    # BUT, T030 specifically says "Read model artifact from data/processed/model_run.json".
    # If the artifact doesn't contain the model weights, we cannot predict.
    
    # Correction: The task T022/T026 implies saving the model. The provided JSON is a summary.
    # To make T030 workable as a standalone task reading the artifact, we have two options:
    # 1. Assume the 'model_run.json' in the real pipeline includes the model (not shown in prompt).
    # 2. Re-implement the training logic here to generate predictions for the held-out set,
    #    using the parameters found in the artifact.
    
    # Given the constraint "Read model artifact", and the fact that the artifact contains
    # the hyperparameters (n_estimators, max_depth, random_state), we will re-instantiate
    # the model with these parameters to generate predictions on the held-out set.
    # This ensures the metrics reflect the exact model configuration stored in the artifact.
    
    try:
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.metrics import mean_absolute_error, r2_score
    except ImportError:
        logger.error("scikit-learn is required for metric calculation.")
        raise

    # Extract parameters from the artifact
    params = model_artifacts.get("params", {})
    n_estimators = params.get("n_estimators", 100)
    max_depth = params.get("max_depth", None)
    random_state = params.get("random_state", 42)

    # Prepare data
    # Assuming the heldout_data has feature columns and a 'target' or 'decomp_energy' column.
    # Based on T018/T019, the target is likely 'target' or 'decomp_energy'.
    # We check for common names.
    target_col = None
    for col in ['target', 'decomp_energy', 'y']:
        if col in heldout_data.columns:
            target_col = col
            break
    
    if not target_col:
        raise ValueError(f"Could not find target column in heldout_data. Columns: {heldout_data.columns.tolist()}")

    feature_cols = [c for c in heldout_data.columns if c != target_col]
    X_heldout = heldout_data[feature_cols].values
    y_heldout = heldout_data[target_col].values

    # Re-train the model on the training set to predict on held-out?
    # No, we don't have the training set here. We only have the artifact and held-out.
    # If the model was trained on the full data (minus held-out), we need that training data.
    # Let's load the full processed features to split again or assume the artifact implies
    # the model was trained on the training split.
    
    # Alternative: The task T030 might be expecting us to calculate metrics based on 
    # the CV score provided in the artifact if no held-out prediction is possible.
    # BUT the task says "Calculate MAE and R2 for the internal validation set".
    # This implies we must have predictions for the held-out set.
    
    # To do this properly without the training set in this function, we must load it.
    processed_dir = get_processed_dir()
    features_path = processed_dir / "electrolyte_features.csv"
    
    if not features_path.exists():
        raise FileNotFoundError(f"Full feature set not found at {features_path}.")
    
    full_data = pd.read_csv(features_path)
    
    # We need to identify which rows are in the held-out set to train on the rest.
    # We assume there is a 'split' column or we can match by ID.
    # If no split column, we assume the heldout_data is a subset of features_data.
    # We will use a simple heuristic: if 'molecule_id' exists, use it to mask.
    
    id_col = None
    if 'molecule_id' in full_data.columns:
        id_col = 'molecule_id'
    elif 'id' in full_data.columns:
        id_col = 'id'
    
    if id_col and id_col in heldout_data.columns:
        heldout_ids = set(heldout_data[id_col].values)
        train_mask = ~full_data[id_col].isin(heldout_ids)
        X_train = full_data[train_mask][feature_cols].values
        y_train = full_data[train_mask][target_col].values
    else:
        # Fallback: Assume the first 80% is train (not ideal, but necessary if no ID)
        # Or assume the heldout_data is the test set and we must re-split full_data similarly?
        # Let's assume the 'split' column exists from T018.
        if 'split' in full_data.columns:
            train_mask = full_data['split'] == 'train'
            X_train = full_data[train_mask][feature_cols].values
            y_train = full_data[train_mask][target_col].values
        else:
            # Last resort: Re-split using the same ratio as T018 (assumed 80/20)
            # This is risky but allows the code to run.
            logger.warning("No ID or split column found. Re-splitting data deterministically.")
            np.random.seed(random_state)
            indices = np.random.permutation(len(full_data))
            split_idx = int(0.8 * len(full_data))
            train_indices = indices[:split_idx]
            X_train = full_data.iloc[train_indices][feature_cols].values
            y_train = full_data.iloc[train_indices][target_col].values

    # Train the model with the exact parameters from the artifact
    logger.info(f"Re-training model with params: {params} to generate predictions for held-out set.")
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state
    )
    model.fit(X_train, y_train)
    
    # Predict
    y_pred = model.predict(X_heldout)
    
    # Calculate metrics
    mae = mean_absolute_error(y_heldout, y_pred)
    r2 = r2_score(y_heldout, y_pred)
    
    return {
        "metric_type": "Internal Consistency",
        "mae": float(mae),
        "r2": float(r2),
        "n_samples": len(y_heldout),
        "deviation_note": "SC-003 (Experimental MAE) unmet. Using Internal DFT Validation.",
        "model_params_used": params
    }

def run_internal_validation() -> Dict[str, Any]:
    """
    Orchestrates the loading of artifacts and calculation of internal metrics.
    
    Returns:
        Dict containing the calculated metrics.
    """
    logger.info("Starting internal validation (T030).")
    
    model_artifacts = load_model_artifacts()
    heldout_data = load_heldout_data()
    
    metrics = calculate_internal_metrics(model_artifacts, heldout_data)
    
    logger.info(f"Internal Validation Complete - MAE: {metrics['mae']:.4f}, R2: {metrics['r2']:.4f}")
    return metrics

def run_evaluator_pipeline() -> Dict[str, Any]:
    """
    Main entry point for the evaluator pipeline.
    Currently focuses on T030: Internal Validation Metrics.
    """
    return run_internal_validation()

if __name__ == "__main__":
    results = run_evaluator_pipeline()
    print(json.dumps(results, indent=2))
