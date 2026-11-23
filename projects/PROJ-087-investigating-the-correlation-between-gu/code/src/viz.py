import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from src.config import load_config

logger = logging.getLogger(__name__)

def generate_placeholder_no_associations(output_path: Path) -> None:
    """
    Generate a placeholder plot when no significant associations are found.
    
    This satisfies FR-006 edge case handling by ensuring a valid image file
    is produced even when the analysis yields no significant correlations.
    
    Args:
        output_path: Path where the placeholder image will be saved.
    """
    logger.info(f"Generating placeholder plot for 'No significant associations' at {output_path}")
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Style the plot
    sns.set_style("whitegrid")
    ax.set_facecolor("#f8f9fa")
    
    # Add a clear message
    ax.text(
        0.5, 0.5,
        "No Significant Associations Found",
        transform=ax.transAxes,
        fontsize=24,
        fontweight='bold',
        ha='center',
        va='center',
        color='#2c3e50'
    )
    
    ax.text(
        0.5, 0.4,
        "After Benjamini-Hochberg correction (q < 0.05)",
        transform=ax.transAxes,
        fontsize=14,
        ha='center',
        va='center',
        color='#7f8c8d'
    )
    
    ax.text(
        0.5, 0.25,
        "All correlations between alpha-diversity indices",
        transform=ax.transAxes,
        fontsize=12,
        ha='center',
        va='center',
        color='#95a5a6'
    )
    
    ax.text(
        0.5, 0.15,
        "and sleep metrics were not statistically significant.",
        transform=ax.transAxes,
        fontsize=12,
        ha='center',
        va='center',
        color='#95a5a6'
    )
    
    # Remove axes
    ax.axis('off')
    
    # Add a subtle border
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Save the figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    
    logger.info(f"Placeholder plot successfully saved to {output_path}")

