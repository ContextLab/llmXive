import os
import sys
import json
import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import shap
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI
import matplotlib.pyplot as plt
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.dummy import DummyRegressor

from utils import setup_logging, load_state, update_state, compute_file_hash

# Configure logging
logger = setup_logging("analyze_explainability")

def load_model(model_path):
    """Load a trained model from a pickle file."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_data(data_path):
    """Load feature data from a CSV file."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    return pd.read_csv(data_path)

def find_best_model(state_path):
    """
    Read state.yaml to determine the selected model subset (raw or derived)
    and the corresponding non-selected subset.
    Returns: (selected_subset, non_selected_subset, selected_model_path, non_selected_model_path, data_suffix)
    """
    if not os.path.exists(state_path):
        raise FileNotFoundError(f"State file not found: {state_path}")
    
    state = load_state(state_path)
    
    # Determine selection from state
    # Based on T028 logic, we expect a 'selected_model' key in state
    if 'selected_model' not in state:
        raise ValueError("No model selection found in state.yaml. Run T028 first.")
    
    selection_info = state['selected_model']
    selected_subset = selection_info.get('subset') # 'raw' or 'derived'
    
    if selected_subset == 'raw':
        non_selected_subset = 'derived'
    elif selected_subset == 'derived':
        non_selected_subset = 'raw'
    else:
        raise ValueError(f"Invalid selected subset: {selected_subset}")
    
    # Construct paths based on T028/T031 logic
    # Models are saved in models/artifacts/
    # Best models are typically named best_{subset}_model.pkl
    selected_model_path = f"models/artifacts/best_{selected_subset}_model.pkl"
    non_selected_model_path = f"models/artifacts/best_{non_selected_subset}_model.pkl"
    
    # Data paths
    # T016b saves X_raw.csv and X_derived.csv
    selected_data_path = f"data/processed/X_{selected_subset}.csv"
    non_selected_data_path = f"data/processed/X_{non_selected_subset}.csv"
    
    return selected_subset, non_selected_subset, selected_model_path, non_selected_model_path, selected_data_path, non_selected_data_path

def calculate_shap_and_plot(model, X_data, output_plot_path, subset_name):
    """
    Calculate SHAP values for the given model and data, then generate a summary plot.
    Saves the plot to output_plot_path.
    """
    logger.info(f"Calculating SHAP values for {subset_name} model...")
    
    # Ensure we have a numpy array for SHAP
    if isinstance(X_data, pd.DataFrame):
        X_np = X_data.values
    else:
        X_np = np.array(X_data)
    
    # Determine explainer based on model type
    # SHAP supports direct explainer creation for GB and MLP (via KernelExplainer or TreeExplainer)
    # For GradientBoosting, we can use TreeExplainer if it's a tree ensemble.
    # For MLP, we typically need a KernelExplainer or a deep learning explainer (if using tf/keras).
    # Since we are using sklearn MLPRegressor, we use KernelExplainer for safety or a simplified approach.
    # However, SHAP has specific support for sklearn models.
    
    try:
        if isinstance(model, GradientBoostingRegressor):
            explainer = shap.TreeExplainer(model)
        elif isinstance(model, MLPRegressor):
            # For MLP, TreeExplainer is not applicable. KernelExplainer is slow.
            # We use a background sample to speed up KernelExplainer
            logger.info("Using KernelExplainer for MLP (may be slow)...")
            # Sample 100 points for background
            background = shap.sample(X_np, min(100, X_np.shape[0]))
            explainer = shap.KernelExplainer(model.predict, background)
        else:
            # Fallback for Dummy or other
            logger.warning(f"Unknown model type {type(model)}, using KernelExplainer")
            background = shap.sample(X_np, min(100, X_np.shape[0]))
            explainer = shap.KernelExplainer(model.predict, background)
        
        # Calculate SHAP values
        # For large datasets, this might take time. We might need to sample if too big.
        # Assuming X_np is manageable for this step.
        shap_values = explainer.shap_values(X_np)
        
        logger.info(f"SHAP values calculated. Shape: {shap_values.shape if hasattr(shap_values, 'shape') else 'N/A'}")
        
        # Plot
        logger.info(f"Generating SHAP summary plot for {subset_name}...")
        plt.figure(figsize=(10, 8))
        
        # Handle case where shap_values might be a list (for multi-output, though regression is single)
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        
        # Ensure we have a 2D array for shap.summary_plot
        if shap_values.ndim == 1:
            shap_values = shap_values.reshape(-1, 1)
        
        # Create summary plot
        # Use feature names from the dataframe if available
        feature_names = X_data.columns.tolist() if isinstance(X_data, pd.DataFrame) else [f"Feature_{i}" for i in range(X_np.shape[1])]
        
        shap.summary_plot(shap_values, X_data, plot_type="dot", feature_names=feature_names, show=False)
        
        # Save plot
        plt.savefig(output_plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"SHAP summary plot saved to {output_plot_path}")
        
        # Also save the SHAP values for potential downstream use (T033)
        shap_output_path = output_plot_path.replace('.png', '_values.npy')
        np.save(shap_output_path, shap_values)
        logger.info(f"SHAP values saved to {shap_output_path}")
        
    except Exception as e:
        logger.error(f"Error calculating or plotting SHAP values: {e}", exc_info=True)
        raise

