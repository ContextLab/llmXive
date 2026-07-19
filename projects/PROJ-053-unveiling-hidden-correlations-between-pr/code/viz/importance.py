"""
Partial Dependence Plots (PDPs) for top 3 influential parameters.

This module generates PDPs to visualize the marginal effect of the top 3
most influential features (as determined by permutation importance) on the
predicted mechanical properties.
"""
import os
import sys
import json
import logging
import numpy as np
import matplotlib.pyplot as plt
import pickle
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import (
    get_results_dir, 
    get_models_dir, 
    get_figures_dir, 
    ensure_directories,
    get_logger
)
from utils.logger import setup_logging

# Constants
N_TOP_FEATURES = 3
FIG_DPI = 300
FIG_SIZE = (10, 8)

def load_processed_test_data() -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load the processed test set features, targets, and feature names.
    
    Returns:
        Tuple of (X_test, y_test, feature_names)
    """
    data_path = os.path.join(get_results_dir(), 'test_data.json')
    
    if not os.path.exists(data_path):
        # Fallback: look in data/processed if results doesn't have it yet
        data_path = os.path.join(os.path.dirname(get_results_dir()), 'data', 'processed', 'test_data.json')
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Test data not found at {data_path}. "
                                "Ensure preprocessing pipeline has run.")
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    X_test = np.array(data['X_test'])
    y_test = np.array(data['y_test'])
    feature_names = data['feature_names']
    
    return X_test, y_test, feature_names

def load_model() -> Any:
    """
    Load the trained GPR model from the results/models directory.
    
    Returns:
        The trained GPR model object.
    """
    model_path = os.path.join(get_models_dir(), 'gpr_model.pkl')
    
    if not os.path.exists(model_path):
        # Try alternative path
        model_path = os.path.join(os.path.dirname(get_models_dir()), 'results', 'models', 'gpr_model.pkl')
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"GPR model not found at {model_path}. "
                                "Ensure model training pipeline has run.")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    return model

def load_importance_ranking() -> List[Dict[str, Any]]:
    """
    Load the permutation importance ranking from the metrics analysis.
    
    Returns:
        List of feature importance dictionaries sorted by rank.
    """
    # Try to load from metrics.json or a dedicated importance file
    metrics_path = os.path.join(get_results_dir(), 'metrics.json')
    importance_path = os.path.join(get_results_dir(), 'baseline_correlation.json')
    
    # First try baseline_correlation.json which contains importance rankings
    if os.path.exists(importance_path):
        with open(importance_path, 'r') as f:
            importance_data = json.load(f)
        
        # Extract features sorted by rank
        if 'features' in importance_data:
            features = importance_data['features']
            # Sort by rank (ascending)
            sorted_features = sorted(features, key=lambda x: x['rank'])
            return sorted_features[:N_TOP_FEATURES]
    
    # Fallback: try to extract from metrics.json if it has importance info
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        # Check if importance info is stored here
        if 'importance_ranking' in metrics:
            features = metrics['importance_ranking']
            sorted_features = sorted(features, key=lambda x: x['rank'])
            return sorted_features[:N_TOP_FEATURES]
    
    raise FileNotFoundError(
        "Importance ranking not found. "
        "Ensure permutation importance analysis (T030) has run."
    )

def generate_pdp_grid(
    X: np.ndarray, 
    feature_idx: int, 
    n_points: int = 50
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a grid of values for a single feature while keeping others at their mean.
    
    Args:
        X: The full feature matrix (test set)
        feature_idx: Index of the feature to vary
        n_points: Number of points to evaluate for the feature
        
    Returns:
        Tuple of (feature_values, grid_indices)
    """
    # Get the range of the feature from the data
    feature_min = X[:, feature_idx].min()
    feature_max = X[:, feature_idx].max()
    
    # Generate evenly spaced points
    feature_values = np.linspace(feature_min, feature_max, n_points)
    
    return feature_values, None

