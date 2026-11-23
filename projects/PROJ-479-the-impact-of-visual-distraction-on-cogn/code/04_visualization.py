import os
import json
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, List, Tuple, Optional
from utils import get_logger, set_random_seed, get_global_seed

# Configure logging
logger = get_logger(__name__)

def load_statistics(filepath: str = "results/statistics/statistics.json") -> Dict[str, Any]:
    """Load the statistics JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Statistics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def load_analysis_data(filepath: str = "data/processed/final_analysis_data.csv") -> pd.DataFrame:
    """Load the final analysis dataset."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Analysis data file not found: {filepath}")
    return pd.read_csv(filepath)

def plot_significant_correlations(
    df: pd.DataFrame,
    stats: Dict[str, Any],
    output_dir: str = "results/plots",
    significance_threshold: float = 0.05
) -> List[str]:
    """
    Generate scatter plots with trend lines for significant correlations.
    
    Args:
        df: The analysis dataframe containing the raw data.
        stats: The statistics dictionary containing correlation results.
        output_dir: Directory to save plots.
        significance_threshold: P-value threshold for significance (default 0.05).
        
    Returns:
        List of paths to generated plot files.
    """
    os.makedirs(output_dir, exist_ok=True)
    generated_plots = []
    
    # Determine which metric pairs are significant
    significant_pairs = []
    if 'correlations' in stats:
        for pair_name, pair_data in stats['correlations'].items():
            p_val = pair_data.get('p_value', 1.0)
            if p_val < significance_threshold:
                significant_pairs.append((pair_name, pair_data))
    
    if not significant_pairs:
        logger.warning("No significant correlations found (p < 0.05). No plots generated.")
        return generated_plots
    
    # Set style
    sns.set(style="whitegrid")
    plt.rcParams['figure.figsize'] = (10, 8)
    plt.rcParams['font.size'] = 10
    
    for pair_name, pair_data in significant_pairs:
        try:
            # Parse pair name (e.g., "edge_density_vs_reaction_time")
            # Expected format: "predictor_vs_outcome"
            if "_vs_" in pair_name:
                predictor, outcome = pair_name.split("_vs_")
            else:
                # Fallback if format is different
                logger.warning(f"Unexpected pair name format: {pair_name}")
                continue
            
            # Check if columns exist in dataframe
            if predictor not in df.columns or outcome not in df.columns:
                logger.warning(f"Columns {predictor} or {outcome} not found in dataframe. Skipping.")
                continue
            
            # Filter out NaNs for this specific plot
            plot_df = df[[predictor, outcome]].dropna()
            
            if len(plot_df) == 0:
                logger.warning(f"No valid data points for {pair_name}. Skipping.")
                continue
            
            # Create the plot
            plt.figure()
            sns.scatterplot(x=predictor, y=outcome, data=plot_df, alpha=0.7, s=60, edgecolor='k')
            
            # Add trend line (linear regression)
            z = np.polyfit(plot_df[predictor].values, plot_df[outcome].values, 1)
            p = np.poly1d(z)
            x_line = np.linspace(plot_df[predictor].min(), plot_df[predictor].max(), 100)
            plt.plot(x_line, p(x_line), "r-", label=f"Trend Line (r={pair_data.get('r_value', 0):.3f})")
            
            # Add labels and title
            plt.title(f"Significant Correlation: {predictor} vs {outcome}\n(p = {pair_data.get('p_value', 0):.4f})")
            plt.xlabel(predictor.replace('_', ' ').title())
            plt.ylabel(outcome.replace('_', ' ').title())
            
            # Add legend
            plt.legend()
            
            # Save plot
            safe_name = pair_name.replace("vs", "vs_").replace(".", "_")
            filename = f"scatter_{safe_name}.png"
            filepath = os.path.join(output_dir, filename)
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            
            generated_plots.append(filepath)
            logger.info(f"Generated plot: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to generate plot for {pair_name}: {e}")
            continue
    
    return generated_plots