def main():
    """
    Main entry point for T031b: Calculate SHAP values for the NON-SELECTED model.
    """
    logger.info("Starting T031b: SHAP analysis for non-selected model")
    
    # Paths
    project_root = Path(__file__).parent.parent
    state_path = project_root / "state" / "state.yaml"
    
    # 1. Find model selection info
    try:
        selected_subset, non_selected_subset, selected_model_path, non_selected_model_path, selected_data_path, non_selected_data_path = find_best_model(str(state_path))
    except Exception as e:
        logger.error(f"Failed to determine model selection: {e}")
        sys.exit(1)
    
    logger.info(f"Selected subset: {selected_subset}, Non-selected subset: {non_selected_subset}")
    
    # 2. Load non-selected model
    non_selected_model_path_full = project_root / non_selected_model_path
    if not non_selected_model_path_full.exists():
        logger.error(f"Non-selected model not found: {non_selected_model_path_full}")
        logger.error("Ensure T025b (or T025) has been run to generate the model artifacts.")
        sys.exit(1)
    
    logger.info(f"Loading non-selected model from {non_selected_model_path_full}")
    try:
        model = load_model(str(non_selected_model_path_full))
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)
    
    # 3. Load non-selected data
    non_selected_data_path_full = project_root / non_selected_data_path
    if not non_selected_data_path_full.exists():
        logger.error(f"Non-selected data not found: {non_selected_data_path_full}")
        logger.error("Ensure T016b has been run to generate feature subsets.")
        sys.exit(1)
    
    logger.info(f"Loading non-selected data from {non_selected_data_path_full}")
    try:
        X_data = load_data(str(non_selected_data_path_full))
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
    
    # 4. Calculate SHAP and Plot
    output_dir = project_root / "results" / "plots"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_plot_path = output_dir / f"shap_summary_{non_selected_subset}.png"
    
    try:
        calculate_shap_and_plot(model, X_data, str(output_plot_path), non_selected_subset)
    except Exception as e:
        logger.error(f"SHAP analysis failed: {e}")
        sys.exit(1)
    
    # 5. Update state
    # Update hash for the new plot
    if output_plot_path.exists():
        plot_hash = compute_file_hash(str(output_plot_path))
        state = load_state(str(state_path))
        if 'shap_plots' not in state:
            state['shap_plots'] = {}
        state['shap_plots'][non_selected_subset] = {
            'path': str(output_plot_path.relative_to(project_root)),
            'hash': plot_hash
        }
        update_state(str(state_path), state)
        logger.info(f"Updated state.yaml with SHAP plot hash for {non_selected_subset}")
    
    logger.info("T031b completed successfully.")

if __name__ == "__main__":
    main()