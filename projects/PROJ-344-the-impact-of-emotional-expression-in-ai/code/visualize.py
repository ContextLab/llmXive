import os
import sys
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

from typing import Optional, Tuple, List, Dict, Any
from logging_config import get_logger

def get_logger():
    return get_logger(__name__)

logger = get_logger()

def load_data(csv_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """Loads data from a CSV file.

    Args:
        csv_path: The path to the CSV file.

    Returns:
        A tuple containing the consistency scores (x-axis) and trust scores (y-axis).
    """
    try:
        df = pd.read_csv(csv_path)
        consistency = df['consistency_score'].to_numpy()
        trust = df['trust_score'].to_numpy()
        return consistency, trust
    except FileNotFoundError:
        logger.error(f"File not found: {csv_path}")
        raise
    except KeyError as e:
        logger.error(f"KeyError: {e}")
        raise

def compute_regression_with_ci(x: np.ndarray, y: np.ndarray) -> Tuple[np.poly1d, np.ndarray]:
    """Computes the regression line and confidence interval.

    Args:
        x: The consistency scores.
        y: The trust scores.

    Returns:
        A tuple containing the regression line (as a polynomial) and the confidence interval.
    """
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    y_predicted = p(x)
    residuals = y - y_predicted
    std_err = np.std(residuals)
    n = len(x)
    t = 2.576  # 95% confidence interval
    ci = std_err * t * np.sqrt(1 / n + (x - np.mean(x))**2 / np.sum((x - np.mean(x))**2))
    return p, ci

def check_wcag_contrast(color1: tuple, color2: tuple) -> bool:
    """Checks if the contrast ratio between two colors meets WCAG AA standards (>= 4.5:1)."""
    from PIL import Image
    def luminance(rgb):
        r, g, b = [int(c) for c in rgb]
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    l1 = luminance(color1)
    l2 = luminance(color2)
    if l1 > l2:
        contrast = (l1 + 0.05) / (l2 + 0.05)
    else:
        contrast = (l2 + 0.05) / (l1 + 0.05)
    return contrast >= 4.5

def validate_visualization_accessibility(ax: matplotlib.axes._axes.Axes) -> None:
    """Validates the accessibility of the visualization."""
    # Check contrast of axis labels
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label_color = label.get_color()
        bg_color = ax.get_facecolor()
        if not check_wcag_contrast(label_color, bg_color):
            raise ValueError(f"Contrast ratio between label color {label_color} and background color {bg_color} does not meet WCAG AA standards.")

    # Check font size of axis labels
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        font_size = label.get_fontsize()
        if font_size < 12:
            raise ValueError(f"Font size of axis label is too small: {font_size}")

def generate_scatter_plot(consistency: np.ndarray, trust: np.ndarray, regression_line: np.poly1d, ci: np.ndarray, output_path: str) -> None:
    """Generates a scatter plot with regression line and confidence interval."""
    plt.figure(figsize=(10, 6))
    plt.scatter(consistency, trust, label='Data Points')
    x = np.linspace(consistency.min(), consistency.max(), 100)
    y = regression_line(x)
    plt.plot(x, y, color='red', label='Regression Line')
    plt.fill_between(x, y - ci, y + ci, color='gray', alpha=0.2, label='95% Confidence Interval')
    plt.xlabel('Consistency Score')
    plt.ylabel('Trust Score')
    plt.title('Consistency vs. Trust (Associational Only)')
    plt.legend()
    plt.grid(True)
    try:
        validate_visualization_accessibility(plt.gca())
    except ValueError as e:
        logger.error(f"Accessibility validation failed: {e}")
        raise
    plt.savefig(output_path)
    plt.close()

def main(csv_path: str, output_path: str) -> None:
    """Main function to generate the scatter plot."""
    try:
        consistency, trust = load_data(csv_path)
        regression_line, ci = compute_regression_with_ci(consistency, trust)
        generate_scatter_plot(consistency, trust, regression_line, ci, output_path)
        logger.info(f"Scatter plot generated successfully at {output_path}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)