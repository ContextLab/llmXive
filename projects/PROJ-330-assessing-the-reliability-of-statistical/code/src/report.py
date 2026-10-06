import os
import logging
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from src.config import PROJECT_ROOT, ensure_directories

# Configure matplotlib for non-interactive backend
matplotlib.use('Agg')

logger = logging.getLogger(__name__)

def generate_bland_altman_report(
    parametric_pvals: List[float],
    empirical_pvals: List[float],
    output_path: Optional[Union[str, Path]] = None
) -> str:
    """
    Generate a Bland-Altman plot comparing parametric vs empirical p-values.
    
    Args:
        parametric_pvals: List of parametric p-values
        empirical_pvals: List of empirical p-values
        output_path: Path to save the plot. If None, uses default path.
        
    Returns:
        Path to the generated plot file.
    """
    if output_path is None:
        output_path = PROJECT_ROOT / "artifacts" / "bland_altman.png"
    else:
        output_path = Path(output_path)
        
    ensure_directories(output_path)
    
    if len(parametric_pvals) == 0 or len(empirical_pvals) == 0:
        logger.warning("Empty p-value lists for Bland-Altman plot")
        return str(output_path)
        
    if len(parametric_pvals) != len(empirical_pvals):
        raise ValueError("Parametric and empirical p-value lists must be the same length")
        
    df = pd.DataFrame({
        'parametric': parametric_pvals,
        'empirical': empirical_pvals
    })
    
    # Filter out infinite or NaN values
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()
    
    if len(df) == 0:
        logger.warning("No valid data points for Bland-Altman plot after filtering")
        return str(output_path)
        
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Bland-Altman plot: difference vs mean
    mean_vals = (df['parametric'] + df['empirical']) / 2
    diff_vals = df['parametric'] - df['empirical']
    
    ax.scatter(mean_vals, diff_vals, alpha=0.6, s=20)
    
    # Add mean difference line
    mean_diff = diff_vals.mean()
    ax.axhline(mean_diff, color='red', linestyle='--', label=f'Mean diff: {mean_diff:.4f}')
    
    # Add 95% limits of agreement
    std_diff = diff_vals.std()
    loa_upper = mean_diff + 1.96 * std_diff
    loa_lower = mean_diff - 1.96 * std_diff
    ax.axhline(loo, color='green', linestyle=':', alpha=0.8, label=f'95% LoA: ±{1.96*std_diff:.4f}')
    ax.axhline(loo, color='green', linestyle=':', alpha=0.8)
    
    ax.set_xlabel('Mean of parametric and empirical p-values')
    ax.set_ylabel('Difference (parametric - empirical)')
    ax.set_title('Bland-Altman Plot: Parametric vs Empirical P-values')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"Bland-Altman plot saved to {output_path}")
    return str(output_path)

def generate_stability_report(
    stability_metrics: Dict[str, float],
    output_path: Optional[Union[str, Path]] = None
) -> str:
    """
    Generate a summary report of stability metrics.
    
    Args:
        stability_metrics: Dictionary of metric names to values
        output_path: Path to save the report. If None, uses default path.
        
    Returns:
        Path to the generated report file.
    """
    if output_path is None:
        output_path = PROJECT_ROOT / "artifacts" / "stability_report.csv"
    else:
        output_path = Path(output_path)
        
    ensure_directories(output_path)
    
    df = pd.DataFrame([stability_metrics])
    df.to_csv(output_path, index=False)
    
    logger.info(f"Stability report saved to {output_path}")
    return str(output_path)

