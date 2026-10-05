"""
Predictor module for inference logic handling out-of-range warnings.

Implements FR-005 (predictions) and Edge Case handling for out-of-range inputs.
"""
import os
import json
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib

from code.utils.logging import get_logger, log_warning_structured
from code.config import ensure_dirs

logger = get_logger(__name__)


def load_model_and_scaler(model_path: str, scaler_path: str) -> Tuple[RandomForestRegressor, StandardScaler]:
    """
    Load the trained model and scaler from disk.
    
    Args:
        model_path: Path to the saved model file (.pkl)
        scaler_path: Path to the saved scaler file (.pkl)
        
    Returns:
        Tuple of (model, scaler)
        
    Raises:
        FileNotFoundError: If model or scaler files do not exist
        RuntimeError: If files cannot be loaded
    """
    model_path = Path(model_path)
    scaler_path = Path(scaler_path)
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not scaler_path.exists():
        raise FileNotFoundError(f"Scaler file not found: {scaler_path}")
        
    try:
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        logger.info(f"Successfully loaded model from {model_path} and scaler from {scaler_path}")
        return model, scaler
    except Exception as e:
        raise RuntimeError(f"Failed to load model or scaler: {e}")


def check_input_ranges(
    input_data: pd.DataFrame, 
    training_stats: Dict[str, Dict[str, float]]
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Check input features against training data ranges and warn about out-of-range values.
    
    Args:
        input_data: DataFrame with input features
        training_stats: Dictionary with 'min' and 'max' for each feature from training data
        
    Returns:
        Tuple of (input_data, list_of_warning_messages)
    """
    warnings_list = []
    
    for feature in input_data.columns:
        if feature not in training_stats:
            logger.warning(f"Feature '{feature}' not found in training statistics. Skipping range check.")
            continue
            
        min_val = training_stats[feature]['min']
        max_val = training_stats[feature]['max']
        
        # Check for values below minimum
        below_min = input_data[input_data[feature] < min_val]
        if len(below_min) > 0:
            count = len(below_min)
            min_obs = below_min[feature].min()
            warning_msg = f"Out-of-range (below min): {count} samples have '{feature}' < {min_val:.4f} (min observed: {min_obs:.4f})"
            warnings_list.append(warning_msg)
            log_warning_structured("OUT_OF_RANGE_BELOW", {
                "feature": feature,
                "threshold": min_val,
                "observed_min": min_obs,
                "count": count
            })
            
        # Check for values above maximum
        above_max = input_data[input_data[feature] > max_val]
        if len(above_max) > 0:
            count = len(above_max)
            max_obs = above_max[feature].max()
            warning_msg = f"Out-of-range (above max): {count} samples have '{feature}' > {max_val:.4f} (max observed: {max_obs:.4f})"
            warnings_list.append(warning_msg)
            log_warning_structured("OUT_OF_RANGE_ABOVE", {
                "feature": feature,
                "threshold": max_val,
                "observed_max": max_obs,
                "count": count
            })
            
    return input_data, warnings_list


def predict_texture(
    model: RandomForestRegressor,
    scaler: StandardScaler,
    input_data: pd.DataFrame,
    training_stats: Dict[str, Dict[str, float]],
    output_path: str,
    new_sample_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Perform inference on input data and save predictions.
    
    Handles out-of-range warnings and saves predictions to CSV.
    
    Args:
        model: Trained RandomForestRegressor model
        scaler: Fitted StandardScaler
        input_data: DataFrame with input features
        training_stats: Dictionary with training data statistics for range checking
        output_path: Path to save predictions.csv
        new_sample_path: Optional path to save new_predictions.csv (for new samples)
        
    Returns:
        DataFrame with predictions
    """
    logger.info(f"Starting prediction for {len(input_data)} samples")
    
    # Check input ranges and collect warnings
    input_data, range_warnings = check_input_ranges(input_data, training_stats)
    
    if range_warnings:
        logger.warning(f"Detected {len(range_warnings)} out-of-range warnings during prediction")
        for w in range_warnings:
            logger.warning(w)
    else:
        logger.info("All input features are within training data ranges")
        
    # Preprocess input data
    try:
        # Ensure columns match training order
        # Note: In a real scenario, we'd need to store feature names with the model
        # For now, we assume input_data columns match the scaler's feature order
        scaled_input = scaler.transform(input_data)
    except Exception as e:
        raise RuntimeError(f"Failed to scale input data: {e}. Ensure columns match training data.")
        
    # Make predictions
    try:
        predictions = model.predict(scaled_input)
    except Exception as e:
        raise RuntimeError(f"Prediction failed: {e}")
        
    # Create output DataFrame
    # Assuming model output corresponds to texture coefficients: {100}, {110}, {111}
    texture_columns = ['texture_100', 'texture_110', 'texture_111']
    if predictions.ndim == 1:
        # Single output - reshape or handle accordingly
        # Assuming multi-output based on trainer.py design
        logger.warning("Model returned 1D predictions, reshaping to 2D")
        predictions = predictions.reshape(-1, 1)
        
    if predictions.shape[1] != len(texture_columns):
        logger.warning(f"Expected {len(texture_columns)} texture outputs, got {predictions.shape[1]}. Adjusting column names.")
        texture_columns = [f'texture_output_{i}' for i in range(predictions.shape[1])]
        
    prediction_df = pd.DataFrame(predictions, columns=texture_columns)
    prediction_df.insert(0, 'sample_id', input_data.index)
    
    # Add original features for reference (optional)
    for col in input_data.columns:
        prediction_df[col] = input_data[col].values
        
    # Save predictions
    output_path = Path(output_path)
    ensure_dirs([output_path])
    
    try:
        prediction_df.to_csv(output_path, index=False)
        logger.info(f"Predictions saved to {output_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to save predictions: {e}")
        
    # Save new_predictions if requested
    if new_sample_path:
        new_sample_path = Path(new_sample_path)
        ensure_dirs([new_sample_path])
        try:
            prediction_df.to_csv(new_sample_path, index=False)
            logger.info(f"New predictions saved to {new_sample_path}")
        except Exception as e:
            logger.error(f"Failed to save new predictions: {e}")
            
    return prediction_df


def run_prediction_pipeline(
    model_path: str,
    scaler_path: str,
    input_data_path: str,
    training_stats_path: str,
    output_predictions_path: str,
    new_predictions_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Run the complete prediction pipeline: load model, check ranges, predict, save.
    
    Args:
        model_path: Path to saved model
        scaler_path: Path to saved scaler
        input_data_path: Path to input data CSV
        training_stats_path: Path to training statistics JSON
        output_predictions_path: Path to save predictions.csv
        new_predictions_path: Optional path for new_predictions.csv
        
    Returns:
        DataFrame with predictions
    """
    logger.info("Starting prediction pipeline")
    
    # Load model and scaler
    model, scaler = load_model_and_scaler(model_path, scaler_path)
    
    # Load input data
    input_path = Path(input_data_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input data not found: {input_path}")
    input_data = pd.read_csv(input_path)
    logger.info(f"Loaded input data with {len(input_data)} samples and {len(input_data.columns)} features")
    
    # Load training statistics
    stats_path = Path(training_stats_path)
    if not stats_path.exists():
        raise FileNotFoundError(f"Training statistics not found: {stats_path}")
    with open(stats_path, 'r') as f:
        training_stats = json.load(f)
    logger.info("Loaded training statistics for range checking")
    
    # Run prediction
    predictions = predict_texture(
        model=model,
        scaler=scaler,
        input_data=input_data,
        training_stats=training_stats,
        output_path=output_predictions_path,
        new_sample_path=new_predictions_path
    )
    
    logger.info("Prediction pipeline completed successfully")
    return predictions


def main():
    """Main entry point for running predictions."""
    # Default paths - can be overridden by config or command line args
    model_path = "data/processed/model.pkl"
    scaler_path = "data/processed/scaler.pkl"
    input_data_path = "data/processed/test_data.csv"
    training_stats_path = "data/processed/training_stats.json"
    output_predictions_path = "data/processed/predictions.csv"
    new_predictions_path = "data/processed/new_predictions.csv"
    
    try:
        run_prediction_pipeline(
            model_path=model_path,
            scaler_path=scaler_path,
            input_data_path=input_data_path,
            training_stats_path=training_stats_path,
            output_predictions_path=output_predictions_path,
            new_predictions_path=new_predictions_path
        )
        logger.info("Prediction script completed successfully")
    except Exception as e:
        logger.error(f"Prediction pipeline failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