def compute_partial_dependence(
    model: Any,
    X: np.ndarray,
    feature_idx: int,
    feature_values: np.ndarray
) -> np.ndarray:
    """
    Compute partial dependence for a single feature.
    
    Args:
        model: The trained GPR model
        X: The full feature matrix
        feature_idx: Index of the feature to vary
        feature_values: Array of values to evaluate for the feature
        
    Returns:
        Array of predicted values for each feature value
    """
    predictions = []
    
    # Get the mean values of all other features
    mean_values = X.mean(axis=0)
    
    for val in feature_values:
        # Create a copy of the mean feature vector
        X_grid = mean_values.copy()
        X_grid[feature_idx] = val
        
        # Reshape for prediction (GPR expects 2D array)
        X_grid = X_grid.reshape(1, -1)
        
        # Predict
        pred = model.predict(X_grid)[0]
        predictions.append(pred)
    
    return np.array(predictions)

def create_pdp_plot(
    feature_name: str,
    feature_values: np.ndarray,
    pdp_values: np.ndarray,
    output_path: str,
    title: Optional[str] = None
):
    """
    Create and save a single Partial Dependence Plot.
    
    Args:
        feature_name: Name of the feature
        feature_values: Array of feature values
        pdp_values: Array of partial dependence values
        output_path: Path to save the plot
        title: Optional plot title
    """
    plt.figure(figsize=FIG_SIZE)
    
    plt.plot(feature_values, pdp_values, 'b-', linewidth=2, label='Partial Dependence')
    plt.xlabel(feature_name, fontsize=12)
    plt.ylabel('Predicted Value', fontsize=12)
    
    if title:
        plt.title(title, fontsize=14, fontweight='bold')
    else:
        plt.title(f'Partial Dependence Plot: {feature_name}', fontsize=14, fontweight='bold')
    
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save with high DPI
    plt.savefig(output_path, dpi=FIG_DPI, bbox_inches='tight')
    plt.close()

def generate_all_pdp_plots(
    model: Any,
    X_test: np.ndarray,
    feature_names: List[str],
    top_features: List[Dict[str, Any]],
    output_dir: str
) -> List[str]:
    """
    Generate PDP plots for all top features.
    
    Args:
        model: Trained GPR model
        X_test: Test feature matrix
        feature_names: List of all feature names
        top_features: List of top feature dictionaries with 'name' and 'rank'
        output_dir: Directory to save plots
        
    Returns:
        List of paths to generated plot files
    """
    generated_files = []
    
    for feat_info in top_features:
        feat_name = feat_info['name']
        
        # Find the index of this feature in the feature_names list
        if feat_name not in feature_names:
            logging.warning(f"Feature '{feat_name}' not found in feature_names. Skipping.")
            continue
        
        feat_idx = feature_names.index(feat_name)
        
        # Generate grid for this feature
        feature_values, _ = generate_pdp_grid(X_test, feat_idx, n_points=50)
        
        # Compute partial dependence
        pdp_values = compute_partial_dependence(model, X_test, feat_idx, feature_values)
        
        # Create plot
        output_filename = f'pdp_{feat_name.replace(" ", "_").replace("/", "_")}.png'
        output_path = os.path.join(output_dir, output_filename)
        
        create_pdp_plot(
            feature_name=feat_name,
            feature_values=feature_values,
            pdp_values=pdp_values,
            output_path=output_path,
            title=f'Partial Dependence Plot: {feat_name} (Rank: {feat_info["rank"]})'
        )
        
        generated_files.append(output_path)
        logging.info(f"Generated PDP plot: {output_path}")
    
    return generated_files

