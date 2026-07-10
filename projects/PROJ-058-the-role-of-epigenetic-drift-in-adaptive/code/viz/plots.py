import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server/headless execution
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from config import get_env, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_variance_matrix() -> pd.DataFrame:
    """
    Load the unified variance matrix from data/processed/variance_matrix.csv.
    
    Returns:
        pd.DataFrame: The variance matrix with columns for epigenetic variance,
                      expression variance, condition, and other metadata.
    """
    matrix_path = Path(get_env("VARIANCE_MATRIX_PATH", "data/processed/variance_matrix.csv"))
    
    if not matrix_path.exists():
        raise FileNotFoundError(
            f"Variance matrix not found at {matrix_path}. "
            "Run the preprocessing pipeline (T019) first."
        )
    
    logger.info(f"Loading variance matrix from {matrix_path}")
    df = pd.read_csv(matrix_path)
    
    # Validate required columns
    required_cols = ['gene_epigenetic_variance', 'gene_expression_variance', 'condition']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Variance matrix missing required columns: {missing_cols}. "
            f"Found columns: {list(df.columns)}"
        )
    
    return df

def filter_by_condition(df: pd.DataFrame, conditions: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Filter the variance matrix by specific conditions.
    
    Args:
        df: The variance matrix DataFrame.
        conditions: List of condition strings to filter by. If None, returns all.
        
    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    if conditions is None:
        return df
    
    valid_conditions = set(df['condition'].unique())
    invalid_conditions = set(conditions) - valid_conditions
    if invalid_conditions:
        logger.warning(f"Requested conditions not found in data: {invalid_conditions}")
    
    return df[df['condition'].isin(conditions)]

def create_scatter_plot(
    df: pd.DataFrame,
    output_path: Path,
    title: str = "Epigenetic vs Expression Variance by Condition",
    xlabel: str = "Epigenetic Variance (LOGO)",
    ylabel: str = "Expression Variance (LOGO)",
    color_map: Optional[Dict[str, str]] = None
) -> str:
    """
    Generate a scatter plot of epigenetic variance vs expression variance,
    colored by condition.
    
    Args:
        df: The variance matrix DataFrame.
        output_path: Path where the plot will be saved.
        title: Plot title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        color_map: Optional mapping of condition names to colors.
        
    Returns:
        str: The path to the saved plot file.
    """
    if df.empty:
        raise ValueError("Cannot create plot: input DataFrame is empty.")
    
    # Ensure output directory exists
    ensure_directories()
    
    plt.figure(figsize=(10, 8))
    
    # Define default color palette if none provided
    if color_map is None:
        unique_conditions = df['condition'].unique()
        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_conditions)))
        color_map = {cond: colors[i] for i, cond in enumerate(unique_conditions)}
    
    # Plot each condition separately to get a legend
    for condition in df['condition'].unique():
        subset = df[df['condition'] == condition]
        color = color_map.get(condition, 'gray')
        
        plt.scatter(
            subset['gene_epigenetic_variance'],
            subset['gene_expression_variance'],
            label=condition,
            alpha=0.6,
            edgecolors='w',
            s=50,
            color=color
        )
    
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend(title='Condition')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Set tight layout to prevent label cutoff
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Scatter plot saved to {output_path}")
    return str(output_path)

def run_viz_analysis(
    matrix_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    conditions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Main function to run the visualization analysis.
    
    Args:
        matrix_path: Optional override for variance matrix path.
        output_dir: Optional override for output directory.
        conditions: Optional list of conditions to include.
        
    Returns:
        Dict containing paths to generated plots and summary stats.
    """
    # Load data
    df = load_variance_matrix()
    
    if conditions:
        df = filter_by_condition(df, conditions)
    
    # Prepare output paths
    if output_dir:
        out_dir = Path(output_dir)
    else:
        out_dir = Path(get_env("OUTPUT_FIGURES_DIR", "output/figures"))
    
    ensure_directories()
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate plot
    plot_path = out_dir / "variance_scatter_by_condition.png"
    create_scatter_plot(df, plot_path)
    
    # Generate summary stats for the report
    stats = {
        "total_genes": len(df),
        "conditions_included": list(df['condition'].unique()),
        "plot_path": str(plot_path),
        "mean_epigenetic_variance": float(df['gene_epigenetic_variance'].mean()),
        "mean_expression_variance": float(df['gene_expression_variance'].mean()),
        "std_epigenetic_variance": float(df['gene_epigenetic_variance'].std()),
        "std_expression_variance": float(df['gene_expression_variance'].std())
    }
    
    logger.info(f"Visualization analysis complete. Stats: {stats}")
    return stats

def main():
    """
    Entry point for the visualization script.
    Reads configuration from environment variables or defaults.
    """
    logger.info("Starting visualization analysis (T025)")
    
    try:
        # Get optional overrides from environment
        matrix_path = get_env("VARIANCE_MATRIX_PATH")
        output_dir = get_env("OUTPUT_FIGURES_DIR")
        
        # Get conditions to filter (comma-separated string or None)
        conditions_str = get_env("VIZ_CONDITIONS", None)
        conditions = None
        if conditions_str:
            conditions = [c.strip() for c in conditions_str.split(',')]
        
        results = run_viz_analysis(
            matrix_path=matrix_path,
            output_dir=output_dir,
            conditions=conditions
        )
        
        # Write summary to JSON for downstream tasks
        summary_path = Path(get_env("OUTPUT_DIR", "output")) / "viz_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Viz summary written to {summary_path}")
        print(f"SUCCESS: Visualization generated at {results['plot_path']}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid data configuration: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during visualization: {e}")
        print(f"ERROR: Unexpected failure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
