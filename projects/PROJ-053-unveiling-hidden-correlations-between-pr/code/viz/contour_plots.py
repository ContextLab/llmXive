import os
import json
import logging
import numpy as np
import matplotlib.pyplot as plt
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from config import get_processed_data_dir, get_figures_dir, get_models_dir, get_results_dir, ensure_directories
from utils.logger import setup_logging

logger = logging.getLogger(__name__)

# Physical unit mapping for axes based on domain knowledge of AM parameters
PHYSICAL_UNITS = {
    'laser_power': 'W',
    'scan_speed': 'mm/s',
    'layer_thickness': 'mm',
    'yield_strength': 'MPa',
    'ductility': '%',
    'energy_density': 'J/mm^3',
    'line_energy': 'J/mm'
}

def load_normalization_bounds(bounds_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load normalization bounds from JSON file.
    
    Args:
        bounds_path: Optional path to bounds file. If None, uses default path.
        
    Returns:
        Dictionary containing normalization bounds.
    """
    if bounds_path is None:
        bounds_path = os.path.join(get_results_dir(), 'normalization_bounds.json')
    
    if not os.path.exists(bounds_path):
        raise FileNotFoundError(f"Normalization bounds file not found at {bounds_path}")
    
    with open(bounds_path, 'r') as f:
        bounds = json.load(f)
    
    logger.info(f"Loaded normalization bounds from {bounds_path}")
    return bounds

def load_processed_test_data(data_path: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load processed test data (features, targets, original indices).
    
    Args:
        data_path: Optional path to test data. If None, uses default path.
        
    Returns:
        Tuple of (features, targets, indices)
    """
    if data_path is None:
        data_path = os.path.join(get_processed_data_dir(), 'test_data.pkl')
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Test data file not found at {data_path}")
    
    with open(data_path, 'rb') as f:
        data = pickle.load(f)
    
    logger.info(f"Loaded test data from {data_path}")
    return data['features'], data['targets'], data['indices']

def load_model(model_path: Optional[str] = None) -> Any:
    """
    Load trained GPR model.
    
    Args:
        model_path: Optional path to model file. If None, uses default path.
        
    Returns:
        Trained GPR model object.
    """
    if model_path is None:
        model_path = os.path.join(get_models_dir(), 'gpr_model.pkl')
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    logger.info(f"Loaded model from {model_path}")
    return model

def generate_contour_grid(bounds: Dict[str, Any], feature_names: list, 
                          n_points: int = 100) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate a grid for contour plotting based on normalization bounds.
    
    Args:
        bounds: Normalization bounds dictionary.
        feature_names: List of feature names.
        n_points: Number of points per dimension.
        
    Returns:
        Tuple of (X_grid, Y_grid, X_denorm, Y_denorm)
    """
    # Assume first two features are laser_power and scan_speed
    if len(feature_names) < 2:
        raise ValueError("Need at least 2 features for contour plotting")
    
    x_feature = feature_names[0]
    y_feature = feature_names[1]
    
    # Get bounds for these features
    x_min = bounds.get(x_feature, {}).get('min', 0)
    x_max = bounds.get(x_feature, {}).get('max', 1)
    y_min = bounds.get(y_feature, {}).get('min', 0)
    y_max = bounds.get(y_feature, {}).get('max', 1)
    
    # Create grid
    x = np.linspace(x_min, x_max, n_points)
    y = np.linspace(y_min, y_max, n_points)
    X_grid, Y_grid = np.meshgrid(x, y)
    
    # Denormalize for display (if bounds contain original ranges)
    # For now, we'll use the normalized grid and annotate axes with physical units
    X_denorm = X_grid
    Y_denorm = Y_grid
    
    return X_grid, Y_grid, X_denorm, Y_denorm

def predict_with_uncertainty(model: Any, X_grid: np.ndarray, Y_grid: np.ndarray, 
                             feature_names: list) -> Tuple[np.ndarray, np.ndarray]:
    """
    Predict values and uncertainty on a grid.
    
    Args:
        model: Trained GPR model.
        X_grid: X coordinate grid.
        Y_grid: Y coordinate grid.
        feature_names: List of feature names.
        
    Returns:
        Tuple of (predictions, uncertainties)
    """
    # Flatten grids
    X_flat = X_grid.flatten()
    Y_flat = Y_grid.flatten()
    
    # Create feature matrix (assuming other features are fixed at mean or 0.5 normalized)
    n_features = len(feature_names)
    grid_points = np.column_stack([X_flat, Y_flat])
    
    # Pad with fixed values for other features (assuming 0.5 normalized)
    if n_features > 2:
        padding = np.full((len(X_flat), n_features - 2), 0.5)
        grid_points = np.hstack([grid_points, padding])
    
    # Predict with uncertainty
    mean, std = model.predict(grid_points, return_std=True)
    
    # Reshape to grid
    predictions = mean.reshape(X_grid.shape)
    uncertainties = std.reshape(X_grid.shape)
    
    return predictions, uncertainties

def create_contour_plot(predictions: np.ndarray, X_grid: np.ndarray, Y_grid: np.ndarray,
                        feature_names: list, target_name: str = 'yield_strength',
                        output_path: Optional[str] = None) -> str:
    """
    Create a contour plot of predictions with physical unit annotations.
    
    Args:
        predictions: Predicted values on grid.
        X_grid: X coordinate grid.
        Y_grid: Y coordinate grid.
        feature_names: List of feature names.
        target_name: Name of target variable.
        output_path: Optional output path for figure.
        
    Returns:
        Path to saved figure.
    """
    ensure_directories()
    
    # Get physical units for axes
    x_unit = PHYSICAL_UNITS.get(feature_names[0], '')
    y_unit = PHYSICAL_UNITS.get(feature_names[1], '')
    target_unit = PHYSICAL_UNITS.get(target_name, '')
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create contour plot
    contour = ax.contourf(X_grid, Y_grid, predictions, levels=20, cmap='viridis')
    plt.colorbar(contour, ax=ax, label=f'{target_name} ({target_unit})')
    
    # Annotate axes with physical units
    ax.set_xlabel(f'{feature_names[0].replace("_", " ").title()} ({x_unit})')
    ax.set_ylabel(f'{feature_names[1].replace("_", " ").title()} ({y_unit})')
    ax.set_title(f'Predicted {target_name.replace("_", " ").title()} vs Processing Parameters')
    
    # Save figure
    if output_path is None:
        output_path = os.path.join(get_figures_dir(), f'{target_name}_contour.png')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Saved contour plot to {output_path}")
    return output_path

def create_uncertainty_heatmap(uncertainties: np.ndarray, X_grid: np.ndarray, Y_grid: np.ndarray,
                               feature_names: list, target_name: str = 'yield_strength',
                               output_path: Optional[str] = None) -> str:
    """
    Create an uncertainty heatmap with physical unit annotations.
    
    Args:
        uncertainties: Uncertainty values on grid.
        X_grid: X coordinate grid.
        Y_grid: Y coordinate grid.
        feature_names: List of feature names.
        target_name: Name of target variable.
        output_path: Optional output path for figure.
        
    Returns:
        Path to saved figure.
    """
    ensure_directories()
    
    # Get physical units for axes
    x_unit = PHYSICAL_UNITS.get(feature_names[0], '')
    y_unit = PHYSICAL_UNITS.get(feature_names[1], '')
    
    # Calculate median uncertainty for threshold
    median_uncertainty = np.median(uncertainties)
    high_uncertainty_threshold = 2 * median_uncertainty
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create heatmap with custom colormap for high uncertainty
    # Low uncertainty: blue to green, high uncertainty: red
    cmap = plt.cm.viridis
    scatter = ax.scatter(X_grid.flatten(), Y_grid.flatten(), 
                        c=uncertainties.flatten(), cmap=cmap, s=1)
    
    # Add threshold indicator
    if high_uncertainty_threshold > 0:
        # Highlight regions with high uncertainty
        high_unc_mask = uncertainties > high_uncertainty_threshold
        if np.any(high_unc_mask):
            ax.contour(X_grid, Y_grid, high_unc_mask.astype(int), 
                      colors=['red'], linewidths=2, linestyles='--')
    
    plt.colorbar(scatter, ax=ax, label='Prediction Uncertainty (σ)')
    
    # Annotate axes with physical units
    ax.set_xlabel(f'{feature_names[0].replace("_", " ").title()} ({x_unit})')
    ax.set_ylabel(f'{feature_names[1].replace("_", " ").title()} ({y_unit})')
    ax.set_title(f'Uncertainty Heatmap for {target_name.replace("_", " ").title()} Predictions')
    
    # Add legend for high uncertainty regions
    if high_uncertainty_threshold > 0 and np.any(high_unc_mask):
        ax.plot([], [], 'r--', linewidth=2, label=f'σ > 2× median ({high_uncertainty_threshold:.4f})')
        ax.legend()
    
    # Save figure
    if output_path is None:
        output_path = os.path.join(get_figures_dir(), f'{target_name}_uncertainty_heatmap.png')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Saved uncertainty heatmap to {output_path}")
    return output_path

def main():
    """Main function to generate contour plots with physical unit annotations."""
    # Setup logging
    setup_logging()
    
    try:
        # Load necessary components
        bounds = load_normalization_bounds()
        test_features, test_targets, test_indices = load_processed_test_data()
        model = load_model()
        
        # Get feature names (assuming they match the order in bounds)
        feature_names = list(bounds.keys())
        if len(feature_names) < 2:
            logger.error("Need at least 2 features for contour plotting")
            return
        
        # Generate contour grid
        X_grid, Y_grid, X_denorm, Y_denorm = generate_contour_grid(bounds, feature_names)
        
        # Predict with uncertainty
        predictions, uncertainties = predict_with_uncertainty(model, X_grid, Y_grid, feature_names)
        
        # Create contour plot for yield_strength
        target_name = 'yield_strength'
        contour_path = create_contour_plot(predictions, X_grid, Y_grid, feature_names, 
                                          target_name=target_name)
        logger.info(f"Created contour plot: {contour_path}")
        
        # Create uncertainty heatmap
        heatmap_path = create_uncertainty_heatmap(uncertainties, X_grid, Y_grid, feature_names, 
                                                 target_name=target_name)
        logger.info(f"Created uncertainty heatmap: {heatmap_path}")
        
        logger.info("Successfully generated visualizations with physical unit annotations")
        
    except Exception as e:
        logger.error(f"Error generating visualizations: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()