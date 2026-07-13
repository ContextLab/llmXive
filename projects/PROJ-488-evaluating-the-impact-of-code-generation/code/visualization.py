"""
Visualization module for generating boxplot figures comparing human-written
and LLM-generated code metrics.
"""
import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import existing project utilities
from logging_config import setup_logger, get_logger
from state_tracker import update_state_with_artifact, load_state_file, save_state_file
from seeds import get_seed_value

# Configure logger
logger = get_logger(__name__)

# Constants
FIGURE_DPI = 300
FIGURE_WIDTH = 10
FIGURE_HEIGHT = 7
FIGURE_FORMAT = 'png'
STATE_FILE_PATH = Path('state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml')
OUTPUT_DIR = Path('results/figures')

# Metric column names expected in the aggregated CSVs
METRIC_COLUMNS = [
    'cyclomatic_complexity',
    'loc',
    'maintainability_index',
    'potential_bug_count',
    'style_issue_count'
]

def load_metric_data(metric_type: str, data_dir: Path) -> Optional[pd.DataFrame]:
    """
    Load aggregated metric data from CSV file.

    Args:
        metric_type: The type of metric (e.g., 'cyclomatic_complexity')
        data_dir: Directory containing the metric CSV files

    Returns:
        DataFrame with metric data or None if file not found
    """
    file_path = data_dir / f"{metric_type}_aggregated.csv"
    if not file_path.exists():
        logger.warning(f"Metric file not found: {file_path}")
        return None

    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} rows from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None

