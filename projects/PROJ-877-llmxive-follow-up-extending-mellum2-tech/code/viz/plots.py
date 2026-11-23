"""
Visualization module for generating correlation plots and threshold analysis charts.

This script is invoked by the run-book to generate visual outputs for the
llmXive complexity-loss analysis pipeline.

Usage:
    python code/viz/plots.py --input data/results/us1_correlation_stats.json --output data/results/us1_correlation_plot.png
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_correlation_stats(input_path: str) -> Dict[str, Any]:
    """Load correlation statistics from JSON file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def generate_scatter_plot(
    data: Dict[str, Any],
    output_path: str,
    title: str = "Complexity vs Prediction Loss"
) -> None:
    """
    Generate scatter plots with regression lines for complexity vs loss data.
    
    Args:
        data: Dictionary containing correlation statistics and raw data
        output_path: Path to save the generated plot
        title: Plot title
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Check if we have Python and/or Java data
    has_python = 'python' in data and 'data' in data['python']
    has_java = 'java' in data and 'data' in data['java']
    
    if not has_python and not has_java:
        logger.warning("No valid data found for plotting. Creating empty placeholder.")
        # Create a placeholder plot indicating no data
        fig.suptitle("No Data Available for Plotting", fontsize=14)
        axes[0].text(0.5, 0.5, 'No Python data available', 
                    transform=axes[0].transAxes, ha='center', va='center')
        axes[1].text(0.5, 0.5, 'No Java data available', 
                    transform=axes[1].transAxes, ha='center', va='center')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return

    # Plot Python data if available
    if has_python:
        py_data = data['python']['data']
        if len(py_data) > 0:
            complexities = [d['complexity'] for d in py_data]
            losses = [d['loss'] for d in py_data]
            
            sns.regplot(
                x=complexities, y=losses,
                ax=axes[0],
                scatter_kws={'alpha': 0.6, 's': 40},
                line_kws={'color': 'red', 'linewidth': 2}
            )
            axes[0].set_title(f"Python: r={data['python'].get('pearson_r', 'N/A'):.3f}")
            axes[0].set_xlabel("Cyclomatic Complexity")
            axes[0].set_ylabel("Normalized Prediction Loss (nats)")
        else:
            axes[0].text(0.5, 0.5, 'No Python data', 
                        transform=axes[0].transAxes, ha='center', va='center')
            axes[0].set_title("Python Data Unavailable")
    else:
        axes[0].text(0.5, 0.5, 'No Python data', 
                    transform=axes[0].transAxes, ha='center', va='center')
        axes[0].set_title("Python Data Unavailable")

    # Plot Java data if available
    if has_java:
        java_data = data['java']['data']
        if len(java_data) > 0:
            complexities = [d['complexity'] for d in java_data]
            losses = [d['loss'] for d in java_data]
            
            sns.regplot(
                x=complexities, y=losses,
                ax=axes[1],
                scatter_kws={'alpha': 0.6, 's': 40, 'color': 'green'},
                line_kws={'color': 'darkgreen', 'linewidth': 2}
            )
            axes[1].set_title(f"Java: r={data['java'].get('pearson_r', 'N/A'):.3f}")
            axes[1].set_xlabel("Cyclomatic Complexity")
            axes[1].set_ylabel("Normalized Prediction Loss (nats)")
        else:
            axes[1].text(0.5, 0.5, 'No Java data', 
                        transform=axes[1].transAxes, ha='center', va='center')
            axes[1].set_title("Java Data Unavailable")
    else:
        axes[1].text(0.5, 0.5, 'No Java data', 
                    transform=axes[1].transAxes, ha='center', va='center')
        axes[1].set_title("Java Data Unavailable")

    fig.suptitle(title, fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Plot saved to: {output_path}")

def generate_threshold_plot(
    threshold_data: Dict[str, Any],
    output_path: str
) -> None:
    """
    Generate threshold detection visualization.
    
    Args:
        threshold_data: Dictionary containing threshold candidates and model comparison
        output_path: Path to save the generated plot
    """
    # This function would be expanded if threshold visualization is required
    # For now, we focus on the correlation plot which is the primary visualization
    logger.info("Threshold visualization not yet implemented in this module.")

def main():
    """Main entry point for the plots script."""
    parser = argparse.ArgumentParser(
        description='Generate visualization plots for llmXive analysis'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to input JSON file (e.g., us1_correlation_stats.json)'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Path to save the output plot (e.g., us1_correlation_plot.png)'
    )
    parser.add_argument(
        '--title',
        type=str,
        default="Complexity vs Prediction Loss",
        help='Title for the plot'
    )
    parser.add_argument(
        '--threshold-input',
        type=str,
        default=None,
        help='Optional: Path to threshold candidates JSON for threshold plots'
    )
    
    args = parser.parse_args()
    
    try:
        # Load correlation stats
        logger.info(f"Loading data from: {args.input}")
        correlation_data = load_correlation_stats(args.input)
        
        # Ensure output directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate scatter plot
        generate_scatter_plot(
            correlation_data,
            str(output_path),
            title=args.title
        )
        
        # If threshold input is provided, generate threshold plot
        if args.threshold_input:
            logger.info(f"Loading threshold data from: {args.threshold_input}")
            threshold_data = load_correlation_stats(args.threshold_input)
            threshold_output = str(output_path).replace('.png', '_threshold.png')
            generate_threshold_plot(threshold_data, threshold_output)
        
        logger.info("Visualization complete.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during plotting: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()