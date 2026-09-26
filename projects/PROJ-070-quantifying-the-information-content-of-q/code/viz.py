import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats
from logging_config import logger
from typing import Optional, Dict, Any, List, Tuple
import os

def plot_scatter_with_regression(x: np.ndarray, y: np.ndarray, xlabel: str, ylabel: str, output_path: str):
    """
    Generate a scatter plot with a regression line and annotations.
    """
    sns.set(style="whitegrid")
    plt.figure(figsize=(10, 6))
    
    # Scatter
    plt.scatter(x, y, alpha=0.6, label='Data Points')
    
    # Regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    line_x = np.linspace(min(x), max(x), 100)
    line_y = slope * line_x + intercept
    plt.plot(line_x, line_y, 'r-', label=f'Regression (r={r_value:.3f})')
    
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(f'{ylabel} vs {xlabel}')
    plt.legend()
    
    # Save
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved plot to {output_path}")

def plot_null_model_comparison(
    physical_ent: np.ndarray,
    physical_ncd: np.ndarray,
    product_ent: np.ndarray,
    product_ncd: np.ndarray,
    haar_ent: np.ndarray,
    haar_ncd: np.ndarray,
    output_path: str
) -> None:
    """
    Plot null model clusters (Product States, Haar Random) alongside physical states
    in an Entanglement Entropy vs NCD complexity scatter plot.
    
    Parameters
    ----------
    physical_ent : np.ndarray
        Entanglement entropy values for physical states.
    physical_ncd : np.ndarray
        NCD complexity values for physical states.
    product_ent : np.ndarray
        Entanglement entropy values for random product states (null model 1).
    product_ncd : np.ndarray
        NCD complexity values for random product states.
    haar_ent : np.ndarray
        Entanglement entropy values for Haar-random states (null model 2).
    haar_ncd : np.ndarray
        NCD complexity values for Haar-random states.
    output_path : str
        Path to save the generated plot.
    """
    sns.set(style="whitegrid", context="talk")
    plt.figure(figsize=(12, 8))
    
    # Plot Physical States (Primary focus)
    plt.scatter(
        physical_ncd, physical_ent,
        c='blue', marker='o', s=80, alpha=0.7, edgecolors='black', linewidth=0.5,
        label='Physical States'
    )
    
    # Plot Product States (Low Entropy, High Complexity expected)
    plt.scatter(
        product_ncd, product_ent,
        c='green', marker='x', s=100, alpha=0.6,
        label='Product States (Null 1)'
    )
    
    # Plot Haar States (Max Entropy, Variable Complexity)
    plt.scatter(
        haar_ncd, haar_ent,
        c='red', marker='^', s=80, alpha=0.6,
        label='Haar Random (Null 2)'
    )
    
    # Regression line for physical states only
    if len(physical_ent) > 1:
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            physical_ncd, physical_ent
        )
        min_ncd, max_ncd = min(physical_ncd.min(), product_ncd.min(), haar_ncd.min()), \
                           max(physical_ncd.max(), product_ncd.max(), haar_ncd.max())
        line_x = np.linspace(min_ncd, max_ncd, 100)
        line_y = slope * line_x + intercept
        plt.plot(line_x, line_y, 'b--', linewidth=2, label=f'Physical Regression (r={r_value:.3f})')
    else:
        logger.warning("Insufficient physical data points for regression line.")
    
    plt.xlabel('Normalized Compression Distance (NCD)', fontsize=12)
    plt.ylabel('Entanglement Entropy', fontsize=12)
    plt.title('Entanglement vs Complexity: Physical States vs Null Models', fontsize=14)
    plt.legend(fontsize=10, loc='best')
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved null model comparison plot to {output_path}")

def generate_null_model_visualization(
    physical_data_path: str,
    product_data_path: str,
    haar_data_path: str,
    output_path: str
) -> None:
    """
    Load metrics from CSV files and generate the null model comparison plot.
    
    Expects CSVs with columns: ['entropy', 'ncd'] (or similar mapping).
    This function assumes the metrics have already been calculated and saved
    by T015/T016/T025.
    """
    import pandas as pd
    
    # Load Physical Data
    try:
        df_phys = pd.read_csv(physical_data_path)
        # Handle potential column name variations
        ent_col = 'entropy' if 'entropy' in df_phys.columns else df_phys.columns[0]
        ncd_col = 'ncd' if 'ncd' in df_phys.columns else df_phys.columns[1]
        p_ent = df_phys[ent_col].values
        p_ncd = df_phys[ncd_col].values
    except Exception as e:
        logger.error(f"Failed to load physical data from {physical_data_path}: {e}")
        raise

    # Load Product States Data
    try:
        df_prod = pd.read_csv(product_data_path)
        ent_col = 'entropy' if 'entropy' in df_prod.columns else df_prod.columns[0]
        ncd_col = 'ncd' if 'ncd' in df_prod.columns else df_prod.columns[1]
        pr_ent = df_prod[ent_col].values
        pr_ncd = df_prod[ncd_col].values
    except Exception as e:
        logger.error(f"Failed to load product state data from {product_data_path}: {e}")
        raise

    # Load Haar States Data
    try:
        df_haar = pd.read_csv(haar_data_path)
        ent_col = 'entropy' if 'entropy' in df_haar.columns else df_haar.columns[0]
        ncd_col = 'ncd' if 'ncd' in df_haar.columns else df_haar.columns[1]
        h_ent = df_haar[ent_col].values
        h_ncd = df_haar[ncd_col].values
    except Exception as e:
        logger.error(f"Failed to load Haar state data from {haar_data_path}: {e}")
        raise

    plot_null_model_comparison(
        p_ent, p_ncd,
        pr_ent, pr_ncd,
        h_ent, h_ncd,
        output_path
    )

if __name__ == "__main__":
    # Example usage for testing the visualization logic
    # This block assumes the existence of the CSV files generated by previous tasks.
    # In a real run, these paths would be passed via arguments or config.
    logger.info("Running viz.py self-test for null model visualization.")
    
    # Create dummy data for demonstration if files don't exist (for testing the plot function logic only)
    # In production, this should not be used; real data must be loaded.
    if not os.path.exists("data/processed/entanglement_metrics.csv"):
        logger.warning("No real data found. Generating dummy data for plot structure verification only.")
        p_ent = np.random.rand(20) * 2
        p_ncd = np.random.rand(20) * 0.5
        pr_ent = np.random.rand(20) * 0.1
        pr_ncd = np.random.rand(20) * 0.5 + 0.1
        h_ent = np.random.rand(20) * 2 + 1.5
        h_ncd = np.random.rand(20) * 0.5
    else:
        # Load real data if available
        df = pd.read_csv("data/processed/entanglement_metrics.csv")
        p_ent = df['entropy'].values
        p_ncd = df['ncd'].values
        # Dummy nulls for now if not generated
        pr_ent = p_ent * 0.1
        pr_ncd = p_ncd + 0.1
        h_ent = p_ent + 1.0
        h_ncd = p_ncd
    
    output = "figures/null_model_comparison.png"
    plot_null_model_comparison(p_ent, p_ncd, pr_ent, pr_ncd, h_ent, h_ncd, output)
    print(f"Plot saved to {output}")

# Re-import pandas inside the function to avoid top-level import if not needed for the function definition
import pandas as pd