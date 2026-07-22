"""
Forest Plot Generation for Meta-Analysis of Brain Connectivity and Music Preferences.

This module generates a forest plot visualizing individual study effect sizes (r-values)
and their confidence intervals, along with the pooled summary effect (diamond).

Dependencies:
    - matplotlib
    - numpy
    - pandas (optional, used for data loading if needed)

Output:
    - data/derived/forest_plot.png
"""

import json
import math
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np

# Import local utilities
# Note: We assume this script is run from the project root or code directory
# Adjust imports based on the actual execution context (e.g., python -m)
try:
    from utils.logger import get_logger
    from visualization.memory_monitor import monitor_memory, get_memory_threshold_mb
except ImportError:
    # Fallback for direct execution or different module structure
    import logging
    logger = logging.getLogger(__name__)
    
    def get_logger(name):
        return logging.getLogger(name)
        
    def monitor_memory(func):
        """Decorator to monitor memory usage."""
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
        
    def get_memory_threshold_mb():
        return 5000  # Default 5GB

# Configure logger
logger = get_logger(__name__)

# Constants
FIGURE_WIDTH = 10
FIGURE_HEIGHT = 8
DENSITY = 150  # DPI
OUTPUT_FILENAME = "forest_plot.png"
RESULTS_JSON_PATH = "data/derived/results.json"
EXTRACTED_STUDIES_PATH = "data/processed/extracted_studies.csv"

def load_analysis_results(results_path: str = RESULTS_JSON_PATH) -> Dict[str, Any]:
    """
    Load the meta-analysis results from the JSON file.
    
    Args:
        results_path: Path to the results JSON file.
        
    Returns:
        Dictionary containing analysis results.
        
    Raises:
        FileNotFoundError: If the results file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
        
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_effect_sizes_for_plotting(csv_path: str = EXTRACTED_STUDIES_PATH) -> List[Dict[str, Any]]:
    """
    Load study data from the extracted studies CSV for plotting.
    
    Args:
        csv_path: Path to the extracted studies CSV.
        
    Returns:
        List of dictionaries containing study data (author, year, r, se, tract).
    """
    import csv
    studies = []
    path = Path(csv_path)
    
    if not path.exists():
        logger.warning(f"Extracted studies file not found: {csv_path}. Generating empty list.")
        return studies
        
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Filter studies with valid r and n (for SE calculation)
            try:
                r_val = float(row.get('r', 0))
                n_val = int(row.get('n', 0))
                if n_val > 0:
                    # Calculate Standard Error for Fisher's z transformed r
                    # SE_z = 1 / sqrt(N - 3)
                    # Then transform back? Or plot in Fisher's z space?
                    # Standard practice: Plot in Fisher's z space, then label axis.
                    # However, tasks often ask for 'r' on the axis.
                    # Let's calculate SE for r directly using the approximation:
                    # SE_r = (1 - r^2) / sqrt(N - 1)
                    se_r = (1 - r_val**2) / math.sqrt(n_val - 1)
                    
                    studies.append({
                        'author': row.get('author', 'Unknown'),
                        'year': row.get('year', ''),
                        'r': r_val,
                        'se': se_r,
                        'tract': row.get('tract', 'Unknown'),
                        'n': n_val
                    })
            except (ValueError, TypeError) as e:
                logger.debug(f"Skipping row due to invalid data: {row}, error: {e}")
                continue
                
    return studies

def calculate_ci(r: float, se: float, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate 95% Confidence Interval for an effect size.
    
    Args:
        r: Effect size (correlation coefficient).
        se: Standard error.
        alpha: Significance level (default 0.05).
        
    Returns:
        Tuple of (lower_bound, upper_bound).
    """
    z_score = 1.96  # Approximate for 95% CI
    lower = r - z_score * se
    upper = r + z_score * se
    return lower, upper

