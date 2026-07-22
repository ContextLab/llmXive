"""
Visualization module for generating publication-quality plots.
Implements box plots with 95% CI error bars for key metrics.
"""
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from utils.logger import get_logger
import os
from pathlib import Path
from typing import Optional, List

logger = get_logger(__name__)


class Visualizer:
    """Generates visualization plots for usability metrics."""

    def __init__(self, output_dir: str = "figures"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Visualization output directory set to: {self.output_dir}")

    def _create_boxplot_with_ci(
        self,
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str,
        xlabel: str,
        ylabel: str,
        output_filename: str,
        ci_level: float = 0.95
    ) -> str:
        """
        Create a box plot with 95% confidence interval error bars.

        Args:
            data: DataFrame containing the data
            x_col: Column name for x-axis categories
            y_col: Column name for y-axis values
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            output_filename: Name of the output file
            ci_level: Confidence level for error bars (default 0.95)

        Returns:
            Path to the saved figure
        """
        plt.figure(figsize=(10, 6))
        ax = plt.gca()

        # Group by x_col and compute statistics
        groups = data.groupby(x_col)[y_col]

        # Calculate means and standard errors for error bars
        means = groups.mean()
        stds = groups.std()
        n = groups.count()
        se = stds / np.sqrt(n)

        # Calculate 95% CI using t-distribution
        from scipy import stats
        t_crit = stats.t.ppf((1 + ci_level) / 2, n - 1)
        ci = t_crit * se

        # Plot boxplot
        bp = ax.boxplot(
            [data[data[x_col] == cat][y_col] for cat in data[x_col].unique()],
            labels=data[x_col].unique(),
            patch_artist=True,
            showfliers=False
        )

        # Color the boxes
        colors = ['#4C72B0', '#DD8452']
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        # Add error bars representing 95% CI
        for i, (mean, err) in enumerate(zip(means.values, ci.values)):
            ax.errorbar(
                i + 1, mean, yerr=[[err], [err]],
                fmt='o', color='black', capsize=5,
                markersize=8, markeredgewidth=1.5
            )

        plt.title(title, fontsize=14, fontweight='bold')
        plt.xlabel(xlabel, fontsize=12)
        plt.ylabel(ylabel, fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.3)
        plt.tight_layout()

        output_path = self.output_dir / output_filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Saved visualization to: {output_path}")
        return str(output_path)

    def plot_completion_time(self, data: pd.DataFrame) -> str:
        """
        Generate box plot for completion time.

        Args:
            data: DataFrame with columns ['interface_type', 'completion_time_seconds']

        Returns:
            Path to saved figure
        """
        return self._create_boxplot_with_ci(
            data=data,
            x_col='interface_type',
            y_col='completion_time_seconds',
            title='Completion Time by Interface Type',
            xlabel='Interface Type',
            ylabel='Completion Time (seconds)',
            output_filename='completion_time.png'
        )

    def plot_error_count(self, data: pd.DataFrame) -> str:
        """
        Generate box plot for error count.

        Args:
            data: DataFrame with columns ['interface_type', 'error_count']

        Returns:
            Path to saved figure
        """
        return self._create_boxplot_with_ci(
            data=data,
            x_col='interface_type',
            y_col='error_count',
            title='Error Count by Interface Type',
            xlabel='Interface Type',
            ylabel='Number of Errors',
            output_filename='error_count.png'
        )

    def plot_sus_score(self, data: pd.DataFrame) -> str:
        """
        Generate box plot for SUS (System Usability Scale) scores.

        Args:
            data: DataFrame with columns ['interface_type', 'sus_score']

        Returns:
            Path to saved figure
        """
        return self._create_boxplot_with_ci(
            data=data,
            x_col='interface_type',
            y_col='sus_score',
            title='System Usability Scale (SUS) Score by Interface Type',
            xlabel='Interface Type',
            ylabel='SUS Score (0-100)',
            output_filename='sus_score.png'
        )

    def plot_explanation_engagement(self, data: pd.DataFrame) -> str:
        """
        Generate box plot for explanation engagement time.

        Args:
            data: DataFrame with columns ['interface_type', 'explanation_engagement_time_seconds']

        Returns:
            Path to saved figure
        """
        return self._create_boxplot_with_ci(
            data=data,
            x_col='interface_type',
            y_col='explanation_engagement_time_seconds',
            title='Explanation Engagement Time by Interface Type',
            xlabel='Interface Type',
            ylabel='Engagement Time (seconds)',
            output_filename='explanation_engagement.png'
        )


def main():
    """
    Main entry point for generating visualizations.
    Loads cleaned data and generates all required plots.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Generate visualization plots')
    parser.add_argument('--input', type=str, default='data/processed/cleaned_sessions.csv',
                      help='Path to cleaned data CSV')
    parser.add_argument('--output_dir', type=str, default='figures',
                      help='Output directory for figures')
    args = parser.parse_args()

    # Load data
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    logger.info(f"Loading data from: {args.input}")
    data = pd.read_csv(args.input)

    # Validate required columns
    required_cols = ['interface_type', 'completion_time_seconds', 'error_count', 'sus_score']
    missing_cols = [col for col in required_cols if col not in data.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        sys.exit(1)

    # Initialize visualizer
    visualizer = Visualizer(output_dir=args.output_dir)

    # Generate plots
    logger.info("Generating completion time plot...")
    visualizer.plot_completion_time(data)

    logger.info("Generating error count plot...")
    visualizer.plot_error_count(data)

    logger.info("Generating SUS score plot...")
    visualizer.plot_sus_score(data)

    # Only plot if explanation engagement time exists
    if 'explanation_engagement_time_seconds' in data.columns:
        logger.info("Generating explanation engagement plot...")
        visualizer.plot_explanation_engagement(data)

    logger.info("All visualizations generated successfully.")


if __name__ == '__main__':
    main()
