"""
Visualization engine.
"""
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import List, Dict
from pathlib import Path
from .config import config
from .utils import get_logger

logger = get_logger(__name__)

class VisualizationEngine:
    """
    Generates plots and heatmaps.
    """
    def __init__(self):
        self.logger = logger
        self.figures_dir = config.figures_dir

    def plot_scatter(self, x: List[float], y: List[float], title: str, filename: str):
        """
        Generates a scatter plot with regression line.
        """
        plt.figure(figsize=(10, 6))
        sns.regplot(x=x, y=y)
        plt.title(title)
        plt.xlabel("Metric Value")
        plt.ylabel("Thermal Conductivity (W/mK)")
        plt.savefig(self.figures_dir / filename, dpi=300)
        plt.close()
        logger.info(f"Saved {filename}")

    def plot_heatmap(self, correlation_matrix: np.ndarray, labels: List[str], filename: str):
        """
        Generates a correlation heatmap.
        """
        plt.figure(figsize=(10, 8))
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', xticklabels=labels, yticklabels=labels)
        plt.title("Correlation Heatmap")
        plt.savefig(self.figures_dir / filename, dpi=300)
        plt.close()
        logger.info(f"Saved {filename}")