def generate_boxplot_by_quartile(
    diversity_df: pd.DataFrame,
    sleep_df: pd.DataFrame,
    diversity_index: str,
    sleep_metric: str,
    output_path: Path
) -> None:
    """
    Generate a boxplot of alpha-diversity by sleep quartile.
    
    Args:
        diversity_df: DataFrame containing diversity indices (sample_id, shannon, simpson, observed_otus).
        sleep_df: DataFrame containing sleep metrics (sample_id, sleep_efficiency, sleep_duration_hours).
        diversity_index: Name of the diversity column to plot (e.g., 'shannon').
        sleep_metric: Name of the sleep metric to use for quartiles (e.g., 'sleep_efficiency').
        output_path: Path to save the generated plot.
    """
    logger.info(f"Generating boxplot for {diversity_index} by {sleep_metric} quartile")
    
    # Merge data
    merged = pd.merge(diversity_df, sleep_df, on='sample_id', how='inner')
    
    if merged.empty:
        logger.warning("No data available to generate boxplot. Merged dataset is empty.")
        return
    
    # Create quartiles
    merged['sleep_quartile'] = pd.qcut(merged[sleep_metric], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.set_style("whitegrid")
    
    # Generate boxplot
    sns.boxplot(
        x='sleep_quartile',
        y=diversity_index,
        data=merged,
        ax=ax,
        palette="viridis",
        order=['Q1', 'Q2', 'Q3', 'Q4']
    )
    
    # Labels and title
    ax.set_xlabel(f'{sleep_metric} Quartile', fontsize=12)
    ax.set_ylabel(f'{diversity_index.capitalize()} Index', fontsize=12)
    ax.set_title(f'{diversity_index.capitalize()} Diversity by {sleep_metric.replace("_", " ").title()} Quartile', fontsize=14)
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Boxplot saved to {output_path}")

def generate_all_quartile_boxplots(
    diversity_df: pd.DataFrame,
    sleep_df: pd.DataFrame,
    output_dir: Path
) -> List[Path]:
    """
    Generate boxplots for all diversity indices against all sleep metrics.
    
    Args:
        diversity_df: DataFrame with diversity indices.
        sleep_df: DataFrame with sleep metrics.
        output_dir: Directory to save generated plots.
        
    Returns:
        List of paths to generated plot files.
    """
    diversity_indices = ['shannon', 'simpson', 'observed_otus']
    sleep_metrics = ['sleep_efficiency', 'sleep_duration_hours']
    generated_paths = []
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for div_idx in diversity_indices:
        for sleep_met in sleep_metrics:
            output_path = output_dir / f"boxplot_{div_idx}_{sleep_met}_quartile.png"
            generate_boxplot_by_quartile(diversity_df, sleep_df, div_idx, sleep_met, output_path)
            generated_paths.append(output_path)
    
    return generated_paths

def save_all_plot_artifacts(
    correlation_results: pd.DataFrame,
    diversity_df: pd.DataFrame,
    sleep_df: pd.DataFrame,
    plots_dir: Path
) -> List[Path]:
    """
    Save all plot artifacts based on correlation results.
    
    If no significant associations are found, generates a placeholder plot.
    Otherwise, generates scatterplots and boxplots for significant correlations.
    
    Args:
        correlation_results: DataFrame with correlation results (including is_significant flag).
        diversity_df: DataFrame with diversity indices.
        sleep_df: DataFrame with sleep metrics.
        plots_dir: Directory to save plot artifacts.
        
    Returns:
        List of paths to saved plot files.
    """
    plots_dir.mkdir(parents=True, exist_ok=True)
    saved_paths = []
    
    # Check for significant associations
    significant_corrs = correlation_results[
        (correlation_results['is_significant'] == True) & 
        (correlation_results['status'] == 'success')
    ]
    
    if significant_corrs.empty:
        logger.info("No significant associations found. Generating placeholder plot.")
        placeholder_path = plots_dir / "placeholder_no_associations.png"
        generate_placeholder_no_associations(placeholder_path)
        saved_paths.append(placeholder_path)
    else:
        logger.info(f"Found {len(significant_corrs)} significant associations. Generating plots.")
        
        # Generate boxplots for all combinations (as per T028 requirement)
        boxplot_paths = generate_all_quartile_boxplots(diversity_df, sleep_df, plots_dir)
        saved_paths.extend(boxplot_paths)
        
        # Generate scatterplots for significant correlations
        for _, row in significant_corrs.iterrows():
            div_idx = row['diversity_index']
            sleep_met = row['sleep_metric']
            
            scatter_path = plots_dir / f"scatterplot_{div_idx}_{sleep_met}.png"
            
            # Merge data for scatterplot
            merged = pd.merge(diversity_df, sleep_df, on='sample_id', how='inner')
            
            if merged.empty:
                logger.warning(f"Skipping scatterplot for {div_idx} vs {sleep_met}: no data.")
                continue
            
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.set_style("whitegrid")
            
            # Scatter plot
            sns.scatterplot(
                x=sleep_met,
                y=div_idx,
                data=merged,
                alpha=0.6,
                ax=ax,
                color="#3498db"
            )
            
            # Regression line
            sns.regplot(
                x=sleep_met,
                y=div_idx,
                data=merged,
                scatter=False,
                ax=ax,
                color="#e74c3c",
                line_kws={"linestyle": "--"}
            )
            
            # Labels
            r_val = row['r']
            q_val = row['q']
            ax.set_xlabel(sleep_met.replace('_', ' ').title(), fontsize=12)
            ax.set_ylabel(div_idx.replace('_', ' ').title(), fontsize=12)
            ax.set_title(
                f'{div_idx.replace("_", " ").title()} vs {sleep_met.replace("_", " ").title()}\n'
                f'r = {r_val:.3f}, q = {q_val:.3f}',
                fontsize=14
            )
            
            plt.tight_layout()
            plt.savefig(scatter_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            saved_paths.append(scatter_path)
            logger.info(f"Saved scatterplot to {scatter_path}")
    
    return saved_paths

def main():
    """
    Main entry point for visualization tasks.
    This function is intended to be called by the run-book or orchestrator.
    """
    config = load_config()
    plots_dir = Path(config.get('DATA_PROCESSED_DIR', 'data/processed/plots'))
    
    # Load data
    diversity_path = Path(config.get('DATA_PROCESSED_DIR', 'data/processed')) / 'diversity_results.csv'
    correlation_path = Path(config.get('DATA_PROCESSED_DIR', 'data/processed')) / 'correlation_results.csv'
    sleep_path = Path(config.get('DATA_PROCESSED_DIR', 'data/processed')) / 'cleaned_microbiome_sleep.csv'
    
    if not diversity_path.exists() or not correlation_path.exists() or not sleep_path.exists():
        logger.error("Required data files not found. Cannot generate plots.")
        return
    
    diversity_df = pd.read_csv(diversity_path)
    correlation_results = pd.read_csv(correlation_path)
    sleep_df = pd.read_csv(sleep_path)
    
    # Save artifacts
    saved = save_all_plot_artifacts(correlation_results, diversity_df, sleep_df, plots_dir)
    logger.info(f"Total plots saved: {len(saved)}")

if __name__ == "__main__":
    main()