"""
Plotting module for T033.
"""
import os
import logging
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
import sys
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.config import Config

def generate_scatter_plot(x: np.ndarray, y: np.ndarray, title: str, output_path: Path):
    """Generate a scatter plot."""
    plt.figure()
    plt.scatter(x, y)
    plt.title(title)
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.savefig(output_path)
    plt.close()

def generate_regression_line_plot(x: np.ndarray, y: np.ndarray, output_path: Path):
    """Generate regression line plot."""
    plt.figure()
    plt.scatter(x, y)
    # Simple linear regression
    m, b = np.polyfit(x, y, 1)
    plt.plot(x, m*x + b, 'r')
    plt.savefig(output_path)
    plt.close()

def generate_residual_plot(residuals: np.ndarray, output_path: Path):
    """Generate residual plot."""
    plt.figure()
    plt.hist(residuals)
    plt.title("Residuals")
    plt.savefig(output_path)
    plt.close()

def ensure_directories():
    """Ensure plot output directory exists."""
    config = Config()
    (config.REPORTS_PATH / "figures").mkdir(parents=True, exist_ok=True)

def run_analysis():
    """Main plotting routine."""
    ensure_directories()
    logging.info("Generating plots")

def main():
    run_analysis()

if __name__ == "__main__":
    main()
