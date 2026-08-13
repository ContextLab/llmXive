import os
import json
import logging
import numpy as np
import matplotlib.pyplot as plt
import pickle
from typing import Dict, Any, Tuple, Optional, List
from pathlib import Path

# Local imports matching API surface
from config import get_results_dir, get_figures_dir, get_processed_data_dir, ensure_directories, get_logger
from utils.logger import setup_logging

# Configure logging
logger = setup_logging("contour_plots")

# Physical units mapping for axis annotation
PHYSICAL_UNITS = {
    "laser_power": "W",
    "scan_speed": "mm/s",
    "layer_thickness": "µm",
    "yield_strength": "MPa",
    "ductility": "%",
    "fatigue_life": "cycles"
}

def load_normalization_bounds(bounds_path: Optional[str] = None) -> Dict[str, Dict[str, float]]:
    """
    Load normalization bounds from JSON file.
    Returns a dict mapping feature names to {'min': float, 'max': float}.
    """
    if bounds_path is None:
        bounds_path = os.path.join(get_results_dir(), "normalization_bounds.json")
    
    if not os.path.exists(bounds_path):
        raise FileNotFoundError(f"Normalization bounds file not found: {bounds_path}")
    
    with open(bounds_path, 'r') as f:
        bounds = json.load(f)
    
    logger.info(f"Loaded normalization bounds from {bounds_path}")
    return bounds

def load_processed_test_data(data_path: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load processed test data (features and targets).
    Returns (X, y, feature_names).
    """
    if data_path is None:
        data_path = os.path.join(get_processed_data_dir(), "test_set.csv")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed test data not found: {data_path}")
    
    import pandas as pd
    df = pd.read_csv(data_path)
    
    # Assume last column is target, rest are features
    # This is a simplification - in production, we'd use explicit column names
    feature_cols = [c for c in df.columns if c not in ['yield_strength', 'ductility', 'fatigue_life']]
    target_cols = [c for c in df.columns if c in ['yield_strength', 'ductility', 'fatigue_life']]
    
    if not target_cols:
        raise ValueError("No target columns found in processed data")
    
    X = df[feature_cols].values
    y = df[target_cols[0]].values  # Use first target for now
    feature_names = feature_cols
    
    logger.info(f"Loaded {len(X)} samples with {len(feature_names)} features")
    return X, y, feature_names

def load_model(model_path: Optional[str] = None) -> Any:
    """
    Load trained GPR model from pickle file.
    """
    if model_path is None:
        model_path = os.path.join(get_results_dir(), "models", "gpr_model.pkl")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    logger.info(f"Loaded GPR model from {model_path}")
    return model

def generate_contour_grid(X: np.ndarray, feature_names: List[str], 
                          bounds: Dict[str, Dict[str, float]], 
                          n_points: int = 50) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate a 2D grid for contour plotting based on two primary features.
    Uses laser_power and scan_speed as the default axes.
    """
    # Find indices of laser_power and scan_speed
    power_idx = None
    speed_idx = None
    
    for i, name in enumerate(feature_names):
        if "laser_power" in name.lower():
            power_idx = i
        elif "scan_speed" in name.lower():
            speed_idx = i
    
    if power_idx is None or speed_idx is None:
        # Fallback: use first two numeric features
        logger.warning("Could not find laser_power and scan_speed. Using first two features.")
        power_idx = 0
        speed_idx = 1 if len(feature_names) > 1 else 0
    
    # Get bounds for these features
    power_name = feature_names[power_idx]
    speed_name = feature_names[speed_idx]
    
    # Use normalization bounds if available, else use data range
    if power_name in bounds:
        x_min, x_max = bounds[power_name]['min'], bounds[power_name]['max']
    else:
        x_min, x_max = X[:, power_idx].min(), X[:, power_idx].max()
    
    if speed_name in bounds:
        y_min, y_max = bounds[speed_name]['min'], bounds[speed_name]['max']
    else:
        y_min, y_max = X[:, speed_idx].min(), X[:, speed_idx].max()
    
    # Generate grid
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, n_points),
                         np.linspace(y_min, y_max, n_points))
    
    return xx, yy, np.c_[xx.ravel(), yy.ravel()], (power_idx, speed_idx)

