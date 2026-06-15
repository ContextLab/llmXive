"""
Complexity Visualization Module

Generates visualization examples showing how complexity metrics (crossing number,
braid index) map to knot diagram features, per dan-rockmore-simulated review.
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from reproducibility.logs import log_operation, get_logger


@dataclass
class VisualizationSpec:
    """Specification for a complexity visualization example."""
    title: str
    description: str
    x_metric: str
    y_metric: str
    hue_metric: Optional[str] = None
    plot_type: str = "scatter"  # scatter, histogram, boxplot
    sample_size: Optional[int] = None


def load_cleaned_knots(data_path: Path) -> pd.DataFrame:
    """Load cleaned knot data from CSV file."""
    logger = get_logger()
    log_operation(logger, "load_cleaned_knots", "data", str(data_path),
                parameters={"data_path": str(data_path)}, status="started")

    try:
        df = pd.read_csv(data_path)
        log_operation(logger, "load_cleaned_knots", "data", str(data_path),
                    parameters={"data_path": str(data_path)},
                    status="completed",
                    input_file=str(data_path),
                    output_file=str(data_path))
        return df
    except Exception as e:
        log_operation(logger, "load_cleaned_knots", "data", str(data_path),
                    parameters={"data_path": str(data_path)},
                    status="failed",
                    input_file=str(data_path))
        raise


def create_complexity_heatmap(df: pd.DataFrame, ax: plt.Axes) -> None:
    """Create heatmap showing correlation between complexity metrics."""
    # Select numeric columns for correlation
    numeric_cols = ['crossing_number', 'braid_index']
    if 'hyperbolic_volume' in df.columns:
        numeric_cols.append('hyperbolic_volume')

    corr_matrix = df[numeric_cols].corr()

    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0,
               square=True, linewidths=0.5, ax=ax,
               cbar_kws={'shrink': 0.8})
    ax.set_title('Complexity Metrics Correlation', fontsize=14, fontweight='bold')
    ax.set_ylabel('Metric', fontsize=12)
    ax.set_xlabel('Metric', fontsize=12)


def create_crossing_braid_scatter(df: pd.DataFrame, ax: plt.Axes) -> None:
    """Create scatter plot of crossing number vs braid index, stratified by alternating."""
    # Filter for valid data
    valid_df = df.dropna(subset=['crossing_number', 'braid_index'])

    # Separate alternating and non-alternating
    alt_mask = valid_df['is_alternating'] == True if 'is_alternating' in valid_df.columns else pd.Series([True] * len(valid_df))
    non_alt_mask = valid_df['is_alternating'] == False if 'is_alternating' in valid_df.columns else pd.Series([False] * len(valid_df))

    alt_df = valid_df[alt_mask]
    non_alt_df = valid_df[non_alt_mask]

    # Plot alternating knots
    if len(alt_df) > 0:
        ax.scatter(alt_df['crossing_number'], alt_df['braid_index'],
                  alpha=0.6, s=50, c='blue', label='Alternating', edgecolors='white')

    # Plot non-alternating knots
    if len(non_alt_df) > 0:
        ax.scatter(non_alt_df['crossing_number'], non_alt_df['braid_index'],
                  alpha=0.6, s=50, c='red', label='Non-Alternating', edgecolors='white')

    # Add reference line: braid index <= crossing number
    max_c = int(valid_df['crossing_number'].max()) + 1
    ax.plot([0, max_c], [0, max_c], 'k--', alpha=0.5, linewidth=1, label='braid ≤ crossing')

    ax.set_xlabel('Crossing Number', fontsize=12)
    ax.set_ylabel('Braid Index', fontsize=12)
    ax.set_title('Crossing Number vs Braid Index', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)


def create_complexity_distribution(df: pd.DataFrame, ax: plt.Axes) -> None:
    """Create distribution plot of crossing numbers."""
    valid_df = df.dropna(subset=['crossing_number'])

    # Create histogram with KDE
    sns.histplot(data=valid_df, x='crossing_number', kde=True,
                bins=range(0, int(valid_df['crossing_number'].max()) + 2),
                color='skyblue', edgecolor='black', ax=ax)

    ax.set_xlabel('Crossing Number', fontsize=12)
    ax.set_ylabel('Count', fontsize=12)
    ax.set_title('Distribution of Crossing Numbers', fontsize=14, fontweight='bold')
    ax.set_xticks(range(0, int(valid_df['crossing_number'].max()) + 1))


def create_braid_index_by_crossing(df: pd.DataFrame, ax: plt.Axes) -> None:
    """Create boxplot showing braid index distribution by crossing number."""
    valid_df = df.dropna(subset=['crossing_number', 'braid_index'])

    # Group by crossing number and create boxplot
    crossing_groups = valid_df.groupby('crossing_number')['braid_index']

    # Create boxplot data
    box_data = [group.values for _, group in crossing_groups]
    bp = ax.boxplot(box_data, patch_artist=True, widths=0.6)

    # Color boxes by median value
    for patch, median in zip(bp['boxes'], [g.median() for _, g in crossing_groups]):
        patch.set_facecolor(sns.color_palette('YlOrRd', 10)[int(min(median / 5, 9))])

    ax.set_xlabel('Crossing Number', fontsize=12)
    ax.set_ylabel('Braid Index', fontsize=12)
    ax.set_title('Braid Index Distribution by Crossing Number', fontsize=14, fontweight='bold')
    ax.set_xticks(range(1, len(box_data) + 1))
    ax.set_xticklabels(range(1, len(box_data) + 1), rotation=45)
    ax.grid(True, alpha=0.3, axis='y')


def create_complexity_feature_examples(df: pd.DataFrame, ax: plt.Axes) -> None:
    """Create example visualization showing complexity metric relationships."""
    # Select representative knots across complexity ranges
    valid_df = df.dropna(subset=['crossing_number', 'braid_index'])

    if len(valid_df) == 0:
        ax.text(0.5, 0.5, 'No valid data available', ha='center', va='center',
               transform=ax.transAxes, fontsize=14)
        return

    # Create a bubble chart showing complexity relationship
    sizes = np.clip(valid_df['braid_index'] * 100, 50, 500)

    scatter = ax.scatter(valid_df['crossing_number'], valid_df['hyperbolic_volume'] if 'hyperbolic_volume' in valid_df.columns else valid_df['braid_index'],
                        s=sizes, alpha=0.5, c=valid_df['crossing_number'],
                        cmap='viridis', edgecolors='black')

    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Crossing Number', fontsize=10)

    ax.set_xlabel('Crossing Number' if 'hyperbolic_volume' not in valid_df.columns else 'Crossing Number', fontsize=12)
    ax.set_ylabel('Braid Index' if 'hyperbolic_volume' not in valid_df.columns else 'Hyperbolic Volume', fontsize=12)
    ax.set_title('Complexity Metrics: Size = Braid Index', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)


def generate_complexity_visualization_examples(df: pd.DataFrame, output_path: Path,
                                               figsize: Tuple[int, int] = (16, 12)) -> Path:
    """
    Generate visualization examples showing how complexity metrics map to knot features.

    This creates a multi-panel figure demonstrating:
    - Correlation between complexity metrics
    - Crossing number vs braid index relationship
    - Distribution of crossing numbers
    - Braid index by crossing number
    - Complexity feature examples

    Args:
        df: DataFrame with knot data (crossing_number, braid_index, etc.)
        output_path: Path to save the visualization
        figsize: Figure size in inches

    Returns:
        Path to saved visualization file
    """
    logger = get_logger()
    log_operation(logger, "generate_complexity_visualization_examples", "analysis",
                str(output_path), parameters={"figsize": figsize}, status="started")

    try:
        # Create figure with subplots
        fig, axes = plt.subplots(2, 3, figsize=figsize)
        fig.suptitle('Knot Complexity Visualization Examples\n'
                    'Crossing Number & Braid Index Relationship',
                    fontsize=16, fontweight='bold', y=0.98)

        # Panel 1: Correlation heatmap
        create_complexity_heatmap(df, axes[0, 0])

        # Panel 2: Crossing vs braid scatter
        create_crossing_braid_scatter(df, axes[0, 1])

        # Panel 3: Crossing number distribution
        create_complexity_distribution(df, axes[0, 2])

        # Panel 4: Braid index by crossing number
        create_braid_index_by_crossing(df, axes[1, 0])

        # Panel 5: Complexity feature examples
        create_complexity_feature_examples(df, axes[1, 1])

        # Panel 6: Summary statistics text box
        ax6 = axes[1, 2]
        ax6.axis('off')

        # Calculate summary statistics
        valid_df = df.dropna(subset=['crossing_number', 'braid_index'])
        if len(valid_df) > 0:
            stats_text = f"""
            Summary Statistics

            Dataset Size: {len(valid_df)} knots
            Crossing Number Range: [{int(valid_df['crossing_number'].min())}, {int(valid_df['crossing_number'].max())}]
            Braid Index Range: [{int(valid_df['braid_index'].min())}, {int(valid_df['braid_index'].max())}]

            Mean Crossing Number: {valid_df['crossing_number'].mean():.2f}
            Mean Braid Index: {valid_df['braid_index'].mean():.2f}

            Correlation (r): {valid_df['crossing_number'].corr(valid_df['braid_index']):.3f}

            Alt/Non-Alt Split:
            - Alternating: {valid_df['is_alternating'].sum() if 'is_alternating' in valid_df.columns else 'N/A'}
            - Non-Alternating: {(~valid_df['is_alternating']).sum() if 'is_alternating' in valid_df.columns else 'N/A'}
            """
            ax6.text(0.1, 0.9, stats_text, transform=ax6.transAxes,
                    fontsize=10, verticalalignment='top',
                    fontfamily='monospace',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save figure
        plt.savefig(output_path, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close(fig)

        log_operation(logger, "generate_complexity_visualization_examples", "analysis",
                    str(output_path), parameters={"figsize": figsize},
                    status="completed",
                    input_file="data/processed/knots_cleaned.csv",
                    output_file=str(output_path))

        return output_path

    except Exception as e:
        log_operation(logger, "generate_complexity_visualization_examples", "analysis",
                    str(output_path), parameters={"figsize": figsize},
                    status="failed",
                    input_file="data/processed/knots_cleaned.csv")
        raise


def main() -> None:
    """Main entry point for complexity visualization generation."""
    logger = get_logger()
    log_operation(logger, "main", "analysis", "complexity_visualization.py",
                parameters={}, status="started")

    try:
        # Define paths
        base_path = Path(__file__).parent.parent.parent
        data_path = base_path / "data" / "processed" / "knots_cleaned.csv"
        output_path = base_path / "data" / "plots" / "complexity_visualization_examples.png"

        # Load data
        logger.info(f"Loading cleaned knot data from {data_path}")
        df = load_cleaned_knots(data_path)

        # Generate visualization
        logger.info(f"Generating complexity visualization examples")
        output_file = generate_complexity_visualization_examples(df, output_path)

        logger.info(f"Visualization saved to {output_file}")

        log_operation(logger, "main", "analysis", "complexity_visualization.py",
                    parameters={}, status="completed",
                    input_file=str(data_path),
                    output_file=str(output_file))

    except Exception as e:
        logger.error(f"Failed to generate complexity visualization: {e}")
        log_operation(logger, "main", "analysis", "complexity_visualization.py",
                    parameters={}, status="failed")
        raise


if __name__ == "__main__":
    main()
