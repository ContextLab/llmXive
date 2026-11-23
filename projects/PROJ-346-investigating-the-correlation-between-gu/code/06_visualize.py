"""
Visualization module for the Gut Microbiome and Cognitive Flexibility project.
Generates heatmaps and forest plots from correlation and regression results.
"""
import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils import get_data_processed_path, get_figures_path, get_data_qc_path, setup_logger

logger = setup_logger("visualize")

def load_correlation_results():
    """Load correlation results from JSON file."""
    processed_dir = get_data_processed_path()
    file_path = processed_dir / "correlation_results.json"
    
    if not file_path.exists():
        logger.warning(f"Correlation results file not found: {file_path}. Skipping visualization.")
        return None
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Failed to load correlation results: {e}")
        return None

def load_regression_results():
    """Load regression results from JSON file."""
    processed_dir = get_data_processed_path()
    file_path = processed_dir / "regression_results.json"
    
    if not file_path.exists():
        logger.warning(f"Regression results file not found: {file_path}. Skipping visualization.")
        return None
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Failed to load regression results: {e}")
        return None

def generate_heatmap(correlation_data):
    """
    Generate a heatmap of taxa-cognition correlation matrix.
    
    Args:
        correlation_data: Dictionary containing correlation results.
    """
    if not correlation_data:
        logger.info("No correlation data available for heatmap generation.")
        return
    
    figures_dir = get_figures_path()
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract correlation matrix
    if "correlation_matrix" not in correlation_data:
        logger.error("Correlation matrix not found in results.")
        return
    
    corr_matrix = correlation_data["correlation_matrix"]
    taxa_labels = correlation_data.get("taxa_labels", list(corr_matrix.keys()))
    cognitive_labels = correlation_data.get("cognitive_labels", ["cognitive_z_score"])
    
    # Convert to DataFrame
    df = pd.DataFrame(corr_matrix, index=taxa_labels, columns=cognitive_labels)
    
    # Plot
    plt.figure(figsize=(12, 8))
    sns.heatmap(df, annot=True, cmap='coolwarm', center=0, 
                square=True, linewidths=.5, cbar_kws={"shrink": .5})
    plt.title("Associational Correlation: Gut Microbiome vs Cognitive Flexibility", fontsize=14)
    plt.xlabel("Cognitive Score (Z-score)", fontsize=12)
    plt.ylabel("Microbial Taxa", fontsize=12)
    
    output_path = figures_dir / "correlation_heatmap.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Heatmap saved to {output_path}")

def generate_forest_plot(regression_data):
    """
    Generate a forest plot of regression coefficients with confidence intervals.
    
    Args:
        regression_data: Dictionary containing regression results.
    """
    if not regression_data:
        logger.info("No regression data available for forest plot generation.")
        return
    
    figures_dir = get_figures_path()
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract coefficients and confidence intervals
    if "coefficients" not in regression_data or "conf_int" not in regression_data:
        logger.error("Coefficients or confidence intervals not found in regression results.")
        return
    
    coefficients = regression_data["coefficients"]
    conf_int = regression_data["conf_int"]
    feature_names = regression_data.get("feature_names", list(coefficients.keys()))
    
    # Prepare data for plotting
    features = []
    coefs = []
    lower_bounds = []
    upper_bounds = []
    
    for feature in feature_names:
        if feature in coefficients:
            features.append(feature)
            coefs.append(coefficients[feature])
            if feature in conf_int:
                lower_bounds.append(conf_int[feature][0])
                upper_bounds.append(conf_int[feature][1])
            else:
                # If no CI available, use coefficient as both bounds (will show as point)
                lower_bounds.append(coefficients[feature])
                upper_bounds.append(coefficients[feature])
    
    if not features:
        logger.warning("No valid features found for forest plot.")
        return
    
    # Sort by coefficient value for better visualization
    sorted_indices = np.argsort(coefs)
    features = [features[i] for i in sorted_indices]
    coefs = [coefs[i] for i in sorted_indices]
    lower_bounds = [lower_bounds[i] for i in sorted_indices]
    upper_bounds = [upper_bounds[i] for i in sorted_indices]
    
    # Plot
    plt.figure(figsize=(10, 8))
    
    y_pos = np.arange(len(features))
    plt.errorbar(coefs, y_pos, xerr=[np.array(coefs) - np.array(lower_bounds), 
                                     np.array(upper_bounds) - np.array(coefs)], 
                 fmt='o', color='darkblue', capsize=5, markersize=6)
    plt.axvline(x=0, color='gray', linestyle='--', linewidth=1)
    
    plt.yticks(y_pos, features)
    plt.xlabel("Standardized Coefficient (Associational)", fontsize=12)
    plt.title("Forest Plot: Gut Microbiome Predictors of Cognitive Flexibility", fontsize=14)
    plt.grid(axis='x', linestyle=':', alpha=0.5)
    
    output_path = figures_dir / "regression_forest_plot.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Forest plot saved to {output_path}")

def main():
    """Main function to generate all visualizations."""
    logger.info("Starting visualization generation...")
    
    # Check if merged dataset exists (as per task requirements)
    processed_dir = get_data_processed_path()
    merged_path = processed_dir / "merged_dataset.parquet"
    
    if not merged_path.exists():
        logger.info("Merged dataset not found. Skipping visualization (N/A - Data Gap).")
        return
    
    # Load data
    correlation_data = load_correlation_results()
    regression_data = load_regression_results()
    
    # Generate plots
    if correlation_data:
        generate_heatmap(correlation_data)
    else:
        logger.warning("Skipping heatmap: correlation data not available.")
    
    if regression_data:
        generate_forest_plot(regression_data)
    else:
        logger.warning("Skipping forest plot: regression data not available.")
    
    logger.info("Visualization generation complete.")

if __name__ == "__main__":
    main()