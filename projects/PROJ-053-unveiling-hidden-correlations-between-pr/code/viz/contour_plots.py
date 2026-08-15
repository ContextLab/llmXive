import os
import json
import logging
import numpy as np
import matplotlib.pyplot as plt
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from config import get_processed_data_dir, get_figures_dir, get_results_dir, ensure_directories
from utils.logger import setup_logging

# --- Configuration ---
# Physical units for axis annotation
PHYSICAL_UNITS = {
    'laser_power': 'W',
    'scan_speed': 'mm/s',
    'layer_thickness': 'µm',
    'yield_strength': 'MPa',
    'ductility': '%',
    'fatigue_life': 'cycles'
}

def load_normalization_bounds(bounds_file: Optional[str] = None) -> Dict[str, Dict[str, float]]:
    """
    Loads the normalization bounds from the JSON file generated during preprocessing.
    
    Args:
        bounds_file: Optional path override. Defaults to data/processed/normalization_bounds.json.
    
    Returns:
        Dictionary mapping feature names to {'min': float, 'max': float, 'unit': str}.
        If unit is not in the file, it is looked up in PHYSICAL_UNITS.
    """
    if bounds_file is None:
        bounds_file = os.path.join(get_processed_data_dir(), "normalization_bounds.json")
    
    if not os.path.exists(bounds_file):
        raise FileNotFoundError(f"Normalization bounds file not found: {bounds_file}")
    
    with open(bounds_file, 'r') as f:
        bounds_data = json.load(f)
    
    # Ensure units are attached
    enriched_bounds = {}
    for key, values in bounds_data.items():
        # Handle cases where the key might be a list or specific feature name
        if isinstance(key, str):
            unit = PHYSICAL_UNITS.get(key, ' (normalized)')
            enriched_bounds[key] = {
                'min': values.get('min', 0.0),
                'max': values.get('max', 1.0),
                'unit': unit,
                'raw_min': values.get('raw_min'), # Optional: if stored
                'raw_max': values.get('raw_max')  # Optional: if stored
            }
        else:
            # Fallback for unexpected structure
            enriched_bounds[str(key)] = {'min': 0.0, 'max': 1.0, 'unit': ' (normalized)'}
    
    return enriched_bounds

def load_processed_test_data(test_data_path: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Loads the preprocessed test set (X_test, y_test, feature_names).
    Expects a pickle file saved by the preprocessing pipeline.
    """
    if test_data_path is None:
        test_data_path = os.path.join(get_processed_data_dir(), "test_data.pkl")
    
    if not os.path.exists(test_data_path):
        raise FileNotFoundError(f"Test data file not found: {test_data_path}")
    
    with open(test_data_path, 'rb') as f:
        data = pickle.load(f)
    
    X_test = data['X_test']
    y_test = data['y_test']
    feature_names = data['feature_names']
    
    return X_test, y_test, feature_names

def load_model(model_path: Optional[str] = None):
    """
    Loads the trained GPR model from disk.
    """
    if model_path is None:
        model_path = os.path.join(get_results_dir(), "models", "gpr_model.pkl")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    return model

def generate_contour_grid(bounds: Dict[str, Dict[str, float]], 
                          n_points: int = 100) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Generates a 2D grid for contour plotting based on physical bounds.
    Assumes the first two features in the bounds dict are the X and Y axes (Power, Speed).
    
    Returns:
        X_grid, Y_grid (meshgrid), X_min, X_max, Y_min, Y_max
    """
    # Identify the first two features as the axes
    # We expect 'laser_power' and 'scan_speed' to be present
    features = list(bounds.keys())
    if len(features) < 2:
        raise ValueError("Normalization bounds must contain at least two features for 2D contour plotting.")
    
    x_feat = features[0]
    y_feat = features[1]
    
    x_min = bounds[x_feat]['min']
    x_max = bounds[x_feat]['max']
    y_min = bounds[y_feat]['min']
    y_max = bounds[y_feat]['max']
    
    x = np.linspace(x_min, x_max, n_points)
    y = np.linspace(y_min, y_max, n_points)
    X_grid, Y_grid = np.meshgrid(x, y)
    
    return X_grid, Y_grid, x_min, x_max, y_min, y_max

def predict_with_uncertainty(model, X_grid: np.ndarray, Y_grid: np.ndarray, 
                             feature_names: list, x_idx: int = 0, y_idx: int = 1) -> Tuple[np.ndarray, np.ndarray]:
    """
    Predicts mean and standard deviation on the grid.
    Flattens grid, constructs feature matrix, predicts, then reshapes.
    """
    # Create mesh of points
    # We need to construct a full feature vector for every point in the grid
    # Since we only have 2D grids, we assume other features are fixed at their mean (0.5 normalized)
    n_samples = X_grid.size
    
    # Initialize feature matrix with zeros (or mean normalized value 0.5)
    # Using 0.5 as a safe normalized center point for missing dimensions
    X_full = np.full((n_samples, len(feature_names)), 0.5)
    
    X_full[:, x_idx] = X_grid.flatten()
    X_full[:, y_idx] = Y_grid.flatten()
    
    # Predict
    mean, std = model.predict(X_full, return_std=True)
    
    return mean.reshape(X_grid.shape), std.reshape(X_grid.shape)

def create_contour_plot(X_grid: np.ndarray, Y_grid: np.ndarray, 
                        Z_mean: np.ndarray, 
                        x_bounds: Dict[str, Dict[str, float]], 
                        y_bounds: Dict[str, Dict[str, float]],
                        target_name: str = 'Yield Strength',
                        output_path: Optional[str] = None):
    """
    Creates a contour plot of the predicted target with physical unit annotations.
    """
    if output_path is None:
        output_path = os.path.join(get_figures_dir(), f"contour_{target_name.lower().replace(' ', '_')}.png")
    
    ensure_directories([os.path.dirname(output_path)])
    
    plt.figure(figsize=(10, 8))
    
    # Create contour plot
    levels = np.linspace(Z_mean.min(), Z_mean.max(), 20)
    contour = plt.contourf(X_grid, Y_grid, Z_mean, levels=levels, cmap='viridis', alpha=0.8)
    plt.colorbar(contour, label=f'{target_name} ({PHYSICAL_UNITS.get(target_name, "")})')
    
    # Add contour lines for clarity
    plt.contour(X_grid, Y_grid, Z_mean, levels=levels, colors='k', linewidths=0.5, alpha=0.3)
    
    # Annotate axes with physical units
    x_unit = x_bounds['unit']
    y_unit = y_bounds['unit']
    
    plt.xlabel(f"Laser Power ({x_unit})")
    plt.ylabel(f"Scan Speed ({y_unit})")
    
    plt.title(f"Predicted {target_name} vs. Process Parameters")
    
    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logging.info(f"Contour plot saved to: {output_path}")
    return output_path

def create_uncertainty_heatmap(X_grid: np.ndarray, Y_grid: np.ndarray, 
                               Z_std: np.ndarray,
                               x_bounds: Dict[str, Dict[str, float]],
                               y_bounds: Dict[str, Dict[str, float]],
                               median_std: float,
                               target_name: str = 'Yield Strength',
                               output_path: Optional[str] = None):
    """
    Creates an uncertainty heatmap where regions with σ > 2× median are highlighted in red.
    """
    if output_path is None:
        output_path = os.path.join(get_figures_dir(), f"uncertainty_{target_name.lower().replace(' ', '_')}.png")
    
    ensure_directories([os.path.dirname(output_path)])
    
    threshold = 2.0 * median_std
    
    # Create a mask for high uncertainty
    high_uncertainty_mask = Z_std > threshold
    
    plt.figure(figsize=(10, 8))
    
    # Plot base uncertainty with a colormap
    # Using 'coolwarm' or 'RdYlBu' to show low (blue) to high (red)
    # We will manually overlay red for high uncertainty if needed, or use a custom colormap
    # For simplicity, we use a standard colormap but emphasize the threshold
    levels = np.linspace(Z_std.min(), Z_std.max(), 50)
    contour = plt.contourf(X_grid, Y_grid, Z_std, levels=levels, cmap='RdYlBu_r', alpha=0.8)
    plt.colorbar(contour, label='Prediction Standard Deviation (Normalized)')
    
    # Overlay red regions where uncertainty is high
    # We create a masked array to show red only where condition is met
    high_unc_data = np.ma.masked_where(~high_uncertainty_mask, Z_std)
    plt.contourf(X_grid, Y_grid, high_unc_data, levels=[threshold, Z_std.max()], 
                 colors=['red'], alpha=0.6)
    
    # Add a legend entry for the threshold manually
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='red', alpha=0.6, label=f'High Uncertainty (σ > {threshold:.4f})')]
    plt.legend(handles=legend_elements, loc='upper right')
    
    # Annotate axes with physical units
    x_unit = x_bounds['unit']
    y_unit = y_bounds['unit']
    
    plt.xlabel(f"Laser Power ({x_unit})")
    plt.ylabel(f"Scan Speed ({y_unit})")
    
    plt.title(f"Prediction Uncertainty Heatmap (σ > 2× Median Highlighted in Red)")
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logging.info(f"Uncertainty heatmap saved to: {output_path}")
    return output_path