def plot_bootstrap_overlay(
    df: pd.DataFrame,
    stats: Dict[str, Any],
    bootstrap_results: Dict[str, Any],
    output_dir: str = "results/plots",
    n_bootstrap: int = 1000
) -> List[str]:
    """
    Generate scatter plots with bootstrap confidence intervals overlay.
    
    Args:
        df: The analysis dataframe.
        stats: The statistics dictionary.
        bootstrap_results: The bootstrap results dictionary.
        output_dir: Directory to save plots.
        n_bootstrap: Number of bootstrap iterations (for labeling).
        
    Returns:
        List of paths to generated plot files.
    """
    os.makedirs(output_dir, exist_ok=True)
    generated_plots = []
    
    if 'correlations' not in stats:
        return generated_plots
        
    sns.set(style="whitegrid")
    plt.rcParams['figure.figsize'] = (10, 8)
    
    for pair_name, pair_data in stats['correlations'].items():
        try:
            if "_vs_" in pair_name:
                predictor, outcome = pair_name.split("_vs_")
            else:
                continue
                
            if predictor not in df.columns or outcome not in df.columns:
                continue
                
            plot_df = df[[predictor, outcome]].dropna()
            if len(plot_df) == 0:
                continue
                
            plt.figure()
            sns.scatterplot(x=predictor, y=outcome, data=plot_df, alpha=0.6, s=50)
            
            # Add regression line with CI if bootstrap data exists
            # Note: This is a simplified visualization of the CI band
            # In a real scenario, we would plot the distribution of slopes/intercepts
            # For now, we plot the main trend and annotate with CI width
            z = np.polyfit(plot_df[predictor].values, plot_df[outcome].values, 1)
            p = np.poly1d(z)
            x_line = np.linspace(plot_df[predictor].min(), plot_df[predictor].max(), 100)
            plt.plot(x_line, p(x_line), "r-", label="Regression Fit")
            
            # Annotate with bootstrap info if available
            bootstrap_info = bootstrap_results.get(pair_name, {})
            ci_lower = bootstrap_info.get('ci_lower')
            ci_upper = bootstrap_info.get('ci_upper')
            
            if ci_lower is not None and ci_upper is not None:
                ci_width = ci_upper - ci_lower
                plt.figtext(0.15, 0.05, f"95% CI Width: {ci_width:.4f}\nBootstrap N={n_bootstrap}",
                            fontsize=9, bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.3))
            
            plt.title(f"Bootstrap Analysis: {predictor} vs {outcome}")
            plt.xlabel(predictor.replace('_', ' ').title())
            plt.ylabel(outcome.replace('_', ' ').title())
            plt.legend()
            
            safe_name = pair_name.replace("vs", "vs_").replace(".", "_")
            filename = f"bootstrap_{safe_name}.png"
            filepath = os.path.join(output_dir, filename)
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            
            generated_plots.append(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate bootstrap plot for {pair_name}: {e}")
            continue
    
    return generated_plots

def generate_visual_summary_report(
    plots: List[str],
    output_path: str = "results/plots/visual_summary.md"
) -> None:
    """
    Generate a markdown summary of all generated plots.
    """
    with open(output_path, 'w') as f:
        f.write("# Visual Analysis Summary\n\n")
        f.write(f"Total plots generated: {len(plots)}\n\n")
        f.write("## Generated Plots\n\n")
        for plot in plots:
            filename = os.path.basename(plot)
            f.write(f"- ![](plots/{filename})\n")
            f.write(f"  - **File**: `{filename}`\n\n")
    
    logger.info(f"Generated visual summary: {output_path}")

def main():
    """Main execution function for T038."""
    logger.info("Starting visualization pipeline (Task T038)...")
    
    # Set random seed for reproducibility
    set_random_seed()
    logger.info(f"Using random seed: {get_global_seed()}")
    
    try:
        # Load data
        logger.info("Loading analysis data...")
        df = load_analysis_data()
        logger.info(f"Loaded {len(df)} records.")
        
        logger.info("Loading statistics...")
        stats = load_statistics()
        logger.info(f"Loaded statistics for {len(stats.get('correlations', {}))} pairs.")
        
        # Load bootstrap results if available
        bootstrap_results = {}
        bootstrap_path = "results/sensitivity/bootstrap_results.json"
        if os.path.exists(bootstrap_path):
            with open(bootstrap_path, 'r') as f:
                bootstrap_results = json.load(f)
            logger.info("Loaded bootstrap results.")
        
        # Generate scatter plots for significant correlations
        logger.info("Generating scatter plots for significant correlations...")
        scatter_plots = plot_significant_correlations(df, stats)
        
        # Generate bootstrap overlay plots
        logger.info("Generating bootstrap overlay plots...")
        bootstrap_plots = plot_bootstrap_overlay(df, stats, bootstrap_results)
        
        # Generate summary report
        all_plots = scatter_plots + bootstrap_plots
        if all_plots:
            generate_visual_summary_report(all_plots)
        else:
            logger.warning("No plots were generated. Skipping summary report.")
        
        logger.info("Visualization pipeline completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Visualization pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()