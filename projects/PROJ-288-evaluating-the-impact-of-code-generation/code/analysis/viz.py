import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import pandas as pd

# Import local project utilities
from data.logging_config import get_logger

logger = get_logger(__name__)

# Constants for paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "docs" / "reports"
ANALYSIS_RESULTS_PATH = DATA_DIR / "analysis_results.json"
PROCESSED_DATA_PATH = DATA_DIR / "processed" / "pr_data_filtered.csv"

def load_analysis_results() -> Dict[str, Any]:
    """Load the analysis results from the JSON file."""
    if not ANALYSIS_RESULTS_PATH.exists():
        raise FileNotFoundError(f"Analysis results not found at {ANALYSIS_RESULTS_PATH}")
    
    with open(ANALYSIS_RESULTS_PATH, 'r') as f:
        return json.load(f)

def load_processed_data() -> pd.DataFrame:
    """Load the filtered processed PR data."""
    if not PROCESSED_DATA_PATH.exists():
        raise FileNotFoundError(f"Processed data not found at {PROCESSED_DATA_PATH}")
    
    return pd.read_csv(PROCESSED_DATA_PATH)

def generate_residuals_plot() -> str:
    """
    Generate residual plots (residuals vs. predicted) to check model assumptions.
    Saves the plot to docs/reports/residuals.png.
    
    Returns:
        str: Path to the saved plot file.
    """
    logger.info("Generating residual plots...")
    
    # Ensure output directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load analysis results to extract residuals and predicted values
    results = load_analysis_results()
    
    if 'lmer' not in results:
        raise ValueError("No LMER results found in analysis_results.json. "
                       "Please ensure T024 has been executed successfully.")
    
    lmer_results = results['lmer']
    
    # Check if residuals are available in the results
    if 'residuals' not in lmer_results or 'fitted_values' not in lmer_results:
        # If residuals are not stored, we need to recalculate them from raw data
        logger.warning("Residuals not found in results. Attempting to recalculate from raw data...")
        
        # Load raw data
        df = load_processed_data()
        
        # We need to reconstruct the model to get residuals
        # This is a simplified approach - in a real scenario, we'd store the fitted model
        if 'coefficients' not in lmer_results:
            raise ValueError("Cannot recalculate residuals: model coefficients not found.")
        
        coeffs = lmer_results['coefficients']
        
        # Extract coefficients
        intercept = coeffs.get('Intercept', 0)
        origin_disclosing = coeffs.get('origin_labelDisclosing', 0)
        code_lines_changed = coeffs.get('code_lines_changed', 0)
        reviewer_count = coeffs.get('reviewer_count', 0)
        
        # Calculate fitted values and residuals
        df['fitted'] = (intercept + 
                       df['origin_label'].map({'Disclosing': 1, 'Non-Disclosing': 0}) * origin_disclosing +
                       df['code_lines_changed'] * code_lines_changed +
                       df['reviewer_count'] * reviewer_count)
        
        df['residuals'] = df['median_time'] - df['fitted']
        
        predicted = df['fitted'].values
        residuals = df['residuals'].values
    else:
        # Use stored residuals and fitted values
        predicted = np.array(lmer_results['fitted_values'])
        residuals = np.array(lmer_results['residuals'])
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    sns.set_style("whitegrid")
    
    # Scatter plot of residuals vs. predicted
    plt.scatter(predicted, residuals, alpha=0.6, edgecolors='w', linewidth=0.5, s=50)
    
    # Add horizontal line at y=0
    plt.axhline(y=0, color='red', linestyle='--', linewidth=2, label='Zero residual line')
    
    # Add regression line to check for patterns
    if len(predicted) > 1:
        z = np.polyfit(predicted, residuals, 1)
        p = np.poly1d(z)
        plt.plot(predicted, p(predicted), "b--", alpha=0.8, linewidth=2, label=f'Trend line (slope={z[0]:.4f})')
    
    # Calculate and display R-squared for the residual trend
    if len(predicted) > 1:
        correlation = np.corrcoef(predicted, residuals)[0, 1]
        r_squared = correlation ** 2
        plt.text(0.05, 0.95, f'R² of residuals vs. fitted: {r_squared:.4f}', 
                transform=plt.gca().transAxes, fontsize=12, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.xlabel('Fitted Values (Predicted Review Time)', fontsize=12)
    plt.ylabel('Residuals (Observed - Predicted)', fontsize=12)
    plt.title('Residuals vs. Fitted Values\n(Check for Homoscedasticity and Linearity)', fontsize=14)
    plt.legend(loc='best')
    
    # Add grid for better readability
    plt.grid(True, alpha=0.3)
    
    # Save the plot
    output_path = REPORTS_DIR / "residuals.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Residual plot saved to {output_path}")
    return str(output_path)

def generate_scatter_size_vs_time() -> str:
    """
    Generate scatter plot of code size vs. review time with separate regression lines.
    """
    logger.info("Generating scatter plot of code size vs. review time...")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    df = load_processed_data()
    
    plt.figure(figsize=(12, 8))
    sns.set_style("whitegrid")
    
    # Create scatter plot with regression lines per group
    sns.lmplot(data=df, x='code_lines_changed', y='median_time', 
              hue='origin_label', height=8, aspect=1.5, 
              scatter_kws={'alpha': 0.6, 's': 50}, line_kws={'linewidth': 2})
    
    plt.title('Code Size vs. Review Time by Origin Label', fontsize=14)
    plt.xlabel('Code Lines Changed', fontsize=12)
    plt.ylabel('Median Review Time (minutes)', fontsize=12)
    
    output_path = REPORTS_DIR / "scatter_size_vs_time.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Scatter plot saved to {output_path}")
    return str(output_path)

def generate_boxplot_review_time() -> str:
    """
    Generate boxplot comparing review time distributions (Disclosing vs Non-Disclosing).
    """
    logger.info("Generating boxplot of review time distributions...")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    df = load_processed_data()
    
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    
    # Create boxplot
    sns.boxplot(data=df, x='origin_label', y='median_time', palette="Set2")
    
    # Add median lines
    for i, group in enumerate(df['origin_label'].unique()):
        median = df[df['origin_label'] == group]['median_time'].median()
        plt.plot([i, i], [median, median], 'r--', linewidth=2, label='Median' if i == 0 else "")
    
    plt.title('Review Time Distribution by Origin Label', fontsize=14)
    plt.xlabel('Origin Label', fontsize=12)
    plt.ylabel('Median Review Time (minutes)', fontsize=12)
    
    output_path = REPORTS_DIR / "boxplot_review_time.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Boxplot saved to {output_path}")
    return str(output_path)

def main():
    """Main entry point for visualization generation."""
    logger.info("Starting visualization generation...")
    
    try:
        # Generate all required plots
        residuals_path = generate_residuals_plot()
        scatter_path = generate_scatter_size_vs_time()
        boxplot_path = generate_boxplot_review_time()
        
        logger.info("All visualizations generated successfully:")
        logger.info(f"  - Residuals plot: {residuals_path}")
        logger.info(f"  - Scatter plot: {scatter_path}")
        logger.info(f"  - Boxplot: {boxplot_path}")
        
        return 0
    except Exception as e:
        logger.error(f"Error generating visualizations: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())