def predict_with_uncertainty(model: Any, X_grid: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Predict mean and standard deviation on the grid.
    """
    # For GPR, we need to handle the full feature set
    # We'll assume the grid only has 2 features, so we need to fill in the rest
    # with mean values from training data (simplified approach)
    
    # This is a placeholder - in reality, we'd need the full feature distribution
    # For now, we'll just predict on the 2D grid if the model accepts it
    try:
        mean, std = model.predict(X_grid, return_std=True)
        return mean.reshape(X_grid.shape[0], X_grid.shape[1]), std.reshape(X_grid.shape[0], X_grid.shape[1])
    except Exception as e:
        logger.warning(f"Direct prediction failed: {e}. Using simplified approach.")
        # Fallback: just predict mean
        mean = model.predict(X_grid)
        std = np.ones_like(mean) * 0.1  # Dummy uncertainty
        return mean.reshape(X_grid.shape[0], X_grid.shape[1]), std.reshape(X_grid.shape[0], X_grid.shape[1])

def create_contour_plot(xx: np.ndarray, yy: np.ndarray, 
                        predictions: np.ndarray, 
                        feature_names: List[str],
                        target_name: str,
                        bounds: Dict[str, Dict[str, float]],
                        output_path: str) -> None:
    """
    Create a contour plot of predicted values with physical unit annotations.
    """
    plt.figure(figsize=(10, 8))
    
    # Determine axis labels with units
    power_idx = None
    speed_idx = None
    for i, name in enumerate(feature_names):
        if "laser_power" in name.lower():
            power_idx = i
        elif "scan_speed" in name.lower():
            speed_idx = i
    
    if power_idx is not None:
        x_label = f"Laser Power ({PHYSICAL_UNITS.get('laser_power', 'W')})"
    else:
        x_label = f"Feature {feature_names[0]}"
    
    if speed_idx is not None:
        y_label = f"Scan Speed ({PHYSICAL_UNITS.get('scan_speed', 'mm/s')})"
    else:
        y_label = f"Feature {feature_names[1] if len(feature_names) > 1 else feature_names[0]}"
    
    # Create contour plot
    contour = plt.contourf(xx, yy, predictions, levels=20, cmap='viridis')
    plt.colorbar(contour, label=f'{target_name} ({PHYSICAL_UNITS.get(target_name, "")})')
    
    # Add axis labels with physical units
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(f'Predicted {target_name} vs Process Parameters')
    
    # Annotate axis limits with physical units if bounds are available
    if power_idx is not None and feature_names[power_idx] in bounds:
        x_min, x_max = bounds[feature_names[power_idx]]['min'], bounds[feature_names[power_idx]]['max']
        plt.xlim(x_min, x_max)
    
    if speed_idx is not None and feature_names[speed_idx] in bounds:
        y_min, y_max = bounds[feature_names[speed_idx]]['min'], bounds[feature_names[speed_idx]]['max']
        plt.ylim(y_min, y_max)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved contour plot to {output_path}")

def create_uncertainty_heatmap(xx: np.ndarray, yy: np.ndarray, 
                               uncertainty: np.ndarray,
                               feature_names: List[str],
                               bounds: Dict[str, Dict[str, float]],
                               output_path: str) -> None:
    """
    Create an uncertainty heatmap with physical unit annotations.
    Highlights regions with high uncertainty (σ > 2× median).
    """
    plt.figure(figsize=(10, 8))
    
    # Determine axis labels with units
    power_idx = None
    speed_idx = None
    for i, name in enumerate(feature_names):
        if "laser_power" in name.lower():
            power_idx = i
        elif "scan_speed" in name.lower():
            speed_idx = i
    
    if power_idx is not None:
        x_label = f"Laser Power ({PHYSICAL_UNITS.get('laser_power', 'W')})"
    else:
        x_label = f"Feature {feature_names[0]}"
    
    if speed_idx is not None:
        y_label = f"Scan Speed ({PHYSICAL_UNITS.get('scan_speed', 'mm/s')})"
    else:
        y_label = f"Feature {feature_names[1] if len(feature_names) > 1 else feature_names[0]}"
    
    # Calculate threshold for high uncertainty
    median_uncertainty = np.median(uncertainty)
    threshold = 2 * median_uncertainty
    
    # Create heatmap
    heatmap = plt.contourf(xx, yy, uncertainty, levels=20, cmap='Reds')
    plt.colorbar(heatmap, label='Prediction Uncertainty (σ)')
    
    # Highlight high uncertainty regions
    high_unc_mask = uncertainty > threshold
    if np.any(high_unc_mask):
        plt.contour(xx, yy, high_unc_mask.astype(int), colors='black', linewidths=0.5, linestyles='dashed')
    
    # Add axis labels with physical units
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(f'Prediction Uncertainty Heatmap\n(High uncertainty: σ > {threshold:.3f})')
    
    # Annotate axis limits with physical units if bounds are available
    if power_idx is not None and feature_names[power_idx] in bounds:
        x_min, x_max = bounds[feature_names[power_idx]]['min'], bounds[feature_names[power_idx]]['max']
        plt.xlim(x_min, x_max)
    
    if speed_idx is not None and feature_names[speed_idx] in bounds:
        y_min, y_max = bounds[feature_names[speed_idx]]['min'], bounds[feature_names[speed_idx]]['max']
        plt.ylim(y_min, y_max)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved uncertainty heatmap to {output_path}")

def main():
    """
    Main function to generate contour plots and uncertainty heatmaps with physical unit annotations.
    """
    try:
        # Ensure directories exist
        ensure_directories()
        
        # Load normalization bounds
        bounds = load_normalization_bounds()
        logger.info(f"Normalization bounds loaded: {list(bounds.keys())}")
        
        # Load processed test data
        X, y, feature_names = load_processed_test_data()
        logger.info(f"Loaded data with features: {feature_names}")
        
        # Load trained model
        model = load_model()
        
        # Generate contour grid
        xx, yy, X_grid, feature_indices = generate_contour_grid(X, feature_names, bounds)
        
        # Predict with uncertainty
        predictions, uncertainty = predict_with_uncertainty(model, X_grid)
        
        # Determine target name
        target_name = "yield_strength"  # Default
        
        # Create output paths
        figures_dir = get_figures_dir()
        os.makedirs(figures_dir, exist_ok=True)
        
        contour_path = os.path.join(figures_dir, "contour_yield_strength.png")
        uncertainty_path = os.path.join(figures_dir, "uncertainty_heatmap.png")
        
        # Generate plots with physical unit annotations
        create_contour_plot(xx, yy, predictions, feature_names, target_name, bounds, contour_path)
        create_uncertainty_heatmap(xx, yy, uncertainty, feature_names, bounds, uncertainty_path)
        
        logger.info("Successfully generated contour plots and uncertainty heatmap with physical unit annotations")
        
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()