"""
Visualization module for User Story 1.
Generates scatter plots of semantic entropy vs. activation variance.
"""
import os
import json
import logging
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, List

# Ensure project root is in path for relative imports if run as script
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import Config
from analysis.correlation import load_entropy_scores, load_activation_variances

logger = logging.getLogger(__name__)

def load_correlation_data(results_path: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load entropy scores and activation variances from the correlation results.
    
    Args:
        results_path: Path to correlation_results.json. Defaults to Config path.
        
    Returns:
        Tuple of (entropy_scores, variance_values) as numpy arrays.
        
    Raises:
        FileNotFoundError: If the results file does not exist.
        KeyError: If expected keys are missing.
    """
    config = Config()
    if results_path is None:
        results_path = str(config.data_processed_dir / "correlation_results.json")
    
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Correlation results file not found at {results_path}. "
                                "Run T017 (run_correlation.py) first to generate this file.")
    
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    if 'data_points' not in data:
        raise KeyError("Expected 'data_points' key in correlation_results.json")
    
    points = data['data_points']
    
    if not points:
        raise ValueError("No data points found in correlation_results.json")
    
    # Extract arrays
    entropies = []
    variances = []
    
    for point in points:
        # Handle potential variations in key names based on generation logic
        ent = point.get('entropy', point.get('semantic_entropy'))
        var = point.get('variance', point.get('activation_variance'))
        
        if ent is not None and var is not None:
            entropies.append(float(ent))
            variances.append(float(var))
    
    if not entropies:
        raise ValueError("Could not extract valid entropy/variance pairs from data_points.")
    
    return np.array(entropies), np.array(variances)

def plot_entropy_vs_variance(
    entropies: np.ndarray,
    variances: np.ndarray,
    output_path: str,
    title: str = "Semantic Entropy vs. Activation Variance",
    correlation_coeff: Optional[float] = None,
    p_value: Optional[float] = None
) -> None:
    """
    Generate a scatter plot of entropy vs. variance with optional regression line.
    
    Args:
        entropies: Array of semantic entropy scores.
        variances: Array of activation variance measurements.
        output_path: Path to save the plot (PNG).
        title: Plot title.
        correlation_coeff: Optional Pearson r to display in title.
        p_value: Optional p-value to display in title.
    """
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plt.figure(figsize=(10, 8))
    
    # Scatter plot
    plt.scatter(entropies, variances, alpha=0.6, edgecolors='w', linewidth=0.5, s=50, c='steelblue')
    
    # Add regression line if we have enough points
    if len(entropies) >= 2:
        # Fit a linear regression line
        m, b = np.polyfit(entropies, variances, 1)
        x_line = np.linspace(min(entropies), max(entropies), 100)
        y_line = m * x_line + b
        plt.plot(x_line, y_line, 'r-', linewidth=2, label=f'Linear Fit (r={correlation_coeff:.3f})' if correlation_coeff is not None else 'Linear Fit')
    
    # Labels and Title
    plt.title(title, fontsize=14, pad=15)
    plt.xlabel("Semantic Entropy (bits)", fontsize=12)
    plt.ylabel("Activation Variance (float32)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add statistics to plot if provided
    if correlation_coeff is not None and p_value is not None:
        stats_text = f"r = {correlation_coeff:.4f}, p = {p_value:.4e}"
        plt.text(0.05, 0.95, stats_text, transform=plt.gca().transAxes, 
                fontsize=11, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.legend()
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Scatter plot saved to {output_path}")

def generate_visualization_report(
    results_path: Optional[str] = None,
    output_dir: Optional[str] = None
) -> str:
    """
    Main entry point to generate the visualization report.
    Loads data from correlation_results.json and saves a scatter plot.
    
    Args:
        results_path: Path to correlation_results.json.
        output_dir: Directory to save the plot. Defaults to Config figures dir.
        
    Returns:
        Path to the generated plot file.
    """
    config = Config()
    
    if results_path is None:
        results_path = str(config.data_processed_dir / "correlation_results.json")
        
    if output_dir is None:
        output_dir = str(config.figures_dir)
    
    output_path = os.path.join(output_dir, "entropy_vs_variance_scatter.png")
    
    # Load data
    logger.info(f"Loading data from {results_path}...")
    entropies, variances = load_correlation_data(results_path)
    
    # Extract correlation stats if available
    corr_coeff = None
    p_val = None
    if os.path.exists(results_path):
        with open(results_path, 'r') as f:
            data = json.load(f)
            corr_coeff = data.get('correlation_coefficient')
            p_val = data.get('p_value')
    
    # Generate plot
    logger.info("Generating scatter plot...")
    plot_entropy_vs_variance(
        entropies, 
        variances, 
        output_path,
        title="User Story 1: Entropy vs. Activation Variance",
        correlation_coeff=corr_coeff,
        p_value=p_val
    )
    
    return output_path

def main():
    """CLI entry point for visualization generation."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        output_file = generate_visualization_report()
        print(f"Visualization complete: {output_file}")
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        logger.error("Please ensure T017 (run_correlation.py) has been run successfully.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()