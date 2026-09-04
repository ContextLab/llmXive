import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import List, Dict, Optional, Union, Tuple
from pathlib import Path
import json
import logging
from .utils import get_logger

# Configure logger
logger = get_logger(__name__)

class VisualizationEngine:
    """
    Handles generation of visualizations for the network structure impact study.
    Produces high-resolution (300 DPI) figures as per FR-005.
    """

    def __init__(self, output_dir: Union[str, Path]):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        sns.set_theme(style="whitegrid")

    def generate_scatter_plot(
        self,
        x_data: List[float],
        y_data: List[float],
        x_label: str,
        y_label: str,
        title: str,
        output_filename: str,
        regression_line: bool = True,
        confidence_interval: float = 0.95
    ) -> str:
        """
        Generates a scatter plot with an optional regression line.
        
        Args:
            x_data: List of x-axis values (e.g., clustering coefficient).
            y_data: List of y-axis values (e.g., thermal conductivity).
            x_label: Label for the x-axis.
            y_label: Label for the y-axis.
            title: Plot title.
            output_filename: Name of the output file (e.g., 'scatter_clustering.png').
            regression_line: Whether to fit and draw a regression line.
            confidence_interval: Confidence interval for the regression line (default 0.95).
        
        Returns:
            Path to the generated figure file.
        
        Raises:
            ValueError: If data lengths do not match or N < 2 for regression.
        """
        if len(x_data) != len(y_data):
            raise ValueError("x_data and y_data must have the same length.")
        
        n = len(x_data)
        if n == 0:
            logger.warning("Empty data provided for scatter plot. Skipping generation.")
            return ""
        
        if n == 1:
            logger.warning("Only one data point provided. Cannot compute regression. Plotting point only.")
            regression_line = False
        
        # Convert to numpy for easier handling
        x = np.array(x_data)
        y = np.array(y_data)

        # Handle NaNs
        valid_mask = ~(np.isnan(x) | np.isnan(y))
        x_clean = x[valid_mask]
        y_clean = y[valid_mask]

        if len(x_clean) < 2:
            logger.warning(f"Insufficient valid data points ({len(x_clean)}) for regression. Plotting available points.")
            regression_line = False

        plt.figure(figsize=(10, 6))
        
        if regression_line and len(x_clean) >= 2:
            # Use regplot for regression line with CI
            # We pass the clean data to regplot, but we need to ensure the plot context is correct
            # regplot handles the plotting of points and line
            sns.regplot(
                x=x_clean, 
                y=y_clean, 
                ci=int(confidence_interval * 100), 
                scatter_kws={'s': 60, 'alpha': 0.7},
                line_kws={'color': 'red', 'linewidth': 2}
            )
        else:
            # Just scatter plot
            plt.scatter(x_clean, y_clean, s=60, alpha=0.7, edgecolors='k')
            if len(x_clean) == 0:
                logger.warning("No valid data points to plot.")

        plt.title(title, fontsize=14, fontweight='bold')
        plt.xlabel(x_label, fontsize=12)
        plt.ylabel(y_label, fontsize=12)
        
        # Save with high DPI
        output_path = self.output_dir / output_filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Scatter plot saved to: {output_path}")
        return str(output_path)

    def generate_correlation_heatmap(
        self,
        correlation_matrix: Union[np.ndarray, List[List[float]]],
        labels: List[str],
        title: str = "Correlation Matrix",
        output_filename: str = "correlation_heatmap.png",
        cmap: str = "coolwarm"
    ) -> str:
        """
        Generates a heatmap of a correlation matrix.
        
        Args:
            correlation_matrix: 2D array or list of lists representing the correlation matrix.
            labels: List of labels for the axes (must match matrix dimensions).
            title: Plot title.
            output_filename: Name of the output file.
            cmap: Matplotlib colormap string.
        
        Returns:
            Path to the generated figure file.
        """
        corr_matrix = np.array(correlation_matrix)
        
        if corr_matrix.shape[0] != corr_matrix.shape[1]:
            raise ValueError("Correlation matrix must be square.")
        
        if len(labels) != corr_matrix.shape[0]:
            raise ValueError("Number of labels must match matrix dimensions.")

        plt.figure(figsize=(10, 8))
        sns.heatmap(
            corr_matrix,
            annot=True,
            fmt=".2f",
            cmap=cmap,
            square=True,
            linewidths=.5,
            cbar_kws={"shrink": .5},
            xticklabels=labels,
            yticklabels=labels
        )
        plt.title(title, fontsize=14, fontweight='bold')
        
        output_path = self.output_dir / output_filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Heatmap saved to: {output_path}")
        return str(output_path)

    def generate_metric_distribution(
        self,
        data: List[float],
        metric_name: str,
        output_filename: str,
        bins: int = 20
    ) -> str:
        """
        Generates a histogram/KDE plot for a single metric distribution.
        
        Args:
            data: List of metric values.
            metric_name: Name of the metric for the title.
            output_filename: Output filename.
            bins: Number of histogram bins.
        
        Returns:
            Path to the generated figure file.
        """
        x = np.array(data)
        x_clean = x[~np.isnan(x)]
        
        if len(x_clean) == 0:
            logger.warning("No valid data for distribution plot.")
            return ""

        plt.figure(figsize=(10, 6))
        sns.histplot(x_clean, bins=bins, kde=True, color='skyblue', edgecolor='black')
        plt.title(f"Distribution of {metric_name}", fontsize=14, fontweight='bold')
        plt.xlabel(metric_name, fontsize=12)
        plt.ylabel("Frequency", fontsize=12)
        
        output_path = self.output_dir / output_filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Distribution plot saved to: {output_path}")
        return str(output_path)