def main():
    """
    Main entry point for T038: Integrate normalization bounds into visualizations.
    This script loads the bounds, generates the grid, and creates plots with physical units.
    """
    # Setup logging
    logger = setup_logging("contour_plots")
    logger.info("Starting T038: Visualization with Physical Unit Integration")
    
    try:
        # 1. Load Normalization Bounds
        logger.info("Loading normalization bounds...")
        bounds = load_normalization_bounds()
        
        # Verify we have the necessary features
        if 'laser_power' not in bounds or 'scan_speed' not in bounds:
            logger.error("Missing required features (laser_power, scan_speed) in normalization bounds.")
            return
        
        x_bounds = bounds['laser_power']
        y_bounds = bounds['scan_speed']
        
        # 2. Load Model and Data
        logger.info("Loading model and test data...")
        model = load_model()
        X_test, y_test, feature_names = load_processed_test_data()
        
        # 3. Generate Contour Grid
        logger.info("Generating contour grid...")
        X_grid, Y_grid, _, _, _, _ = generate_contour_grid(bounds)
        
        # 4. Predict with Uncertainty
        logger.info("Predicting on grid...")
        Z_mean, Z_std = predict_with_uncertainty(model, X_grid, Y_grid, feature_names)
        
        # 5. Calculate Median Standard Deviation for Thresholding
        median_std = np.median(Z_std)
        logger.info(f"Calculated median standard deviation: {median_std:.4f}")
        
        # 6. Create Plots
        logger.info("Creating contour plot...")
        create_contour_plot(
            X_grid, Y_grid, Z_mean, 
            x_bounds, y_bounds, 
            target_name='Yield Strength',
            output_path=os.path.join(get_figures_dir(), "contour_yield_strength.png")
        )
        
        logger.info("Creating uncertainty heatmap...")
        create_uncertainty_heatmap(
            X_grid, Y_grid, Z_std,
            x_bounds, y_bounds,
            median_std=median_std,
            target_name='Yield Strength',
            output_path=os.path.join(get_figures_dir(), "uncertainty_yield_strength.png")
        )
        
        logger.info("T038 completed successfully. Figures generated with physical unit annotations.")
        
    except Exception as e:
        logger.error(f"Error during T038 execution: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
