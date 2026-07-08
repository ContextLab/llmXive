"""
Visualization module for generating plots and figures.
"""
import os
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional, List, Dict, Any

def load_processed_data_for_viz(data_path: str) -> pd.DataFrame:
    """
    Load processed data for visualization.

    Args:
        data_path: Path to the processed data CSV file.

    Returns:
        DataFrame containing the data.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Loading data for visualization from {data_path}")

    return pd.read_csv(data_path)

def generate_scatter_plot_with_regression(data: pd.DataFrame,
                                          x_col: str,
                                          y_col: str,
                                          output_path: str,
                                          title: str = 'MFN Amplitude vs Error Magnitude',
                                          electrodes: Optional[List[str]] = None) -> None:
    """
    Generate a scatter plot with regression line overlay.

    Args:
        data: DataFrame with the data.
        x_col: Column name for x-axis.
        y_col: Column name for y-axis.
        output_path: Path to save the plot.
        title: Plot title.
        electrodes: List of electrode columns to plot separately.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Generating scatter plot: {y_col} vs {x_col}")

    plt.figure(figsize=(10, 6))

    if electrodes:
        for electrode in electrodes:
            if electrode in data.columns:
                sns.regplot(data=data, x=x_col, y=electrode, label=electrode)
        plt.legend()
    else:
        sns.regplot(data=data, x=x_col, y=y_col)

    plt.xlabel(x_col.replace('_', ' ').title())
    plt.ylabel(y_col.replace('_', ' ').title())
    plt.title(title)
    plt.grid(True, alpha=0.3)

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Plot saved to {output_path}")

def generate_multi_electrode_comparison(data: pd.DataFrame,
                                        electrodes: List[str],
                                        x_col: str,
                                        output_path: str,
                                        title: str = 'Multi-Electrode Comparison') -> None:
    """
    Generate a comparison plot across multiple electrodes.

    Args:
        data: DataFrame with the data.
        electrodes: List of electrode column names.
        x_col: Column name for x-axis.
        output_path: Path to save the plot.
        title: Plot title.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Generating multi-electrode comparison for {electrodes}")

    fig, axes = plt.subplots(1, len(electrodes), figsize=(4 * len(electrodes), 4), sharey=True)

    if len(electrodes) == 1:
        axes = [axes]

    for i, electrode in enumerate(electrodes):
        if electrode in data.columns:
            sns.regplot(data=data, x=x_col, y=electrode, ax=axes[i])
            axes[i].set_title(electrode)
            axes[i].set_xlabel(x_col.replace('_', ' ').title())
            axes[i].set_ylabel('MFN Amplitude (µV)')
            axes[i].grid(True, alpha=0.3)

    plt.suptitle(title)
    plt.tight_layout()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Multi-electrode plot saved to {output_path}")

def generate_sensitivity_analysis_plot(sensitivity_results: pd.DataFrame,
                                       output_path: str,
                                       title: str = 'Sensitivity Analysis: Threshold vs Significance') -> None:
    """
    Generate a sensitivity analysis summary plot showing threshold vs correlation/p-value.

    Args:
        sensitivity_results: DataFrame containing sensitivity sweep results.
        output_path: Path to save the plot.
        title: Plot title.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Generating sensitivity analysis plot")

    # Ensure required columns exist
    required_cols = ['threshold', 'correlation', 'p_value']
    if not all(col in sensitivity_results.columns for col in required_cols):
        raise ValueError(f"Sensitivity results must contain columns: {required_cols}")

    # Create figure with two subplots
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Plot 1: Threshold vs Correlation
    ax1 = axes[0]
    ax1.plot(sensitivity_results['threshold'], sensitivity_results['correlation'], 
             marker='o', linestyle='-', color='blue', linewidth=2, markersize=8)
    ax1.fill_between(sensitivity_results['threshold'], sensitivity_results['correlation'], 
                     alpha=0.3, color='blue')
    ax1.set_xlabel('Error Magnitude Threshold (degrees)')
    ax1.set_ylabel('Correlation Coefficient')
    ax1.set_title('Correlation vs Threshold')
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='r', linestyle='--', alpha=0.5, label='Zero correlation')
    ax1.legend()

    # Plot 2: Threshold vs P-value
    ax2 = axes[1]
    ax2.plot(sensitivity_results['threshold'], sensitivity_results['p_value'], 
             marker='s', linestyle='-', color='green', linewidth=2, markersize=8)
    ax2.fill_between(sensitivity_results['threshold'], sensitivity_results['p_value'], 
                     alpha=0.3, color='green')
    ax2.set_xlabel('Error Magnitude Threshold (degrees)')
    ax2.set_ylabel('P-value')
    ax2.set_title('P-value vs Threshold')
    ax2.grid(True, alpha=0.3)
    
    # Add significance threshold line (alpha = 0.05)
    ax2.axhline(y=0.05, color='r', linestyle='--', alpha=0.7, label='α = 0.05')
    ax2.legend()

    plt.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Sensitivity analysis plot saved to {output_path}")

