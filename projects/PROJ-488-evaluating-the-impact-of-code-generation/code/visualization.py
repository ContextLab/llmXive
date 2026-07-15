"""
Visualization module for generating boxplot visualizations of metric distributions.
Generates figures for each metric type comparing human-written vs LLM-generated code.
"""

import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Import from existing project modules
from data_model import MetricResult
from state_tracker import update_state_with_artifact, load_state_file, save_state_file
from logging_config import get_logger
from seeds import set_seed

# Configure logging
logger = get_logger("visualization")

# Constants
FIGURE_DIR = Path("results/figures")
METRICS_DIR = Path("data/metrics")
METRIC_TYPES = [
    "cyclomatic_complexity",
    "maintainability_index",
    "loc",
    "bug_potential",
    "style_issues"
]
GROUP_LABELS = {
    "human": "Human-Written",
    "codegen": "LLM-Generated (CodeParrot/CodeGen)"
}

def load_metric_data(metric_type: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load metric data for human and LLM groups from CSV files.
    
    Args:
        metric_type: The type of metric to load (e.g., 'cyclomatic_complexity')
        
    Returns:
        Tuple of (human_df, codegen_df) DataFrames
    """
    human_path = METRICS_DIR / f"human_{metric_type}.csv"
    codegen_path = METRICS_DIR / f"codegen_{metric_type}.csv"
    
    if not human_path.exists() or not codegen_path.exists():
        logger.warning(f"Missing metric files for {metric_type}: {human_path.exists()}, {codegen_path.exists()}")
        return None, None
    
    try:
        human_df = pd.read_csv(human_path)
        codegen_df = pd.read_csv(codegen_path)
        logger.info(f"Loaded {len(human_df)} human and {len(codegen_df)} codegen snippets for {metric_type}")
        return human_df, codegen_df
    except Exception as e:
        logger.error(f"Error loading metric data for {metric_type}: {e}")
        return None, None

def create_boxplot(
    metric_type: str,
    human_data: List[float],
    codegen_data: List[float],
    output_path: Path,
    figsize: Tuple[int, int] = (10, 6)
) -> bool:
    """
    Create a boxplot visualization comparing human and LLM-generated code metrics.
    
    Args:
        metric_type: The metric type being visualized
        human_data: List of metric values for human-written code
        codegen_data: List of metric values for LLM-generated code
        output_path: Path to save the figure
        figsize: Figure size in inches
        
    Returns:
        True if successful, False otherwise
    """
    set_seed(42)  # Reproducibility
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Prepare data for boxplot
    data_to_plot = [human_data, codegen_data]
    labels = [GROUP_LABELS["human"], GROUP_LABELS["codegen"]]
    
    # Create boxplot
    bp = ax.boxplot(data_to_plot, labels=labels, patch_artist=True, notch=True)
    
    # Color the boxes
    colors = ['#3498db', '#e74c3c']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # Add median lines
    for i, line in enumerate(bp['medians']):
        line.set_color('black')
        line.set_linewidth(2)
    
    # Calculate and annotate statistics
    human_stats = {
        'mean': np.mean(human_data),
        'median': np.median(human_data),
        'std': np.std(human_data),
        'q1': np.percentile(human_data, 25),
        'q3': np.percentile(human_data, 75)
    }
    
    codegen_stats = {
        'mean': np.mean(codegen_data),
        'median': np.median(codegen_data),
        'std': np.std(codegen_data),
        'q1': np.percentile(codegen_data, 25),
        'q3': np.percentile(codegen_data, 75)
    }
    
    # Add statistics text box
    stats_text = (
        f"Human: Median={human_stats['median']:.2f}, IQR={human_stats['q3']-human_stats['q1']:.2f}\n"
        f"LLM:   Median={codegen_stats['median']:.2f}, IQR={codegen_stats['q3']-codegen_stats['q1']:.2f}"
    )
    
    ax.text(
        0.98, 0.98, stats_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment='top',
        horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    # Labels and title
    metric_title = metric_type.replace('_', ' ').title()
    ax.set_title(f'{metric_title} Distribution: Human vs LLM-Generated Code', fontsize=14, fontweight='bold')
    ax.set_ylabel(metric_title, fontsize=12)
    ax.set_xlabel('Source', fontsize=12)
    
    # Grid for better readability
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Save figure
    try:
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"Saved boxplot for {metric_type} to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving boxplot for {metric_type}: {e}")
        plt.close(fig)
        return False

def generate_all_boxplots() -> Dict[str, str]:
    """
    Generate boxplot visualizations for all metric types.
    
    Returns:
        Dictionary mapping metric type to output file path
    """
    if not FIGURE_DIR.exists():
        FIGURE_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created figure directory: {FIGURE_DIR}")
    
    results = {}
    
    for metric_type in METRIC_TYPES:
        logger.info(f"Processing {metric_type}...")
        human_df, codegen_df = load_metric_data(metric_type)
        
        if human_df is None or codegen_df is None:
            logger.warning(f"Skipping {metric_type} due to missing data")
            continue
        
        # Extract metric values (assuming column name matches metric_type)
        if metric_type not in human_df.columns or metric_type not in codegen_df.columns:
            # Try to find the actual column
            available_cols_human = list(human_df.columns)
            available_cols_codegen = list(codegen_df.columns)
            logger.warning(f"Column '{metric_type}' not found. Human cols: {available_cols_human}, Codegen cols: {available_cols_codegen}")
            continue
        
        human_data = human_df[metric_type].dropna().tolist()
        codegen_data = codegen_df[metric_type].dropna().tolist()
        
        if len(human_data) < 3 or len(codegen_data) < 3:
            logger.warning(f"Insufficient data for {metric_type}: human={len(human_data)}, codegen={len(codegen_data)}")
            continue
        
        output_filename = f"boxplot_{metric_type}.png"
        output_path = FIGURE_DIR / output_filename
        
        success = create_boxplot(
            metric_type=metric_type,
            human_data=human_data,
            codegen_data=codegen_data,
            output_path=output_path
        )
        
        if success:
            results[metric_type] = str(output_path)
            logger.info(f"Successfully generated {output_filename}")
        else:
            logger.error(f"Failed to generate boxplot for {metric_type}")
    
    return results

def update_state_with_figures(figures: Dict[str, str]):
    """
    Update the project state file with the generated figures.
    
    Args:
        figures: Dictionary mapping metric type to figure path
    """
    if not figures:
        logger.warning("No figures to register in state")
        return
    
    state_path = Path("state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml")
    if not state_path.exists():
        logger.warning(f"State file not found: {state_path}")
        return
    
    try:
        state = load_state_file(state_path)
        
        if "artifacts" not in state:
            state["artifacts"] = {}
        
        if "figures" not in state["artifacts"]:
            state["artifacts"]["figures"] = {}
        
        for metric_type, figure_path in figures.items():
            state["artifacts"]["figures"][metric_type] = {
                "path": figure_path,
                "type": "boxplot",
                "generated_at": str(pd.Timestamp.now())
            }
        
        save_state_file(state_path, state)
        logger.info(f"Updated state file with {len(figures)} figures")
    except Exception as e:
        logger.error(f"Error updating state with figures: {e}")

def run_visualization_pipeline() -> Dict[str, str]:
    """
    Run the complete visualization pipeline: load data, generate boxplots, update state.
    
    Returns:
        Dictionary mapping metric type to output file path
    """
    logger.info("Starting visualization pipeline...")
    
    # Generate all boxplots
    figures = generate_all_boxplots()
    
    if not figures:
        logger.warning("No figures were generated")
        return figures
    
    # Update state
    update_state_with_figures(figures)
    
    logger.info(f"Visualization pipeline complete. Generated {len(figures)} figures.")
    return figures

def main():
    """Main entry point for the visualization module."""
    logger.info("Running visualization module as main script...")
    
    try:
        figures = run_visualization_pipeline()
        
        if figures:
            logger.info("Generated figures:")
            for metric, path in figures.items():
                logger.info(f"  {metric}: {path}")
        else:
            logger.warning("No figures were generated. Check logs for errors.")
            return 1
        
        return 0
    except Exception as e:
        logger.error(f"Fatal error in visualization pipeline: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
