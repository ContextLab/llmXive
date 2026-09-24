"""
code/08_visualize.py

Reconciles run-book vs implementation for the visualization step.
Generates diagnostic plots and summary statistics for the top ranked CREs
to support IGV visualization validation and quality control.

This script is invoked by the run-book (quickstart.md) to produce:
1. `results/visualization_summary.png`: A composite plot showing:
   - Correlation between log2FC and weighted delta signal.
   - Distribution of VIF scores.
   - Heatmap of top CRE signals across conditions.
2. `results/top_cre_coordinates.tsv`: Coordinates of the top N CREs for track generation.

Dependencies:
- data/processed/weights.tsv (Output of T013c)
- results/CRE_ranked_<stress>.md (Output of T018)
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"

# Ensure output directories exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def load_weights(path: Path) -> pd.DataFrame:
    """Load the weights TSV file."""
    logger.info(f"Loading weights from {path}")
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    
    df = pd.read_csv(path, sep='\t')
    required_cols = ['cre_id', 'gene_id', 'weighted_delta_peak_signal', 'weight_source']
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in {path}: {missing}")
    return df


def load_ranked_report(path: Path) -> pd.DataFrame:
    """
    Load the ranked CRE report (Markdown).
    Expects a standard markdown table format.
    """
    logger.info(f"Loading ranked report from {path}")
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    
    # Read the file and find the table
    with open(path, 'r') as f:
        lines = f.readlines()
    
    # Find the header line (starts with |)
    header_idx = None
    data_start_idx = None
    for i, line in enumerate(lines):
        if line.startswith('|') and 'cre_id' in line.lower():
            header_idx = i
        if header_idx is not None and i > header_idx and line.startswith('|'):
            data_start_idx = i
            break
    
    if header_idx is None or data_start_idx is None:
        raise ValueError(f"Could not parse markdown table in {path}")
    
    # Extract table lines
    table_lines = [line.strip() for line in lines[data_start_idx:] if line.strip().startswith('|')]
    
    # Parse into DataFrame
    data = []
    for line in table_lines:
        # Remove pipe characters and split
        parts = [p.strip() for p in line.split('|')[1:-1]]
        if len(parts) >= 5: # Ensure we have enough columns
            data.append(parts)
    
    # Construct DataFrame
    # Expected columns: cre_id, gene_id, tf_id, condition, log2fc, beta1, q_value (approx)
    # We adapt based on what we find in the header
    header_line = lines[header_idx].strip()
    header_parts = [p.strip() for p in header_line.split('|')[1:-1]]
    
    df = pd.DataFrame(data, columns=header_parts[:len(data[0])])
    
    # Normalize column names to lowercase for easier access
    df.columns = [c.lower().replace(' ', '_').replace('-', '_') for c in df.columns]
    
    return df


def plot_visualization_summary(weights_df: pd.DataFrame, ranked_df: pd.DataFrame, output_path: Path):
    """
    Generate the composite visualization summary.
    """
    logger.info("Generating visualization summary plots")
    
    # Prepare data for merging
    # We need to join weights with ranked report to get log2fc if available
    # Assuming 'cre_id' is the key
    merged = weights_df.merge(ranked_df[['cre_id', 'log2fc']], on='cre_id', how='left')
    
    # Filter out NaNs for correlation plot
    corr_data = merged.dropna(subset=['weighted_delta_peak_signal', 'log2fc'])
    
    # Setup plot
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # Plot 1: Correlation
    ax1 = axes[0]
    if not corr_data.empty:
        sns.scatterplot(
            data=corr_data,
            x='weighted_delta_peak_signal',
            y='log2fc',
            ax=ax1,
            alpha=0.6,
            edgecolor='k'
        )
        # Calculate correlation
        rho = corr_data['weighted_delta_peak_signal'].corr(corr_data['log2fc'])
        ax1.set_title(f'Weighted Signal vs Log2FC (ρ={rho:.3f})')
        ax1.set_xlabel('Weighted ΔPeakSignal')
        ax1.set_ylabel('Log2FC')
        ax1.axhline(0, color='gray', linestyle='--', linewidth=0.8)
        ax1.axvline(0, color='gray', linestyle='--', linewidth=0.8)
    else:
        ax1.text(0.5, 0.5, 'No overlap for correlation', ha='center', va='center', transform=ax1.transAxes)
        ax1.set_title('Correlation (No Data)')
    
    # Plot 2: VIF Distribution (if available in weights or separate, assuming we can infer from 'weight_source' or similar if VIF was part of input)
    # Since VIF is in vif_flags.tsv (T013b), and we are visualizing the result of T013c (weights),
    # we check if 'vif_score' is in the weights file or if we need to load it.
    # The task T013c joins vif_flags. If the weights file doesn't have VIF, we skip or load it.
    # For safety, let's assume we need to load vif_flags if not present.
    vif_path = PROCESSED_DIR / "vif_flags.tsv"
    if vif_path.exists():
        vif_df = pd.read_csv(vif_path, sep='\t')
        ax2 = axes[1]
        sns.histplot(data=vif_df, x='vif_score', bins=30, ax=ax2, color='salmon', kde=True)
        ax2.axvline(5, color='red', linestyle='--', linewidth=2, label='Threshold (VIF > 5)')
        ax2.set_title('Distribution of VIF Scores')
        ax2.set_xlabel('VIF Score')
        ax2.set_ylabel('Count')
        ax2.legend()
    else:
        ax2 = axes[1]
        ax2.text(0.5, 0.5, 'VIF Data Missing', ha='center', va='center', transform=ax2.transAxes)
        ax2.set_title('VIF Distribution (Missing)')

    # Plot 3: Top CREs Heatmap (Top 10 by q-value if available, else by beta1)
    ax3 = axes[2]
    # Sort by q-value if present, else beta1
    sort_col = 'q_value' if 'q_value' in ranked_df.columns else ('beta1' if 'beta1' in ranked_df.columns else None)
    
    if sort_col:
        top_n = 10
        top_cre = ranked_df.nsmallest(top_n, sort_col)
        
        # Pivot for heatmap: rows = cre_id, cols = condition (if available) or just index
        # Since we don't have a clear signal matrix per condition in the ranked report,
        # we will visualize the 'weighted_delta_peak_signal' from the weights file for these top CREs.
        
        # Join top_cre with weights to get the signal
        top_merged = top_cre.merge(weights_df[['cre_id', 'weighted_delta_peak_signal', 'gene_id']], on='cre_id', how='left')
        
        if not top_merged.empty:
            # Create a simple bar chart instead of heatmap if condition info is missing
            # Or a heatmap of signal vs gene
            top_merged = top_merged.sort_values(by=sort_col)
            sns.barplot(
                data=top_merged,
                x='cre_id',
                y='weighted_delta_peak_signal',
                ax=ax3,
                palette='viridis'
            )
            ax3.set_title(f'Top {top_n} CREs by {sort_col}')
            ax3.set_xlabel('CRE ID')
            ax3.set_ylabel('Weighted Signal')
            ax3.tick_params(axis='x', rotation=45)
        else:
            ax3.text(0.5, 0.5, 'No Top CREs Found', ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Top CREs (No Data)')
    else:
        ax3.text(0.5, 0.5, 'Missing Sort Column', ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title('Top CREs (Missing)')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved visualization summary to {output_path}")


def write_top_cre_coordinates(ranked_df: pd.DataFrame, weights_df: pd.DataFrame, output_path: Path):
    """
    Write a TSV with coordinates for the top CREs to facilitate track generation.
    Since the ranked report might not have coordinates (chrom, start, end),
    we check if 'cre_id' implies coordinates or if we need to load from a BED file.
    If 'cre_id' is just an ID, we might not have coordinates in this scope.
    However, T018 output usually contains the full table. If coordinates are missing,
    we write what we have and log a warning.
    """
    logger.info(f"Writing top CRE coordinates to {output_path}")
    
    # Identify top 10
    sort_col = 'q_value' if 'q_value' in ranked_df.columns else ('beta1' if 'beta1' in ranked_df.columns else None)
    
    if not sort_col:
        logger.warning("No sort column (q_value or beta1) found in ranked report. Writing all rows.")
        top_cre = ranked_df
    else:
        top_cre = ranked_df.nsmallest(10, sort_col)
    
    # Merge with weights to ensure we have the signal
    output_df = top_cre.merge(weights_df[['cre_id', 'weighted_delta_peak_signal', 'gene_id']], on='cre_id', how='left')
    
    # Check for coordinate columns
    coord_cols = ['chrom', 'start', 'end', 'strand']
    existing_coords = [c for c in coord_cols if c in output_df.columns]
    
    if not existing_coords:
        logger.warning("No coordinate columns (chrom, start, end) found in the ranked report. Output will contain only ID and signal.")
    
    # Ensure output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, sep='\t', index=False)
    logger.info(f"Saved {len(output_df)} top CREs to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate visualization summary for CRE analysis.")
    parser.add_argument(
        "--weights",
        type=str,
        default=str(PROCESSED_DIR / "weights.tsv"),
        help="Path to the weights TSV file."
    )
    parser.add_argument(
        "--report",
        type=str,
        default=str(RESULTS_DIR / "CRE_ranked_heatshock.md"),
        help="Path to the ranked CRE report (Markdown)."
    )
    parser.add_argument(
        "--output-plot",
        type=str,
        default=str(RESULTS_DIR / "visualization_summary.png"),
        help="Path for the output plot."
    )
    parser.add_argument(
        "--output-coords",
        type=str,
        default=str(PROCESSED_DIR / "top_cre_coordinates.tsv"),
        help="Path for the top CRE coordinates TSV."
    )
    
    args = parser.parse_args()
    
    try:
        # Load data
        weights_df = load_weights(Path(args.weights))
        ranked_df = load_ranked_report(Path(args.report))
        
        # Generate plots
        plot_visualization_summary(weights_df, ranked_df, Path(args.output_plot))
        
        # Write coordinates
        write_top_cre_coordinates(ranked_df, weights_df, Path(args.output_coords))
        
        logger.info("Visualization step completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during visualization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
