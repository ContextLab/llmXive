import os
import json
import logging
import numpy as np
import matplotlib.pyplot as plt
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

# Import from project config
from config import (
    get_processed_data_dir,
    get_models_dir,
    get_figures_dir,
    get_results_dir,
    ensure_directories
)
from utils.logger import setup_logging

# Constants
FIGURE_DPI = 150
FIGURE_SIZE = (10, 8)
CONTOUR_LEVELS = 20

def setup_logger() -> logging.Logger:
    """Setup logger for visualization module."""
    return setup_logging("contour_plots")

def load_normalization_bounds() -> Dict[str, Dict[str, float]]:
    """
    Load normalization bounds from data/processed/normalization_bounds.json.
    
    Returns:
        Dictionary mapping feature names to their min/max physical values.
        Example: {"laser_power": {"min": 100.0, "max": 400.0}, ...}
    """
    bounds_path = Path(get_processed_data_dir()) / "normalization_bounds.json"
    logger = logging.getLogger(__name__)
    
    if not bounds_path.exists():
        logger.error(f"Normalization bounds file not found: {bounds_path}")
        raise FileNotFoundError(
            f"Normalization bounds file not found: {bounds_path}. "
            "Please run T019 (preprocess) first to generate this file."
        )
    
    with open(bounds_path, 'r') as f:
        bounds = json.load(f)
    
    logger.info(f"Loaded normalization bounds from {bounds_path}")
    return bounds

def load_processed_test_data() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Load preprocessed test data from the pipeline.
    
    Returns:
        Tuple of (X_test, y_test, feature_names, target_name)
    """
    logger = logging.getLogger(__name__)
    processed_dir = Path(get_processed_data_dir())
    
    # Load processed test features
    test_features_path = processed_dir / "test_features.npy"
    test_targets_path = processed_dir / "test_targets.npy"
    feature_names_path = processed_dir / "feature_names.json"
    
    if not test_features_path.exists():
        logger.error(f"Test features not found: {test_features_path}")
        raise FileNotFoundError(f"Test features not found: {test_features_path}")
    
    if not test_targets_path.exists():
        logger.error(f"Test targets not found: {test_targets_path}")
        raise FileNotFoundError(f"Test targets not found: {test_targets_path}")
    
    if not feature_names_path.exists():
        logger.error(f"Feature names not found: {feature_names_path}")
        raise FileNotFoundError(f"Feature names not found: {feature_names_path}")
    
    X_test = np.load(test_features_path)
    y_test = np.load(test_targets_path)
    
    with open(feature_names_path, 'r') as f:
        feature_names = json.load(f)
    
    logger.info(f"Loaded test data: {X_test.shape} features, {y_test.shape} targets")
    return X_test, y_test, feature_names, "mechanical_property"

def load_model(model_path: Optional[str] = None):
    """
    Load the trained GPR model.
    
    Args:
        model_path: Optional path to model pickle file. If None, uses default path.
    
    Returns:
        Trained GPR model object.
    """
    logger = logging.getLogger(__name__)
    models_dir = Path(get_models_dir())
    
    if model_path is None:
        model_path = models_dir / "gpr_model.pkl"
    else:
        model_path = Path(model_path)
    
    if not model_path.exists():
        logger.error(f"Model file not found: {model_path}")
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    logger.info(f"Loaded model from {model_path}")
    return model

def generate_contour_grid(
    X_train: np.ndarray,
    feature_names: list,
    n_points: int = 100
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate a contour grid for visualization based on training data ranges.
    
    Args:
        X_train: Training feature matrix.
        feature_names: List of feature names.
        n_points: Number of points per dimension.
    
    Returns:
        Tuple of (X1_grid, X2_grid, X1_mesh, X2_mesh) where X1 and X2 are the
        first two feature dimensions (laser_power, scan_speed).
    """
    logger = logging.getLogger(__name__)
    
    # Assume first two features are laser_power and scan_speed
    if len(feature_names) < 2:
        logger.error("Need at least 2 features for contour plot")
        raise ValueError("Need at least 2 features for contour plot")
    
    # Get ranges for first two features
    x1_min, x1_max = X_train[:, 0].min(), X_train[:, 0].max()
    x2_min, x2_max = X_train[:, 1].min(), X_train[:, 1].max()
    
    # Create mesh grid
    x1 = np.linspace(x1_min, x1_max, n_points)
    x2 = np.linspace(x2_min, x2_max, n_points)
    X1_mesh, X2_mesh = np.meshgrid(x1, x2)
    
    # Flatten for prediction
    X_grid = np.column_stack([
        X1_mesh.ravel(),
        X2_mesh.ravel(),
        np.zeros(X1_mesh.size)  # Placeholder for other features
    ])
    
    # Pad if necessary
    if X_grid.shape[1] < X_train.shape[1]:
        X_grid = np.column_stack([
            X_grid,
            np.zeros((X_grid.shape[0], X_train.shape[1] - X_grid.shape[1]))
        ])
    
    logger.info(f"Generated contour grid: {X1_mesh.shape}")
    return x1, x2, X1_mesh, X2_mesh

