import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Ensure project root is in path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config.environment import get_local_paths, ensure_directories

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_output_dir():
    """Ensure the paper/figures directory exists."""
    paths = get_local_paths()
    figures_dir = paths['figures_dir']
    ensure_directories([figures_dir])
    logger.info(f"Ensured output directory: {figures_dir}")
    return figures_dir

def load_processed_dataset():
    """Load the main processed dataset for the Rank-OLS fit plot."""
    paths = get_local_paths()
    dataset_path = paths['processed_dataset']
    logger.info(f"Loading processed dataset from {dataset_path}")
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Processed dataset not found at {dataset_path}. "
                                "Please ensure T020 (write_dataset) has completed successfully.")
    df = pd.read_csv(dataset_path)
    # Filter for samples with valid age and burden for the plot
    df = df.dropna(subset=['age', 'heteroplasmy_burden'])
    return df

def load_sensitivity_results():
    """Load sensitivity results for threshold sensitivity plot."""
    paths = get_local_paths()
    sensitivity_path = paths['sensitivity_results']
    logger.info(f"Loading sensitivity results from {sensitivity_path}")
    if not os.path.exists(sensitivity_path):
        raise FileNotFoundError(f"Sensitivity results not found at {sensitivity_path}. "
                                "Please ensure T032 (threshold sweep) has completed.")
    return pd.read_csv(sensitivity_path)

def load_subgroup_results():
    """Load subgroup results for subgroup comparison plot."""
    paths = get_local_paths()
    subgroup_path = paths['subgroup_results']
    logger.info(f"Loading subgroup results from {subgroup_path}")
    if not os.path.exists(subgroup_path):
        raise FileNotFoundError(f"Subgroup results not found at {subgroup_path}. "
                                "Please ensure T033 (subgroup analysis) has completed.")
    return pd.read_csv(subgroup_path)

def plot_linear_fit(df, output_path):
    """
    Generate the Rank-OLS fit plot.
    Shows the relationship between Age and Heteroplasmy Burden with the model fit.
    """
    logger.info("Generating Rank-OLS fit plot...")
    plt.figure(figsize=(8, 6))
    
    # Scatter plot of raw data
    sns.scatterplot(data=df, x='heteroplasmy_burden', y='age', alpha=0.5, label='Samples')
    
    # Calculate linear regression for visualization (on original scale for interpretability)
    # Note: The model was Rank-OLS, but we plot the trend on original values for clarity
    slope, intercept, r_value, p_value, std_err = stats.linregress(df['heteroplasmy_burden'], df['age'])
    x_line = np.linspace(df['heteroplasmy_burden'].min(), df['heteroplasmy_burden'].max(), 100)
    y_line = slope * x_line + intercept
    
    plt.plot(x_line, y_line, 'r-', linewidth=2, label=f'Trend (r={r_value:.2f}, p={p_value:.3f})')
    
    plt.xlabel('Heteroplasmy Burden (VAF ≥ 1%)')
    plt.ylabel('Age (Years)')
    plt.title('Correlation between Mitochondrial Heteroplasmy Burden and Age')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved Rank-OLS fit plot to {output_path}")

def plot_threshold_sensitivity(df, output_path):
    """
    Generate the threshold sensitivity plot.
    Shows how the correlation coefficient changes across VAF thresholds.
    """
    logger.info("Generating threshold sensitivity plot...")
    plt.figure(figsize=(8, 6))
    
    # Ensure threshold is numeric
    df['threshold'] = pd.to_numeric(df['threshold'], errors='coerce')
    df = df.dropna(subset=['threshold'])
    
    # Sort by threshold
    df = df.sort_values('threshold')
    
    plt.plot(df['threshold'], df['coefficient'], marker='o', linewidth=2, markersize=8, color='blue')
    
    # Add significance line if p-value is available
    if 'p_value' in df.columns:
        # Optional: add a second axis or annotation for p-values if needed
        # For now, we focus on the coefficient trend
        pass
    
    plt.xlabel('VAF Threshold (%)')
    plt.ylabel('Correlation Coefficient')
    plt.title('Sensitivity Analysis: Correlation vs. VAF Threshold')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved threshold sensitivity plot to {output_path}")

def plot_subgroup_comparison(df, output_path):
    """
    Generate the subgroup comparison plot.
    Shows correlation coefficients across different continental ancestries.
    """
    logger.info("Generating subgroup comparison plot...")
    plt.figure(figsize=(10, 6))
    
    # Sort for consistent plotting
    df = df.sort_values('ancestry')
    
    # Bar plot with error bars if standard error is available, otherwise just coefficient
    x_pos = range(len(df))
    plt.bar(x_pos, df['coefficient'], color='skyblue', edgecolor='black', alpha=0.8)
    
    # Add coefficient values on top of bars
    for i, v in enumerate(df['coefficient']):
        plt.text(i, v + (0.01 if v > 0 else -0.03), f'{v:.3f}', ha='center', va='bottom' if v > 0 else 'top', fontweight='bold')
    
    plt.xticks(x_pos, df['ancestry'], rotation=45, ha='right')
    plt.xlabel('Ancestry Group')
    plt.ylabel('Correlation Coefficient')
    plt.title('Subgroup Analysis: Correlation by Continental Ancestry')
    plt.axhline(0, color='red', linestyle='--', linewidth=1)
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved subgroup comparison plot to {output_path}")

def main():
    """Main entry point to generate all final figures."""
    logger.info("Starting final figure generation (T055)...")
    
    figures_dir = ensure_output_dir()
    
    try:
        # 1. Rank-OLS Fit
        df_main = load_processed_dataset()
        plot_linear_fit(df_main, os.path.join(figures_dir, 'rank_ols_fit.png'))
        
        # 2. Threshold Sensitivity
        df_sens = load_sensitivity_results()
        plot_threshold_sensitivity(df_sens, os.path.join(figures_dir, 'threshold_sensitivity.png'))
        
        # 3. Subgroup Comparison
        df_sub = load_subgroup_results()
        plot_subgroup_comparison(df_sub, os.path.join(figures_dir, 'subgroup_comparison.png'))
        
        logger.info("All final figures generated successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating figures: {e}")
        raise

if __name__ == "__main__":
    main()