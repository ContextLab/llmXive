"""
Evaluator module for calculating performance metrics of the Gap Prediction model.

This module implements evaluation logic to compute Pearson correlation coefficient (r)
and Mean Absolute Error (MAE) between predicted and actual divergence values.
"""

import logging
import json
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr

logger = logging.getLogger(__name__)


class EvaluationResult:
    """Container for evaluation metrics."""
    
    def __init__(
        self,
        pearson_r: float,
        mae: float,
        num_samples: int,
        predictions: Optional[List[float]] = None,
        actuals: Optional[List[float]] = None
    ):
        self.pearson_r = pearson_r
        self.mae = mae
        self.num_samples = num_samples
        self.predictions = predictions
        self.actuals = actuals
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "pearson_r": self.pearson_r,
            "mae": self.mae,
            "num_samples": self.num_samples,
            "predictions": self.predictions,
            "actuals": self.actuals
        }
    
    def __repr__(self) -> str:
        return (
            f"EvaluationResult(pearson_r={self.pearson_r:.4f}, "
            f"mae={self.mae:.4f}, num_samples={self.num_samples})"
        )


def calculate_pearson_correlation(
    predictions: List[float],
    actuals: List[float]
) -> float:
    """
    Calculate Pearson correlation coefficient between predictions and actuals.
    
    Args:
        predictions: List of predicted divergence values.
        actuals: List of actual divergence values.
        
    Returns:
        Pearson correlation coefficient (r) between -1 and 1.
        
    Raises:
        ValueError: If input lists are empty or have different lengths.
    """
    if len(predictions) == 0 or len(actuals) == 0:
        raise ValueError("Input lists cannot be empty")
    
    if len(predictions) != len(actuals):
        raise ValueError(
            f"Predictions and actuals must have same length. "
            f"Got {len(predictions)} and {len(actuals)}"
        )
    
    # Convert to numpy arrays for efficient computation
    pred_array = np.array(predictions)
    actual_array = np.array(actuals)
    
    # Calculate Pearson correlation
    correlation, _ = pearsonr(pred_array, actual_array)
    
    return float(correlation)


def calculate_mae(
    predictions: List[float],
    actuals: List[float]
) -> float:
    """
    Calculate Mean Absolute Error between predictions and actuals.
    
    Args:
        predictions: List of predicted divergence values.
        actuals: List of actual divergence values.
        
    Returns:
        Mean Absolute Error.
        
    Raises:
        ValueError: If input lists are empty or have different lengths.
    """
    if len(predictions) == 0 or len(actuals) == 0:
        raise ValueError("Input lists cannot be empty")
    
    if len(predictions) != len(actuals):
        raise ValueError(
            f"Predictions and actuals must have same length. "
            f"Got {len(predictions)} and {len(actuals)}"
        )
    
    pred_array = np.array(predictions)
    actual_array = np.array(actuals)
    
    mae = np.mean(np.abs(pred_array - actual_array))
    
    return float(mae)


def evaluate_predictions(
    predictions: List[float],
    actuals: List[float]
) -> EvaluationResult:
    """
    Evaluate model predictions against actual values.
    
    This function calculates both Pearson correlation coefficient and MAE
    to assess model performance.
    
    Args:
        predictions: List of predicted divergence values.
        actuals: List of actual divergence values.
        
    Returns:
        EvaluationResult containing all metrics.
        
    Raises:
        ValueError: If input lists are invalid.
    """
    if len(predictions) == 0:
        raise ValueError("Cannot evaluate empty prediction list")
    
    # Calculate metrics
    pearson_r = calculate_pearson_correlation(predictions, actuals)
    mae = calculate_mae(predictions, actuals)
    
    return EvaluationResult(
        pearson_r=pearson_r,
        mae=mae,
        num_samples=len(predictions),
        predictions=predictions,
        actuals=actuals
    )


def load_predictions_from_parquet(
    parquet_path: Path,
    prediction_column: str = "predicted_divergence",
    actual_column: str = "calculated_kl_divergence"
) -> Tuple[List[float], List[float]]:
    """
    Load predictions and actuals from a parquet file.
    
    Args:
        parquet_path: Path to the parquet file containing predictions.
        prediction_column: Name of the column containing predictions.
        actual_column: Name of the column containing actual values.
        
    Returns:
        Tuple of (predictions, actuals) as lists of floats.
        
    Raises:
        FileNotFoundError: If the parquet file doesn't exist.
        KeyError: If specified columns don't exist in the file.
    """
    import pandas as pd
    
    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
    
    df = pd.read_parquet(parquet_path)
    
    if prediction_column not in df.columns:
        raise KeyError(f"Prediction column '{prediction_column}' not found in {parquet_path}")
    
    if actual_column not in df.columns:
        raise KeyError(f"Actual column '{actual_column}' not found in {parquet_path}")
    
    predictions = df[prediction_column].dropna().tolist()
    actuals = df[actual_column].dropna().tolist()
    
    # Ensure both lists have same length after dropping NaN
    min_len = min(len(predictions), len(actuals))
    predictions = predictions[:min_len]
    actuals = actuals[:min_len]
    
    logger.info(
        f"Loaded {len(predictions)} samples from {parquet_path} "
        f"(prediction_col={prediction_column}, actual_col={actual_column})"
    )
    
    return predictions, actuals


def save_evaluation_results(
    result: EvaluationResult,
    output_path: Path
) -> None:
    """
    Save evaluation results to a JSON file.
    
    Args:
        result: EvaluationResult object to save.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)
    
    logger.info(f"Evaluation results saved to {output_path}")


def run_evaluation(
    predictions: List[float],
    actuals: List[float],
    output_path: Optional[Path] = None
) -> EvaluationResult:
    """
    Run full evaluation pipeline and optionally save results.
    
    Args:
        predictions: List of predicted divergence values.
        actuals: List of actual divergence values.
        output_path: Optional path to save results as JSON.
        
    Returns:
        EvaluationResult containing all metrics.
    """
    result = evaluate_predictions(predictions, actuals)
    
    logger.info(
        f"Evaluation complete: Pearson r={result.pearson_r:.4f}, "
        f"MAE={result.mae:.4f}, samples={result.num_samples}"
    )
    
    if output_path:
        save_evaluation_results(result, output_path)
    
    return result