def generate_sensitivity_summary_table(sensitivity_results: pd.DataFrame,
                                       output_path: str) -> None:
    """
    Generate a summary table of sensitivity analysis results.

    Args:
        sensitivity_results: DataFrame containing sensitivity sweep results.
        output_path: Path to save the table (CSV format).
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Generating sensitivity analysis summary table")

    # Ensure required columns exist
    required_cols = ['threshold', 'correlation', 'p_value']
    if not all(col in sensitivity_results.columns for col in required_cols):
        raise ValueError(f"Sensitivity results must contain columns: {required_cols}")

    # Add significance flag
    sensitivity_summary = sensitivity_results.copy()
    sensitivity_summary['significant'] = sensitivity_summary['p_value'] < 0.05
    sensitivity_summary['correlation_strength'] = sensitivity_summary['correlation'].apply(
        lambda x: 'strong' if abs(x) > 0.5 else 'moderate' if abs(x) > 0.3 else 'weak'
    )

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    sensitivity_summary.to_csv(output_path, index=False)
    
    logger.info(f"Sensitivity summary table saved to {output_path}")

def main():
    """
    Main function to run visualization pipeline.
    """
    import argparse
    parser = argparse.ArgumentParser(description='Generate visualization plots')
    parser.add_argument('--data', type=str, required=True, help='Path to processed data')
    parser.add_argument('--sensitivity-data', type=str, 
                        help='Path to sensitivity analysis results CSV')
    parser.add_argument('--output', type=str, required=True, help='Path to output directory')
    parser.add_argument('--electrodes', type=str, nargs='+', default=['FCz', 'Cz', 'Fz'],
                        help='List of electrodes to plot')

    args = parser.parse_args()

    # Load main data
    data = load_processed_data_for_viz(args.data)

    # Generate scatter plot
    scatter_path = f"{args.output}/scatter_mfn_vs_error.png"
    generate_scatter_plot_with_regression(
        data,
        x_col='error_magnitude',
        y_col='MFN_amplitude_FCz',
        output_path=scatter_path,
        electrodes=args.electrodes
    )

    # Generate multi-electrode comparison
    multi_path = f"{args.output}/multi_electrode_comparison.png"
    generate_multi_electrode_comparison(
        data,
        electrodes=args.electrodes,
        x_col='error_magnitude',
        output_path=multi_path
    )

    # Generate sensitivity analysis if data provided
    if args.sensitivity_data:
        sensitivity_results = pd.read_csv(args.sensitivity_data)
        
        # Generate sensitivity plot
        sens_plot_path = f"{args.output}/sensitivity_analysis_plot.png"
        generate_sensitivity_analysis_plot(
            sensitivity_results,
            output_path=sens_plot_path,
            title='Sensitivity Analysis: Error Threshold Robustness'
        )
        
        # Generate sensitivity table
        sens_table_path = f"{args.output}/sensitivity_summary.csv"
        generate_sensitivity_summary_table(
            sensitivity_results,
            output_path=sens_table_path
        )
        print(f"Sensitivity analysis outputs saved to {args.output}")

    print(f"Visualization complete. Plots saved to {args.output}")

if __name__ == '__main__':
    main()