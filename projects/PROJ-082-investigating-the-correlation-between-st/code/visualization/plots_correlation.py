"""
Correlation Summary Plot Generator for PROJ-082.

Generates a summary plot showing the distribution of effect sizes (r-values)
across different brain tracts, based on the meta-analysis results.

This task depends on:
- T042 (memory_monitor) for memory safety checks
- T014 (meta_analysis) for results data
"""
import json
import math
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Import project utilities
from utils.logger import get_logger
from utils.config import get_project_root, ensure_directory
from visualization.memory_monitor import check_memory_usage, get_memory_threshold_mb

# Configure logger
logger = get_logger(__name__)

def load_analysis_results(results_path: Path) -> Dict[str, Any]:
    """
    Load the meta-analysis results from the JSON file.
    
    Args:
        results_path: Path to the results JSON file (data/derived/results.json)
        
    Returns:
        Dictionary containing the analysis results
        
    Raises:
        FileNotFoundError: If the results file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    with open(results_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_effect_sizes_for_plotting(results: Dict[str, Any]) -> Tuple[List[str], List[float], List[float]]:
    """
    Extract tract names, effect sizes (r-values), and confidence intervals from results.
    
    Args:
        results: Dictionary containing meta-analysis results
        
    Returns:
        Tuple of (tract_names, effect_sizes, confidence_intervals)
    """
    tract_names = []
    effect_sizes = []
    confidence_intervals = []
    
    # Handle different possible result structures
    if 'by_tract' in results:
        # Structure: {"by_tract": {"tract_name": {"r": 0.5, "ci_lower": 0.3, "ci_upper": 0.7}}}
        for tract, data in results['by_tract'].items():
            if isinstance(data, dict) and 'r' in data:
                tract_names.append(tract)
                effect_sizes.append(float(data['r']))
                if 'ci_lower' in data and 'ci_upper' in data:
                    ci_width = float(data['ci_upper']) - float(data['ci_lower'])
                    confidence_intervals.append(ci_width)
                else:
                    confidence_intervals.append(0.0)  # Placeholder if CI not available
    elif 'results' in results and isinstance(results['results'], list):
        # Structure: {"results": [{"tract": "name", "r": 0.5, ...}, ...]}
        for item in results['results']:
            if isinstance(item, dict) and 'tract' in item and 'r' in item:
                tract_names.append(item['tract'])
                effect_sizes.append(float(item['r']))
                if 'ci_lower' in item and 'ci_upper' in item:
                    ci_width = float(item['ci_upper']) - float(item['ci_lower'])
                    confidence_intervals.append(ci_width)
                else:
                    confidence_intervals.append(0.0)
    else:
        # Fallback: try to extract from top-level if it's a simple dict
        for key, value in results.items():
            if isinstance(value, dict) and 'r' in value:
                tract_names.append(key)
                effect_sizes.append(float(value['r']))
                if 'ci_lower' in value and 'ci_upper' in value:
                    ci_width = float(value['ci_upper']) - float(value['ci_lower'])
                    confidence_intervals.append(ci_width)
                else:
                    confidence_intervals.append(0.0)
    
    if not tract_names:
        logger.warning("No effect sizes found in results for plotting. Returning empty lists.")
    
    return tract_names, effect_sizes, confidence_intervals

def create_correlation_summary_plot(
    tract_names: List[str],
    effect_sizes: List[float],
    confidence_intervals: List[float],
    output_path: Path,
    title: str = "Correlation Summary: Brain Tracts and Music Preferences"
) -> None:
    """
    Create and save the correlation summary plot.
    
    Args:
        tract_names: List of tract names
        effect_sizes: List of correlation coefficients (r-values)
        confidence_intervals: List of confidence interval widths
        output_path: Path where the plot will be saved
        title: Title for the plot
    """
    if not tract_names:
        logger.warning("No data to plot. Creating an empty plot with a message.")
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No data available for correlation summary', 
                transform=ax.transAxes, ha='center', va='center', fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        fig.suptitle(title, fontsize=12)
        ensure_directory(output_path.parent)
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return

    # Check memory usage before plotting
    if not check_memory_usage(get_memory_threshold_mb()):
        logger.error("Memory threshold exceeded. Aborting plot generation.")
        raise MemoryError("Memory threshold exceeded during plot generation")

    # Set style
    sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create a bar plot with error bars
    # Sort by effect size for better visualization
    sorted_indices = np.argsort(effect_sizes)
    sorted_tracts = [tract_names[i] for i in sorted_indices]
    sorted_effects = [effect_sizes[i] for i in sorted_indices]
    sorted_cis = [confidence_intervals[i] for i in sorted_indices]
    
    # Calculate error bars (symmetric around the mean)
    # If we have CI width, use half of it as the error
    errors = [ci / 2.0 if ci > 0 else 0.05 for ci in sorted_cis]  # Default to 0.05 if no CI
    
    x_pos = np.arange(len(sorted_tracts))
    
    # Create the bar plot
    bars = ax.bar(x_pos, sorted_effects, yerr=errors, capsize=5, 
                  color='steelblue', alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # Customize the plot
    ax.set_xticks(x_pos)
    ax.set_xticklabels(sorted_tracts, rotation=45, ha='right', fontsize=10)
    ax.set_ylabel('Correlation Coefficient (r)', fontsize=12)
    ax.set_xlabel('Brain Tract', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Add a horizontal line at r=0
    ax.axhline(y=0, color='red', linestyle='--', linewidth=1, alpha=0.7, label='No correlation')
    
    # Add a reference line for weak, moderate, strong correlations
    ax.axhline(y=0.1, color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
    ax.axhline(y=-0.1, color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
    
    # Add legend
    ax.legend(loc='upper left')
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save the figure
    ensure_directory(output_path.parent)
    fig.savefig(output_path, dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close(fig)
    
    logger.info(f"Correlation summary plot saved to: {output_path}")

def run_correlation_plot_generation(
    results_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Main function to generate the correlation summary plot.
    
    Args:
        results_path: Path to the results JSON file (default: data/derived/results.json)
        output_path: Path for the output PNG file (default: data/derived/correlation_summary.png)
        
    Returns:
        Path to the generated plot file
    """
    project_root = get_project_root()
    
    if results_path is None:
        results_path = project_root / "data" / "derived" / "results.json"
    
    if output_path is None:
        output_path = project_root / "data" / "derived" / "correlation_summary.png"
    
    logger.info(f"Loading results from: {results_path}")
    results = load_analysis_results(results_path)
    
    logger.info("Extracting effect sizes for plotting...")
    tract_names, effect_sizes, confidence_intervals = load_effect_sizes_for_plotting(results)
    
    logger.info(f"Found {len(tract_names)} tracts to plot.")
    
    logger.info(f"Generating correlation summary plot at: {output_path}")
    create_correlation_summary_plot(
        tract_names=tract_names,
        effect_sizes=effect_sizes,
        confidence_intervals=confidence_intervals,
        output_path=output_path,
        title="Correlation Summary: Structural Brain Connectivity vs. Music Preferences"
    )
    
    return output_path

def main() -> int:
    """
    Entry point for the correlation plot generation script.
    
    Returns:
        0 on success, 1 on failure
    """
    try:
        logger.info("Starting correlation summary plot generation (T027c)...")
        output_path = run_correlation_plot_generation()
        
        if output_path.exists():
            file_size = output_path.stat().st_size
            logger.info(f"Successfully generated plot: {output_path} ({file_size} bytes)")
            return 0
        else:
            logger.error(f"Failed to generate plot file: {output_path}")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in results file: {e}")
        return 1
    except MemoryError as e:
        logger.error(f"Memory error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during plot generation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())