def generate_cross_dataset_comparison(
    results: List[Dict[str, Union[str, float]]],
    output_path: Optional[Union[str, Path]] = None
) -> str:
    """
    Generate a comparative visualization of stability correlations across repositories.
    
    This function creates a bar chart comparing the stability correlation coefficients
    (Pearson r) of effect sizes across different genomic data repositories (GEO, TCGA, ENCODE).
    
    Args:
        results: List of dictionaries containing:
            - 'source': Repository name (e.g., 'GEO', 'TCGA', 'ENCODE')
            - 'stability_correlation': Pearson correlation coefficient
            - 'num_genes': Number of genes analyzed (optional)
            - 'num_samples': Number of samples (optional)
        output_path: Path to save the visualization. If None, uses default path.
        
    Returns:
        Path to the generated plot file.
    """
    if output_path is None:
        output_path = PROJECT_ROOT / "artifacts" / "cross_dataset_comparison.png"
    else:
        output_path = Path(output_path)
        
    ensure_directories(output_path)
    
    if not results:
        logger.warning("No results provided for cross-dataset comparison")
        # Create an empty plot to indicate no data
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Cross-Dataset Stability Comparison')
        plt.savefig(output_path, dpi=150)
        plt.close()
        return str(output_path)
    
    # Convert results to DataFrame
    df = pd.DataFrame(results)
    
    # Ensure required columns exist
    if 'source' not in df.columns or 'stability_correlation' not in df.columns:
        raise ValueError("Results must contain 'source' and 'stability_correlation' columns")
    
    # Sort by source for consistent ordering
    df = df.sort_values('source')
    
    # Create the bar chart
    fig, ax = plt.subplots(figsize=(12, 7))
    
    colors = {
        'GEO': '#3498db',
        'TCGA': '#e74c3c',
        'ENCODE': '#2ecc71'
    }
    
    bars = []
    for _, row in df.iterrows():
        source = row['source']
        corr = row['stability_correlation']
        color = colors.get(source, '#95a5a6')
        bar = ax.bar(source, corr, color=color, edgecolor='black', alpha=0.8)
        bars.extend(bar)
        
        # Add value label on top of bar
        ax.text(
            source, corr + 0.01,
            f'{corr:.3f}',
            ha='center', va='bottom', fontsize=11, fontweight='bold'
        )
    
    # Add horizontal line at r=0 for reference
    ax.axhline(0, color='black', linewidth=0.8, linestyle='-')
    
    # Add reference lines for correlation strength thresholds
    ax.axhline(0.3, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
    ax.axhline(0.5, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
    ax.axhline(0.7, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
    
    ax.set_ylabel('Stability Correlation (Pearson r)', fontsize=12)
    ax.set_xlabel('Data Repository', fontsize=12)
    ax.set_title('Cross-Dataset Comparison of Effect Size Stability', fontsize=14, fontweight='bold')
    ax.set_ylim(bottom=0, top=1.05)
    ax.grid(True, axis='y', alpha=0.3, linestyle='--')
    
    # Add legend explaining color coding
    legend_elements = []
    for source, color in colors.items():
        if source in df['source'].values:
            legend_elements.append(plt.Rectangle((0,0),1,1, color=color, label=source))
    
    if legend_elements:
        ax.legend(handles=legend_elements, title='Repository', loc='upper right')
    
    # Add annotation about correlation interpretation
    ax.text(
        0.02, 0.98,
        'Correlation Interpretation:\n'
        '• 0.3-0.5: Moderate stability\n'
        '• 0.5-0.7: Good stability\n'
        '• >0.7: High stability',
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Cross-dataset comparison visualization saved to {output_path}")
    return str(output_path)

def main():
    """
    Main function to demonstrate cross-dataset comparison visualization.
    This is intended to be called by the orchestration script.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Example usage with mock data (in production, this would come from actual analysis results)
    # In the actual pipeline, results would be aggregated from multiple datasets processed
    # by T029a (generate_cross_dataset_comparison logic)
    example_results = [
        {'source': 'GEO', 'stability_correlation': 0.65, 'num_genes': 20000, 'num_samples': 50},
        {'source': 'TCGA', 'stability_correlation': 0.72, 'num_genes': 18000, 'num_samples': 300},
        {'source': 'ENCODE', 'stability_correlation': 0.58, 'num_genes': 22000, 'num_samples': 80}
    ]
    
    output_path = generate_cross_dataset_comparison(example_results)
    print(f"Visualization generated at: {output_path}")

if __name__ == "__main__":
    main()
