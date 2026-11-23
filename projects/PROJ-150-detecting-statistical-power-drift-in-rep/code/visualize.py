import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_data(input_path):
    """Load the residuals dataset."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file {input_path} not found. Please ensure T011c has run successfully.")
    df = pd.read_csv(input_path)
    required_cols = ['year', 'power_residual']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Input file missing required columns: {missing}")
    return df

def plot_residuals_vs_year(df, output_path):
    """
    Generate a scatter plot of residual power vs. year with a regression line and confidence intervals.
    
    Args:
        df: DataFrame with 'year' and 'power_residual' columns
        output_path: Path to save the figure
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    plt.figure(figsize=(10, 6))
    
    # Set style
    sns.set_style("whitegrid")
    
    try:
        # Use regplot to automatically handle regression line and 95% CI
        # ci=95 adds the shaded confidence interval
        sns.regplot(
            x="year", 
            y="power_residual", 
            data=df, 
            ci=95, 
            scatter_kws={'alpha': 0.6, 's': 40},
            line_kws={'color': 'red', 'linewidth': 2}
        )
        
        plt.title("Residual Power vs. Year (95% Confidence Interval)", fontsize=14)
        plt.xlabel("Year", fontsize=12)
        plt.ylabel("Residual Power (Power Estimate - Predicted)", fontsize=12)
        
        # Save the figure
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        logger.info(f"Plot successfully saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Seaborn regplot with CI failed: {e}")
        raise
    finally:
        plt.close()

def main():
    """Main entry point for the visualization task."""
    input_path = "data/derived/residuals.csv"
    output_path = "results/power_drift_scatter.png"
    
    logger.info(f"Starting visualization task. Input: {input_path}, Output: {output_path}")
    
    try:
        # Load data
        df = load_data(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
        
        # Generate plot
        plot_residuals_vs_year(df, output_path)
        
        # Verify output exists and has size
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            if size > 0:
                logger.info(f"Verification passed: Output file exists with size {size} bytes.")
            else:
                logger.error("Verification failed: Output file is empty.")
                sys.exit(1)
        else:
            logger.error("Verification failed: Output file was not created.")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during visualization: {e}")
        raise

if __name__ == "__main__":
    main()