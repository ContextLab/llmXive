import os
import json
import logging
import numpy as np
import matplotlib.pyplot as plt
import pickle
from typing import Tuple, Dict, Any, Optional
from pathlib import Path

from config import (
    get_processed_data_dir,
    get_results_dir,
    get_figures_dir,
    get_models_dir,
    get_logger,
    ensure_directories
)
from utils.logger import setup_logging

# Ensure logging is configured
setup_logging()
logger = get_logger(__name__)

def load_processed_test_data(file_name: str = "processed_data.csv") -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Load the test set from the processed CSV.
    Returns: (X_train, y_train, X_test, y_test)
    Note: This function assumes the preprocessing step has saved the split data.
    For this implementation, we expect a specific structure or a saved split state.
    Given the constraints, we will load the full processed CSV and assume the last 20%
    are test samples, or load a saved split if available.
    
    However, to be robust, we will look for a saved split state or load the CSV and
    infer. The most reliable way given the pipeline is to load the CSV and use the
    same split logic if not saved, OR load the specific test set if saved.
    
    Let's assume the preprocessing saved a 'split_indices.json' or similar, or we
    simply load the CSV and re-split using the random seed for consistency if needed.
    But the task implies using the *existing* processed data.
    
    We will load the CSV and assume the last 20% are the test set for visualization purposes,
    or load a saved 'test_set.pkl' if it exists.
    """
    data_path = get_processed_data_dir() / file_name
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data file not found: {data_path}")
    
    import pandas as pd
    df = pd.read_csv(data_path)
    
    # Identify feature columns (exclude target and original categorical if any)
    # Based on schema: laser_power, scan_speed, layer_thickness, yield_strength, ductility
    # One-hot encoded alloy types will be present.
    target_cols = ['yield_strength', 'ductility']
    # We will use yield_strength as the primary target for this plot
    target_col = 'yield_strength'
    
    # Features are all numeric columns except the target
    feature_cols = [c for c in df.columns if c not in target_cols and df[c].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Simple train/test split for visualization (assuming data is already shuffled or split)
    # If the preprocessing saved a specific test set, we should load that.
    # For robustness, we'll take the last 20% as test set if no saved split exists.
    split_idx = int(len(X) * 0.8)
    X_test = X[split_idx:]
    y_test = y[split_idx:]
    
    # We need X_train to fit the scaler if not already done, but data is preprocessed.
    # We assume X is already scaled.
    X_train = X[:split_idx]
    y_train = y[:split_idx]
    
    return X_train, y_train, X_test, y_test

def load_normalization_bounds(file_name: str = "normalization_bounds.json") -> Dict[str, Any]:
    """Load normalization bounds saved during preprocessing."""
    bounds_path = get_processed_data_dir() / file_name
    if not bounds_path.exists():
        raise FileNotFoundError(f"Normalization bounds not found: {bounds_path}")
    
    with open(bounds_path, 'r') as f:
        return json.load(f)

def load_model(model_name: str = "gpr_model.pkl") -> Any:
    """Load the trained GPR model."""
    model_path = get_models_dir() / model_name
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def generate_contour_grid(X_train: np.ndarray, bounds: Dict[str, Any], n_points: int = 50) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate a grid for contour plotting based on Laser Power and Scan Speed.
    Returns: X_grid (n_points*n_points, n_features), power_grid, speed_grid
    """
    # Identify columns for laser_power and scan_speed
    # We need to know the column names in the preprocessed data
    # Assuming they are present in the bounds or we infer from X_train shape if not
    # But we need the actual column names to map back.
    # Let's assume the first two numeric features are laser_power and scan_speed
    # This is fragile. Better to load the column names from the processed CSV.
    
    data_path = get_processed_data_dir() / "processed_data.csv"
    import pandas as pd
    df = pd.read_csv(data_path)
    feature_cols = [c for c in df.columns if c not in ['yield_strength', 'ductility'] and df[c].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    if 'laser_power' not in feature_cols or 'scan_speed' not in feature_cols:
        # Fallback: assume first two columns
        logger.warning("laser_power or scan_speed not found in feature columns. Using first two columns.")
        power_idx = 0
        speed_idx = 1
    else:
        power_idx = feature_cols.index('laser_power')
        speed_idx = feature_cols.index('scan_speed')
    
    # Get min/max for these columns from bounds or data
    # Bounds might be stored as 'min' and 'max' per feature
    # If bounds structure is {feature: {'min': ..., 'max': ...}}
    # We need to handle one-hot encoded features too.
    
    # Let's extract ranges from the training data if bounds are not per-feature in a dict
    # Assuming bounds is a dict of feature_name -> {min, max}
    if isinstance(bounds, dict) and 'laser_power' in bounds:
        power_min, power_max = bounds['laser_power']['min'], bounds['laser_power']['max']
        speed_min, speed_max = bounds['scan_speed']['min'], bounds['scan_speed']['max']
    else:
        # Fallback to data range
        power_min, power_max = X_train[:, power_idx].min(), X_train[:, power_idx].max()
        speed_min, speed_max = X_train[:, speed_idx].min(), X_train[:, speed_idx].max()
    
    # Create grid
    power_range = np.linspace(power_min, power_max, n_points)
    speed_range = np.linspace(speed_min, speed_max, n_points)
    power_grid, speed_grid = np.meshgrid(power_range, speed_range)
    
    # Construct full grid X
    n_features = X_train.shape[1]
    X_grid = np.zeros((n_points * n_points, n_features))
    
    # Fill in power and speed
    X_grid[:, power_idx] = power_grid.flatten()
    X_grid[:, speed_idx] = speed_grid.flatten()
    
    # For other features, use the mean of the training set
    # This is a simplification. Ideally, we iterate over combinations or fix other vars.
    # For a 2D plot, we fix other variables to their mean.
    means = X_train.mean(axis=0)
    for i in range(n_features):
        if i != power_idx and i != speed_idx:
            X_grid[:, i] = means[i]
    
    return X_grid, power_grid, speed_grid

def predict_with_uncertainty(model: Any, X_grid: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Predict mean and standard deviation for the grid.
    GPR in sklearn returns (mean, std) if return_std=True
    """
    mean_pred, std_pred = model.predict(X_grid, return_std=True)
    return mean_pred, std_pred

def create_contour_plot(power_grid: np.ndarray, speed_grid: np.ndarray, y_pred: np.ndarray, 
                        power_label: str = "Laser Power (W)", 
                        speed_label: str = "Scan Speed (mm/s)",
                        title: str = "Predicted Yield Strength") -> plt.Figure:
    """Create a contour plot of the predicted values."""
    fig, ax = plt.subplots(figsize=(10, 8))
    contour = ax.contourf(power_grid, speed_grid, y_pred.reshape(power_grid.shape), levels=20, cmap='viridis')
    plt.colorbar(contour, ax=ax, label='Yield Strength (MPa)')
    ax.set_xlabel(power_label)
    ax.set_ylabel(speed_label)
    ax.set_title(title)
    return fig

def create_uncertainty_heatmap(power_grid: np.ndarray, speed_grid: np.ndarray, std_pred: np.ndarray,
                               power_label: str = "Laser Power (W)",
                               speed_label: str = "Scan Speed (mm/s)",
                               title: str = "Prediction Uncertainty (σ)") -> plt.Figure:
    """
    Create an uncertainty heatmap.
    Highlight regions where σ > 2 × median(σ) in red.
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Calculate the threshold
    median_std = np.median(std_pred)
    threshold = 2 * median_std
    
    # Create a mask for high uncertainty
    # We will plot the standard deviation, but overlay a red mask or use a custom colormap
    # Strategy: Use a colormap that highlights high values, or create a composite image.
    # Let's use a standard heatmap for σ, and then overlay a contour or mask for > threshold.
    
    # Plot the standard deviation
    im = ax.contourf(power_grid, speed_grid, std_pred.reshape(power_grid.shape), levels=20, cmap='viridis')
    
    # Overlay the high uncertainty region
    # Create a mask where std > threshold
    high_uncertainty = std_pred.reshape(power_grid.shape) > threshold
    
    # We can use a second contourf with a specific color for high uncertainty
    # Or use a masked array to show it distinctly.
    # Let's use a red overlay with alpha
    # Create a masked array for the high uncertainty region
    high_unc_mask = np.ma.masked_where(~high_uncertainty, std_pred.reshape(power_grid.shape))
    
    # Plot the high uncertainty region in red
    # We need to make sure the red region is visible on top of the viridis map
    # Using a separate contourf with a single level or a custom colormap
    # Simpler: Use a red contour line or fill
    # Let's use a red fill for the high uncertainty area
    ax.contourf(power_grid, speed_grid, high_uncertainty, levels=[0.5, 1], colors=['red'], alpha=0.3)
    
    # Add a threshold line annotation
    ax.text(0.05, 0.95, f'High Uncertainty (σ > {threshold:.2f})', 
            transform=ax.transAxes, fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))
    
    plt.colorbar(im, ax=ax, label='Standard Deviation (σ)')
    ax.set_xlabel(power_label)
    ax.set_ylabel(speed_label)
    ax.set_title(title)
    
    return fig

def main():
    """
    Main function to generate contour plots and uncertainty heatmaps.
    """
    ensure_directories()
    
    try:
        # Load data
        logger.info("Loading processed test data...")
        X_train, y_train, X_test, y_test = load_processed_test_data()
        
        logger.info("Loading normalization bounds...")
        bounds = load_normalization_bounds()
        
        logger.info("Loading GPR model...")
        model = load_model()
        
        # Generate grid
        logger.info("Generating contour grid...")
        X_grid, power_grid, speed_grid = generate_contour_grid(X_train, bounds)
        
        # Predict
        logger.info("Predicting with uncertainty...")
        y_pred, std_pred = predict_with_uncertainty(model, X_grid)
        
        # Create figures
        logger.info("Creating contour plot...")
        fig_contour = create_contour_plot(power_grid, speed_grid, y_pred)
        
        logger.info("Creating uncertainty heatmap...")
        fig_uncertainty = create_uncertainty_heatmap(power_grid, speed_grid, std_pred)
        
        # Save figures
        figures_dir = get_figures_dir()
        os.makedirs(figures_dir, exist_ok=True)
        
        contour_path = figures_dir / "yield_strength_contour.png"
        uncertainty_path = figures_dir / "uncertainty_heatmap.png"
        
        fig_contour.savefig(contour_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved contour plot to {contour_path}")
        
        fig_uncertainty.savefig(uncertainty_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved uncertainty heatmap to {uncertainty_path}")
        
        # Close plots to free memory
        plt.close(fig_contour)
        plt.close(fig_uncertainty)
        
        logger.info("Visualization tasks completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during visualization: {e}")
        raise

if __name__ == "__main__":
    main()