def create_boxplot(
    df: pd.DataFrame,
    metric_type: str,
    output_path: Path,
    xlabel: str = "Dataset Group",
    ylabel: str = "Score",
    title: str = None
) -> bool:
    """
    Create a boxplot comparing metric distributions between human and LLM code.

    Args:
        df: DataFrame containing metric values and group labels
        metric_type: Name of the metric being plotted
        output_path: Path to save the figure
        xlabel: Label for x-axis
        ylabel: Label for y-axis
        title: Optional title for the plot

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Set random seed for reproducibility
        seed = get_seed_value()
        np.random.seed(seed)
        plt.rcParams['figure.dpi'] = FIGURE_DPI
        plt.rcParams['savefig.dpi'] = FIGURE_DPI

        # Prepare data for boxplot
        # Expected columns: 'group' (human/llm) and the metric value column
        group_col = 'group'
        value_col = metric_type

        if group_col not in df.columns or value_col not in df.columns:
            logger.error(f"DataFrame missing required columns. Available: {df.columns.tolist()}")
            return False

        # Filter out NaN values
        df_clean = df[[group_col, value_col]].dropna()

        if len(df_clean) == 0:
            logger.error("No valid data points after filtering NaN values")
            return False

        # Create figure and axis
        fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))

        # Prepare data for boxplot
        groups = df_clean[group_col].unique()
        data_to_plot = [
            df_clean[df_clean[group_col] == g][value_col].values
            for g in sorted(groups)
        ]

        # Create boxplot with custom styling
        bp = ax.boxplot(
            data_to_plot,
            labels=[g.capitalize() for g in sorted(groups)],
            patch_artist=True,
            showmeans=True,
            meanline=True,
            showfliers=True
        )

        # Color the boxes
        colors = ['#3498db', '#e74c3c']  # Blue for human, Red for LLM
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        # Style the means
        for meanline in bp['medians']:
            meanline.set_color('black')
            meanline.set_linewidth(2)

        # Add labels and title
        if title is None:
            title = f"Distribution of {metric_type.replace('_', ' ').title()}\n(Human vs LLM Generated Code)"

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)

        # Add grid for readability
        ax.yaxis.grid(True, linestyle='--', alpha=0.7)
        ax.set_axisbelow(True)

        # Add statistical annotations if available in the dataframe
        # Look for columns containing statistical test results
        stat_cols = [col for col in df.columns if 'p_value' in col.lower() or 'cliffs' in col.lower()]
        if stat_cols:
            # Add a text box with key statistics
            stats_text = []
            for col in stat_cols:
                if len(df[col]) > 0 and not pd.isna(df[col].iloc[0]):
                    stats_text.append(f"{col}: {df[col].iloc[0]:.4f}")

            if stats_text:
                ax.text(
                    0.98, 0.98, '\n'.join(stats_text),
                    transform=ax.transAxes,
                    fontsize=10,
                    verticalalignment='top',
                    horizontalalignment='right',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
                )

        # Save the figure
        plt.tight_layout()
        plt.savefig(output_path, format=FIGURE_FORMAT, bbox_inches='tight')
        plt.close(fig)

        logger.info(f"Successfully saved boxplot to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error creating boxplot for {metric_type}: {e}")
        return False

def generate_all_boxplots(
    data_dir: Path,
    output_dir: Optional[Path] = None
) -> Dict[str, str]:
    """
    Generate boxplot figures for all available metrics.

    Args:
        data_dir: Directory containing aggregated metric CSV files
        output_dir: Directory to save figures (defaults to results/figures)

    Returns:
        Dictionary mapping metric names to output file paths
    """
    if output_dir is None:
        output_dir = OUTPUT_DIR

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_files = {}

    for metric_type in METRIC_COLUMNS:
        logger.info(f"Processing metric: {metric_type}")

        # Load data
        df = load_metric_data(metric_type, data_dir)
        if df is None:
            logger.warning(f"Skipping {metric_type} - no data available")
            continue

        # Check if we have both human and LLM groups
        if 'group' in df.columns:
            unique_groups = df['group'].unique()
            if len(unique_groups) < 2:
                logger.warning(f"Skipping {metric_type} - only one group found: {unique_groups}")
                continue

        # Create output filename
        output_filename = f"{metric_type}_boxplot.{FIGURE_FORMAT}"
        output_path = output_dir / output_filename

        # Generate the boxplot
        success = create_boxplot(
            df=df,
            metric_type=metric_type,
            output_path=output_path,
            title=f"{metric_type.replace('_', ' ').title()} Distribution Comparison"
        )

        if success:
            generated_files[metric_type] = str(output_path)
            logger.info(f"Generated: {output_path}")
        else:
            logger.error(f"Failed to generate boxplot for {metric_type}")

    return generated_files

def update_state_with_figures(generated_files: Dict[str, str]):
    """
    Update the project state file with references to generated figures.

    Args:
        generated_files: Dictionary mapping metric names to figure paths
    """
    try:
        state = load_state_file(STATE_FILE_PATH)
        if state is None:
            logger.warning("State file not found, skipping update")
            return

        # Add figures to state
        if 'artifacts' not in state:
            state['artifacts'] = {}

        state['artifacts']['visualization_figures'] = {
            'generated_at': str(pd.Timestamp.now()),
            'files': generated_files
        }

        save_state_file(STATE_FILE_PATH, state)
        logger.info("Updated state file with figure references")

    except Exception as e:
        logger.error(f"Error updating state file: {e}")

def run_visualization_pipeline(
    data_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, str]:
    """
    Run the complete visualization pipeline.

    Args:
        data_dir: Directory containing aggregated metric data
        output_dir: Directory to save generated figures

    Returns:
        Dictionary of generated figure paths
    """
    if data_dir is None:
        data_dir = Path('data/metrics')

    data_dir = Path(data_dir)
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return {}

    logger.info(f"Starting visualization pipeline...")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Output directory: {output_dir or OUTPUT_DIR}")

    # Generate all boxplots
    generated_files = generate_all_boxplots(data_dir, output_dir)

    if not generated_files:
        logger.warning("No figures were generated")
        return generated_files

    logger.info(f"Successfully generated {len(generated_files)} figures")

    # Update state file
    update_state_with_figures(generated_files)

    return generated_files

def main():
    """Main entry point for the visualization script."""
    logger.info("=" * 60)
    logger.info("Starting Boxplot Visualization Pipeline")
    logger.info("=" * 60)

    # Run the pipeline
    generated_files = run_visualization_pipeline()

    if generated_files:
        logger.info("Generated figures:")
        for metric, path in generated_files.items():
            logger.info(f"  {metric}: {path}")
    else:
        logger.warning("No figures were generated. Check logs for details.")

    logger.info("=" * 60)
    logger.info("Visualization Pipeline Complete")
    logger.info("=" * 60)

    return generated_files

if __name__ == "__main__":
    main()