def predict_with_uncertainty(
    model,
    X_grid: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Predict mean and uncertainty (standard deviation) on the grid.
    
    Args:
        model: Trained GPR model.
        X_grid: Grid of points for prediction.
    
    Returns:
        Tuple of (mean_predictions, std_predictions)
    """
    logger = logging.getLogger(__name__)
    
    try:
        # GPR predict with return_std=True
        mean, std = model.predict(X_grid, return_std=True)
        logger.info(f"Predicted on grid: mean shape {mean.shape}, std shape {std.shape}")
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise
    
    return mean, std

def create_contour_plot(
    X1_mesh: np.ndarray,
    X2_mesh: np.ndarray,
    predictions: np.ndarray,
    feature_names: list,
    bounds: Dict[str, Dict[str, float]],
    target_name: str = "Yield Strength",
    output_path: Optional[str] = None
):
    """
    Create a contour plot of predicted values with physical unit annotations.
    
    Args:
        X1_mesh: Mesh grid for first feature (laser_power).
        X2_mesh: Mesh grid for second feature (scan_speed).
        predictions: Predicted values reshaped to match mesh.
        feature_names: List of feature names.
        bounds: Normalization bounds with physical min/max values.
        target_name: Name of the target variable for the colorbar.
        output_path: Optional path to save the figure.
    """
    logger = logging.getLogger(__name__)
    
    # Reshape predictions
    predictions_reshaped = predictions.reshape(X1_mesh.shape)
    
    # Create figure
    fig, ax = plt.subplots(figsize=FIGURE_SIZE, dpi=FIGURE_DPI)
    
    # Create contour plot
    contour = ax.contourf(
        X1_mesh, X2_mesh, predictions_reshaped,
        levels=CONTOUR_LEVELS, cmap='viridis', alpha=0.8
    )
    
    # Add colorbar
    cbar = plt.colorbar(contour, ax=ax)
    cbar.set_label(target_name, fontsize=12)
    
    # Get physical bounds for axis labels
    x1_name = feature_names[0] if len(feature_names) > 0 else "Feature 1"
    x2_name = feature_names[1] if len(feature_names) > 1 else "Feature 2"
    
    # Extract physical units from bounds
    x1_min_phys = bounds.get(x1_name, {}).get('min', X1_mesh.min())
    x1_max_phys = bounds.get(x1_name, {}).get('max', X1_mesh.max())
    x2_min_phys = bounds.get(x2_name, {}).get('min', X2_mesh.min())
    x2_max_phys = bounds.get(x2_name, {}).get('max', X2_mesh.max())
    
    # Determine units based on feature names
    x1_unit = "W" if "power" in x1_name.lower() else "units"
    x2_unit = "mm/s" if "speed" in x2_name.lower() else "units"
    
    # Set axis labels with physical units
    ax.set_xlabel(f"{x1_name.replace('_', ' ').title()} ({x1_unit})", fontsize=12)
    ax.set_ylabel(f"{x2_name.replace('_', ' ').title()} ({x2_unit})", fontsize=12)
    ax.set_title(f"Predicted {target_name} vs Processing Parameters", fontsize=14)
    
    # Set axis limits to physical bounds
    ax.set_xlim(x1_min_phys, x1_max_phys)
    ax.set_ylim(x2_min_phys, x2_max_phys)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Save or show
    if output_path:
        plt.savefig(output_path, bbox_inches='tight', dpi=FIGURE_DPI)
        logger.info(f"Contour plot saved to {output_path}")
        plt.close()
    else:
        plt.show()

def create_uncertainty_heatmap(
    X1_mesh: np.ndarray,
    X2_mesh: np.ndarray,
    std_predictions: np.ndarray,
    feature_names: list,
    bounds: Dict[str, Dict[str, float]],
    output_path: Optional[str] = None
):
    """
    Create an uncertainty heatmap where high uncertainty (>2x median) is highlighted in red.
    
    Args:
        X1_mesh: Mesh grid for first feature.
        X2_mesh: Mesh grid for second feature.
        std_predictions: Standard deviation predictions reshaped to match mesh.
        feature_names: List of feature names.
        bounds: Normalization bounds with physical min/max values.
        output_path: Optional path to save the figure.
    """
    logger = logging.getLogger(__name__)
    
    # Reshape std predictions
    std_reshaped = std_predictions.reshape(X1_mesh.shape)
    
    # Calculate threshold (2x median)
    threshold = 2 * np.median(std_predictions)
    logger.info(f"Uncertainty threshold (2x median): {threshold:.4f}")
    
    # Create mask for high uncertainty
    high_uncertainty_mask = std_reshaped > threshold
    
    # Create figure
    fig, ax = plt.subplots(figsize=FIGURE_SIZE, dpi=FIGURE_DPI)
    
    # Create base heatmap
    heatmap = ax.contourf(
        X1_mesh, X2_mesh, std_reshaped,
        levels=CONTOUR_LEVELS, cmap='coolwarm', alpha=0.7
    )
    
    # Overlay high uncertainty regions in red
    ax.contourf(
        X1_mesh, X2_mesh, high_uncertainty_mask.astype(int),
        levels=[0.5, 1.5], colors=['red'], alpha=0.3
    )
    
    # Add colorbar
    cbar = plt.colorbar(heatmap, ax=ax)
    cbar.set_label("Prediction Standard Deviation (σ)", fontsize=12)
    
    # Get physical bounds for axis labels
    x1_name = feature_names[0] if len(feature_names) > 0 else "Feature 1"
    x2_name = feature_names[1] if len(feature_names) > 1 else "Feature 2"
    
    x1_min_phys = bounds.get(x1_name, {}).get('min', X1_mesh.min())
    x1_max_phys = bounds.get(x1_name, {}).get('max', X1_mesh.max())
    x2_min_phys = bounds.get(x2_name, {}).get('min', X2_mesh.min())
    x2_max_phys = bounds.get(x2_name, {}).get('max', X2_mesh.max())
    
    x1_unit = "W" if "power" in x1_name.lower() else "units"
    x2_unit = "mm/s" if "speed" in x2_name.lower() else "units"
    
    # Set axis labels with physical units
    ax.set_xlabel(f"{x1_name.replace('_', ' ').title()} ({x1_unit})", fontsize=12)
    ax.set_ylabel(f"{x2_name.replace('_', ' ').title()} ({x2_unit})", fontsize=12)
    ax.set_title("Prediction Uncertainty Heatmap (Red = High Uncertainty)", fontsize=14)
    
    # Set axis limits to physical bounds
    ax.set_xlim(x1_min_phys, x1_max_phys)
    ax.set_ylim(x2_min_phys, x2_max_phys)
    
    # Add legend for high uncertainty
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='red', alpha=0.3, label='High Uncertainty (σ > 2× median)')
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Save or show
    if output_path:
        plt.savefig(output_path, bbox_inches='tight', dpi=FIGURE_DPI)
        logger.info(f"Uncertainty heatmap saved to {output_path}")
        plt.close()
    else:
        plt.show()

def main():
    """
    Main function to generate contour plots and uncertainty heatmaps
    with physical unit annotations from normalization_bounds.json.
    """
    logger = setup_logger()
    logger.info("Starting contour plot generation with physical unit annotations")
    
    try:
        # Ensure output directory exists
        ensure_directories()
        figures_dir = Path(get_figures_dir())
        
        # Load normalization bounds (T019 artifact)
        bounds = load_normalization_bounds()
        logger.info(f"Loaded bounds: {list(bounds.keys())}")
        
        # Load test data
        X_test, y_test, feature_names, target_name = load_processed_test_data()
        
        # Load trained model
        model = load_model()
        
        # Generate contour grid
        x1, x2, X1_mesh, X2_mesh = generate_contour_grid(X_test, feature_names)
        
        # Predict with uncertainty
        mean_preds, std_preds = predict_with_uncertainty(model, X1_mesh)
        
        # Create contour plot with physical units
        contour_path = figures_dir / "contour_yield_strength.png"
        create_contour_plot(
            X1_mesh, X2_mesh, mean_preds, feature_names, bounds,
            target_name="Yield Strength", output_path=str(contour_path)
        )
        
        # Create uncertainty heatmap with physical units
        heatmap_path = figures_dir / "uncertainty_heatmap.png"
        create_uncertainty_heatmap(
            X1_mesh, X2_mesh, std_preds, feature_names, bounds,
            output_path=str(heatmap_path)
        )
        
        logger.info("Successfully generated contour plots with physical unit annotations")
        logger.info(f"  - Contour plot: {contour_path}")
        logger.info(f"  - Uncertainty heatmap: {heatmap_path}")
        
    except Exception as e:
        logger.error(f"Error generating plots: {e}")
        raise

if __name__ == "__main__":
    main()