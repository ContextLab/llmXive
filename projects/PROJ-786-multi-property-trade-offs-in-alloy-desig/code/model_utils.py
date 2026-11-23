"""
Utility functions for model predictions, including physical clamping and extrapolation detection.
"""
import logging
import numpy as np
from typing import Tuple, Optional, List, Dict, Any
from scipy.spatial import ConvexHull, Delaunay

from utils.logging_config import log_info_with_context, log_warning_with_context, log_error_with_context
from utils.convex_hull import ConvexHullWrapper

logger = logging.getLogger(__name__)

def clamp_predictions(
    predictions: np.ndarray,
    lower_bound: float = 0.0,
    upper_bound: Optional[float] = None,
    property_name: str = "modulus"
) -> np.ndarray:
    """
    Clamps prediction values to physical limits.
    
    Args:
        predictions: Array of predicted values.
        lower_bound: Minimum physically allowed value (default 0.0 for moduli).
        upper_bound: Maximum physically allowed value (optional).
        property_name: Name of the property for logging.
        
    Returns:
        Clamped array of predictions.
    """
    original_predictions = predictions.copy()
    clamped = np.clip(predictions, lower_bound, upper_bound)
    
    clamped_count = np.sum(clamped != original_predictions)
    if clamped_count > 0:
        log_warning_with_context(
            f"Clamped {clamped_count} {property_name} predictions to physical limits.",
            {
                "original_min": float(np.min(original_predictions)),
                "original_max": float(np.max(original_predictions)),
                "clamped_min": float(np.min(clamped)),
                "clamped_max": float(np.max(clamped)),
                "lower_bound": lower_bound,
                "upper_bound": upper_bound
            }
        )
    
    return clamped

def test_extrapolation(
    feature_matrix: np.ndarray,
    training_features: np.ndarray,
    tolerance: float = 0.05
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Tests if new feature points lie outside the convex hull of the training data.
    
    Args:
        feature_matrix: Array of shape (n_samples, n_features) to test.
        training_features: Array of shape (n_train, n_features) defining the hull.
        tolerance: Fractional tolerance for hull expansion (default 0.05).
        
    Returns:
        Tuple of:
        - is_extrapolated: Boolean array indicating which points are extrapolated.
        - stats: Dictionary with extrapolation statistics.
    """
    if training_features.shape[0] < training_features.shape[1] + 1:
        log_error_with_context(
            "Training data insufficient to compute convex hull for extrapolation check.",
            {"training_samples": training_features.shape[0], "n_features": training_features.shape[1]}
        )
        # If we can't compute a hull, we assume all points are potentially extrapolated
        return np.ones(feature_matrix.shape[0], dtype=bool), {
            "reason": "insufficient_training_data",
            "extrapolated_count": feature_matrix.shape[0],
            "total_points": feature_matrix.shape[0]
        }

    try:
        hull = ConvexHull(training_features)
        delaunay = Delaunay(training_features)
        
        # Check points
        # Note: Delaunay.find_simplex returns -1 for points outside the hull
        simplexes = delaunay.find_simplex(feature_matrix)
        is_extrapolated = simplexes == -1
        
        extrapolated_count = int(np.sum(is_extrapolated))
        total_count = feature_matrix.shape[0]
        percentage = (extrapolated_count / total_count * 100) if total_count > 0 else 0.0
        
        log_info_with_context(
            f"Extrapolation check complete: {extrapolated_count}/{total_count} points ({percentage:.2f}%) outside training hull.",
            {
                "n_training_samples": training_features.shape[0],
                "n_features": training_features.shape[1],
                "extrapolated_count": extrapolated_count,
                "total_points": total_count,
                "percentage_extrapolated": percentage
            }
        )
        
        return is_extrapolated, {
            "reason": "outside_convex_hull",
            "extrapolated_count": extrapolated_count,
            "total_points": total_count,
            "percentage_extrapolated": percentage
        }
        
    except Exception as e:
        log_error_with_context(
            f"Failed to compute convex hull for extrapolation check: {str(e)}",
            {"error": str(e)}
        )
        # If hull computation fails, assume all points are extrapolated to be safe
        return np.ones(feature_matrix.shape[0], dtype=bool), {
            "reason": "hull_computation_failed",
            "error": str(e),
            "extrapolated_count": feature_matrix.shape[0],
            "total_points": feature_matrix.shape[0]
        }

def process_model_predictions(
    raw_predictions: np.ndarray,
    feature_matrix: np.ndarray,
    training_features: np.ndarray,
    property_name: str,
    lower_bound: float = 0.0,
    upper_bound: Optional[float] = None
) -> Dict[str, Any]:
    """
    Comprehensive pipeline to clamp predictions and flag extrapolation.
    
    Args:
        raw_predictions: Raw model predictions.
        feature_matrix: Feature matrix for the predictions.
        training_features: Training feature matrix for hull construction.
        property_name: Name of the property for logging.
        lower_bound: Physical lower bound.
        upper_bound: Physical upper bound.
        
    Returns:
        Dictionary with processed predictions and metadata.
    """
    # Step 1: Check extrapolation
    is_extrapolated, extrap_stats = test_extrapolation(
        feature_matrix, training_features
    )
    
    # Step 2: Clamp predictions
    clamped_predictions = clamp_predictions(
        raw_predictions, lower_bound, upper_bound, property_name
    )
    
    return {
        "raw_predictions": raw_predictions,
        "clamped_predictions": clamped_predictions,
        "is_extrapolated": is_extrapolated,
        "extrapolation_stats": extrap_stats,
        "property_name": property_name
    }