@monitor_memory
def create_forest_plot(
    studies: List[Dict[str, Any]], 
    pooled_r: float, 
    pooled_se: Optional[float] = None,
    output_path: str = "data/derived/forest_plot.png"
) -> str:
    """
    Create and save a forest plot.
    
    Args:
        studies: List of study dictionaries with 'r', 'se', 'author', 'year'.
        pooled_r: The pooled effect size (weighted mean r).
        pooled_se: Standard error of the pooled effect (optional).
        output_path: Path to save the plot.
        
    Returns:
        Path to the saved plot.
    """
    if not studies:
        logger.warning("No studies provided for forest plot. Creating empty plot.")
        # Create a placeholder plot if no data
        fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))
        ax.text(0.5, 0.5, "No studies available for visualization", 
                transform=ax.transAxes, ha='center', va='center', fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=DENSITY, bbox_inches='tight')
        plt.close()
        return output_path
    
    # Sort studies by year for better visualization
    studies = sorted(studies, key=lambda x: x.get('year', 0))
    
    n_studies = len(studies)
    y_positions = np.arange(n_studies)
    
    # Extract data
    r_values = [s['r'] for s in studies]
    se_values = [s['se'] for s in studies]
    authors = [s['author'] for s in studies]
    years = [s['year'] for s in studies]
    
    # Calculate CIs
    lower_bounds = [r - 1.96 * se for r, se in zip(r_values, se_values)]
    upper_bounds = [r + 1.96 * se for r, se in zip(r_values, se_values)]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))
    
    # Plot individual study points and CIs
    ax.errorbar(r_values, y_positions, xerr=[[r-lb for r, lb in zip(r_values, lower_bounds)], 
                                              [ub-r for ub, r in zip(upper_bounds, r_values)]], 
                fmt='o', ecolor='gray', capsize=3, color='steelblue', alpha=0.7, label='Study')
    
    # Plot vertical line at r=0 (null effect)
    ax.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    
    # Plot pooled effect (diamond)
    if pooled_se:
        # Calculate CI for pooled effect
        pooled_lower = pooled_r - 1.96 * pooled_se
        pooled_upper = pooled_r + 1.96 * pooled_se
        
        # Draw diamond shape for pooled effect
        # Top point
        ax.plot(pooled_r, -1, 'D', color='red', markersize=10, label='Pooled Effect')
        # Draw lines for CI
        ax.plot([pooled_lower, pooled_upper], [-1, -1], color='red', linewidth=2)
    else:
        # If SE is not provided, just mark the point
        ax.plot(pooled_r, -1, 'D', color='red', markersize=10, label='Pooled Effect')
    
    # Labels and formatting
    ax.set_yticks(y_positions)
    ax.set_yticklabels([f"{a} ({y})" for a, y in zip(authors, years)], fontsize=8)
    ax.set_xlabel('Correlation Coefficient (r)')
    ax.set_title('Forest Plot: Structural Brain Connectivity vs. Music Preferences', fontsize=12, fontweight='bold')
    
    # Add a summary row label
    ax.text(0.0, -1, "Pooled", ha='right', va='center', fontsize=9, fontweight='bold')
    
    # Set limits with padding
    all_bounds = lower_bounds + upper_bounds
    min_x = min(all_bounds + [pooled_r - 0.1]) if all_bounds else -0.2
    max_x = max(all_bounds + [pooled_r + 0.1]) if all_bounds else 0.2
    ax.set_xlim(min(min_x, -0.2), max(max_x, 0.2))
    ax.set_ylim(-2, n_studies + 0.5)
    
    # Grid
    ax.grid(True, axis='x', linestyle=':', alpha=0.5)
    
    # Legend
    ax.legend(loc='upper left')
    
    # Save
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=DENSITY, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Forest plot saved to {output_path}")
    return output_path

def run_forest_plot_generation(
    results_path: str = RESULTS_JSON_PATH,
    csv_path: str = EXTRACTED_STUDIES_PATH,
    output_path: str = f"data/derived/{OUTPUT_FILENAME}"
) -> str:
    """
    Main function to orchestrate forest plot generation.
    
    1. Load results JSON to get pooled_r.
    2. Load extracted studies CSV to get individual study data.
    3. Generate plot.
    4. Save to disk.
    
    Returns:
        Path to the generated plot.
    """
    logger.info("Starting forest plot generation...")
    
    # Load results
    try:
        results = load_analysis_results(results_path)
        # Extract weighted_mean_r from results
        # The structure might vary, check common keys
        pooled_r = results.get('weighted_mean_r') or results.get('pooled_effect') or 0.0
        pooled_se = results.get('weighted_mean_se') or results.get('pooled_se')
        
        if pooled_r is None:
            logger.warning("weighted_mean_r not found in results.json. Using 0.0.")
            pooled_r = 0.0
            
    except Exception as e:
        logger.error(f"Failed to load results: {e}")
        # Fallback to 0 if results are missing
        pooled_r = 0.0
        pooled_se = None
        
    # Load studies
    try:
        studies = load_effect_sizes_for_plotting(csv_path)
        logger.info(f"Loaded {len(studies)} studies for plotting.")
    except Exception as e:
        logger.error(f"Failed to load studies: {e}")
        studies = []
        
    # Generate plot
    plot_path = create_forest_plot(
        studies=studies,
        pooled_r=pooled_r,
        pooled_se=pooled_se,
        output_path=output_path
    )
    
    return plot_path

def main():
    """Entry point for script execution."""
    logger.info("Executing Forest Plot Generation (T027a)")
    
    try:
        output = run_forest_plot_generation()
        logger.info(f"Success: {output}")
        return 0
    except Exception as e:
        logger.critical(f"Forest plot generation failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())