def create_combined_pdp_figure(
    model: Any,
    X_test: np.ndarray,
    feature_names: List[str],
    top_features: List[Dict[str, Any]],
    output_path: str
):
    """
    Create a combined figure with all top PDPs in a single plot.
    
    Args:
        model: Trained GPR model
        X_test: Test feature matrix
        feature_names: List of all feature names
        top_features: List of top feature dictionaries
        output_path: Path to save the combined figure
    """
    fig, axes = plt.subplots(1, len(top_features), figsize=(FIG_SIZE[0] * len(top_features), FIG_SIZE[1]))
    
    # Handle case where there's only one subplot
    if len(top_features) == 1:
        axes = [axes]
    
    for idx, feat_info in enumerate(top_features):
        feat_name = feat_info['name']
        
        if feat_name not in feature_names:
            continue
        
        feat_idx = feature_names.index(feat_name)
        
        # Generate grid
        feature_values, _ = generate_pdp_grid(X_test, feat_idx, n_points=50)
        
        # Compute PDP
        pdp_values = compute_partial_dependence(model, X_test, feat_idx, feature_values)
        
        # Plot
        axes[idx].plot(feature_values, pdp_values, 'b-', linewidth=2)
        axes[idx].set_xlabel(feat_name, fontsize=10)
        axes[idx].set_ylabel('Predicted Value', fontsize=10)
        axes[idx].set_title(f'{feat_name}\n(Rank: {feat_info["rank"]})', fontsize=12)
        axes[idx].grid(True, alpha=0.3)
    
    plt.suptitle('Partial Dependence Plots for Top 3 Influential Parameters', 
                fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    # Save combined figure
    plt.savefig(output_path, dpi=FIG_DPI, bbox_inches='tight')
    plt.close()
    
    logging.info(f"Generated combined PDP figure: {output_path}")

def main():
    """
    Main function to generate Partial Dependence Plots for top 3 influential parameters.
    """
    # Setup logging
    log_dir = os.path.join(os.path.dirname(get_results_dir()), 'logs')
    ensure_directories([log_dir])
    setup_logging('importance_plots.log', log_dir)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Partial Dependence Plot generation...")
    
    try:
        # Ensure output directories exist
        ensure_directories([get_figures_dir()])
        
        # Load data
        logger.info("Loading test data...")
        X_test, y_test, feature_names = load_processed_test_data()
        logger.info(f"Loaded test data with {len(feature_names)} features")
        
        # Load model
        logger.info("Loading GPR model...")
        model = load_model()
        logger.info("Model loaded successfully")
        
        # Load importance ranking
        logger.info("Loading importance ranking...")
        top_features = load_importance_ranking()
        logger.info(f"Loaded top {len(top_features)} features for PDP analysis")
        
        if len(top_features) < 1:
            logger.error("No features found in importance ranking. Cannot generate PDPs.")
            sys.exit(1)
        
        # Generate individual PDP plots
        logger.info("Generating individual PDP plots...")
        individual_plots = generate_all_pdp_plots(
            model, X_test, feature_names, top_features, get_figures_dir()
        )
        
        # Generate combined figure
        logger.info("Generating combined PDP figure...")
        combined_plot_path = os.path.join(
            get_figures_dir(), 'pdp_combined_top3.png'
        )
        create_combined_pdp_figure(
            model, X_test, feature_names, top_features, combined_plot_path
        )
        
        # Save metadata
        metadata = {
            'top_features': top_features,
            'individual_plots': [os.path.basename(p) for p in individual_plots],
            'combined_plot': os.path.basename(combined_plot_path),
            'n_features_analyzed': len(top_features),
            'n_test_samples': len(X_test)
        }
        
        metadata_path = os.path.join(get_results_dir(), 'pdp_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Generated {len(individual_plots)} individual PDP plots")
        logger.info(f"Generated 1 combined PDP figure: {combined_plot_path}")
        logger.info(f"Saved metadata to {metadata_path}")
        logger.info("Partial Dependence Plot generation completed successfully!")
        
    except FileNotFoundError as e:
        logger.error(f"Required data file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during PDP generation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
