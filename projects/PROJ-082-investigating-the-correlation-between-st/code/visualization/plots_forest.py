"""
Forest Plot Generation for Meta-Analysis of Brain Connectivity and Music Preferences.

This module generates a forest plot visualizing individual study effect sizes (r-values)
and their confidence intervals, alongside the pooled summary effect (diamond).
"""

import json
import math
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon

# Import from project utilities
from utils.config import get_project_root
from utils.logger import get_logger
from visualization.memory_monitor import check_memory_usage, log_memory_snapshot

# Initialize logger
logger = get_logger(__name__)


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def load_analysis_results(results_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the meta-analysis results from the JSON file.

    Args:
        results_path: Path to the results JSON file. Defaults to data/derived/results.json.

    Returns:
        Dictionary containing analysis results.

    Raises:
        FileNotFoundError: If the results file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if results_path is None:
        results_path = get_project_root() / "data" / "derived" / "results.json"

    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")

    with open(results_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_effect_sizes_for_plotting(
    extracted_studies_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Load individual study effect sizes and standard errors for plotting.

    Args:
        extracted_studies_path: Path to the extracted studies CSV. Defaults to
                                data/processed/extracted_studies.csv.

    Returns:
        List of dictionaries containing 'author', 'year', 'r', 'se', 'ci_lower', 'ci_upper'.
    """
    if extracted_studies_path is None:
        extracted_studies_path = get_project_root() / "data" / "processed" / "extracted_studies.csv"

    if not extracted_studies_path.exists():
        raise FileNotFoundError(f"Extracted studies file not found: {extracted_studies_path}")

    import csv
    studies = []
    with open(extracted_studies_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only include studies with valid r and n values
            try:
                r_val = float(row.get('r', 0))
                n_val = int(row.get('n', 0))
                if n_val > 0:
                    # Calculate standard error of r (approximate)
                    # SE_r = 1 / sqrt(N - 3) for Fisher's z, but we use r directly here
                    # A common approximation for SE of r is sqrt((1-r^2)/(n-2))
                    se = math.sqrt((1 - r_val**2) / (n_val - 2)) if n_val > 2 else 0.5
                    
                    # Calculate 95% CI for r
                    # Using Fisher's z-transformation for better accuracy
                    z = 0.5 * math.log((1 + r_val) / (1 - r_val + 1e-10))
                    se_z = 1 / math.sqrt(n_val - 3)
                    z_lower = z - 1.96 * se_z
                    z_upper = z + 1.96 * se_z
                    
                    r_lower = (math.exp(2 * z_lower) - 1) / (math.exp(2 * z_lower) + 1)
                    r_upper = (math.exp(2 * z_upper) - 1) / (math.exp(2 * z_upper) + 1)
                    
                    studies.append({
                        'author': row.get('author', 'Unknown'),
                        'year': row.get('year', 'N/A'),
                        'r': r_val,
                        'se': se,
                        'ci_lower': r_lower,
                        'ci_upper': r_upper,
                        'n': n_val
                    })
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid row: {row} - Error: {e}")
                continue

    return studies


def calculate_ci(r: float, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate confidence interval for a correlation coefficient using Fisher's z-transformation.

    Args:
        r: Correlation coefficient.
        n: Sample size.
        alpha: Significance level (default 0.05 for 95% CI).

    Returns:
        Tuple of (lower_bound, upper_bound).
    """
    if n <= 3:
        return (r - 1.0, r + 1.0)  # Fallback for very small samples

    # Fisher's z-transformation
    z = 0.5 * math.log((1 + r) / (1 - r + 1e-10))
    se_z = 1 / math.sqrt(n - 3)
    
    # Critical value for normal distribution
    z_crit = 1.96 if alpha == 0.05 else 2.576  # 99% CI for alpha=0.01
    
    z_lower = z - z_crit * se_z
    z_upper = z + z_crit * se_z
    
    # Back-transform to r
    r_lower = (math.exp(2 * z_lower) - 1) / (math.exp(2 * z_lower) + 1)
    r_upper = (math.exp(2 * z_upper) - 1) / (math.exp(2 * z_upper) + 1)
    
    return (r_lower, r_upper)


def create_forest_plot(
    studies: List[Dict[str, Any]],
    weighted_mean_r: float,
    ci_lower: float,
    ci_upper: float,
    i_squared: Optional[float] = None,
    output_path: Optional[Path] = None
) -> None:
    """
    Create and save a forest plot.

    Args:
        studies: List of study dictionaries with r, se, ci_lower, ci_upper.
        weighted_mean_r: The pooled effect size (weighted mean r).
        ci_lower: Lower bound of the pooled effect CI.
        ci_upper: Upper bound of the pooled effect CI.
        i_squared: Heterogeneity statistic (I²).
        output_path: Path to save the plot. Defaults to data/derived/forest_plot.png.
    """
    if output_path is None:
        output_path = get_project_root() / "data" / "derived" / "forest_plot.png"

    # Check memory usage before plotting
    check_memory_usage(threshold_mb=6000)
    log_memory_snapshot("Forest Plot Generation Start")

    n_studies = len(studies)
    if n_studies == 0:
        logger.warning("No studies to plot. Creating empty forest plot.")
        # Create a minimal plot to avoid crashing
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No studies available for forest plot', 
                transform=ax.transAxes, ha='center', va='center', fontsize=12)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return

    # Sort studies by year for better visualization
    studies_sorted = sorted(studies, key=lambda x: int(x.get('year', 0)))

    # Create figure
    fig, ax = plt.subplots(figsize=(12, max(6, n_studies * 0.4 + 2)))

    # Plot parameters
    y_positions = range(n_studies)
    colors = plt.cm.viridis(np.linspace(0, 0.8, n_studies))

    # Plot individual studies
    for i, study in enumerate(studies_sorted):
        r_val = study['r']
        ci_l = study['ci_lower']
        ci_u = study['ci_upper']
        
        # Plot confidence interval line
        ax.plot([ci_l, ci_u], [i, i], color='gray', linewidth=1.5, alpha=0.7)
        
        # Plot effect size point (size proportional to sample size)
        point_size = min(100, max(20, study['n'] / 10))
        ax.scatter(r_val, i, s=point_size, c=[colors[i]], zorder=3, edgecolors='black', linewidths=0.5)

    # Plot summary diamond
    diamond_y = n_studies + 0.5
    diamond_width = ci_upper - ci_lower
    
    # Create diamond shape
    diamond_points = [
        (weighted_mean_r, diamond_y),  # Top
        (ci_upper, diamond_y + 0.3),   # Right
        (weighted_mean_r, diamond_y + 0.6),  # Bottom
        (ci_lower, diamond_y + 0.3)    # Left
    ]
    diamond = Polygon(diamond_points, closed=True, fill=True, color='red', alpha=0.6, edgecolor='darkred')
    ax.add_patch(diamond)

    # Vertical line at zero effect
    ax.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    
    # Vertical line at pooled effect
    ax.axvline(x=weighted_mean_r, color='red', linestyle='-', linewidth=1.5, alpha=0.8)

    # Labels and title
    ax.set_xlabel('Correlation Coefficient (r)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Study', fontsize=12, fontweight='bold')
    ax.set_title('Forest Plot: Brain Connectivity and Music Preferences', 
                fontsize=14, fontweight='bold', pad=20)

    # Y-axis labels
    ax.set_yticks(y_positions)
    ax.set_yticklabels([f"{s['author']} ({s['year']})" for s in studies_sorted], fontsize=10)

    # X-axis limits with padding
    x_min = min(ci_l for s in studies_sorted + [{'ci_lower': ci_lower}])
    x_max = max(ci_u for s in studies_sorted + [{'ci_upper': ci_upper}])
    padding = (x_max - x_min) * 0.1
    ax.set_xlim(x_min - padding, x_max + padding)

    # Add heterogeneity info if available
    if i_squared is not None:
        ax.text(1.02, -0.1, f"I² = {i_squared:.2f}%", transform=ax.transAxes, 
               fontsize=10, verticalalignment='bottom', horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Add summary stats
    summary_text = f"Pooled r = {weighted_mean_r:.3f} [{ci_lower:.3f}, {ci_upper:.3f}]"
    ax.text(1.02, -0.05, summary_text, transform=ax.transAxes, 
           fontsize=10, verticalalignment='bottom', horizontalalignment='right',
           bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

    # Layout adjustments
    plt.tight_layout()
    
    # Save plot
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    log_memory_snapshot("Forest Plot Generation Complete")
    logger.info(f"Forest plot saved to: {output_path}")


def run_forest_plot_generation(
    results_path: Optional[Path] = None,
    extracted_studies_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> None:
    """
    Main function to run the forest plot generation pipeline.

    Args:
        results_path: Path to the meta-analysis results JSON.
        extracted_studies_path: Path to the extracted studies CSV.
        output_path: Path to save the forest plot PNG.
    """
    try:
        # Load results
        results = load_analysis_results(results_path)
        
        # Check if we have the necessary data
        if 'weighted_mean_r' not in results:
            raise ValueError("Results file missing 'weighted_mean_r'. Cannot generate forest plot.")
        
        weighted_mean_r = results['weighted_mean_r']
        ci_lower = results.get('ci_lower', weighted_mean_r - 0.1)
        ci_upper = results.get('ci_upper', weighted_mean_r + 0.1)
        i_squared = results.get('i_squared', None)
        
        # Load individual studies
        studies = load_effect_sizes_for_plotting(extracted_studies_path)
        
        # Create and save the plot
        create_forest_plot(
            studies=studies,
            weighted_mean_r=weighted_mean_r,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            i_squared=i_squared,
            output_path=output_path
        )
        
        logger.info("Forest plot generation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in results file: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during forest plot generation: {e}")
        raise


def main() -> None:
    """Entry point for running the forest plot generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Forest Plot for Meta-Analysis')
    parser.add_argument('--results', type=str, help='Path to results JSON file')
    parser.add_argument('--studies', type=str, help='Path to extracted studies CSV')
    parser.add_argument('--output', type=str, help='Path to save the forest plot PNG')
    
    args = parser.parse_args()
    
    results_path = Path(args.results) if args.results else None
    studies_path = Path(args.studies) if args.studies else None
    output_path = Path(args.output) if args.output else None
    
    run_forest_plot_generation(
        results_path=results_path,
        extracted_studies_path=studies_path,
        output_path=output_path
    )


if __name__ == "__main__":
    main()