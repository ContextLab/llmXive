"""
Replicate Statistics Dashboard Implementation

Generates a visual and tabular summary of replicate statistics across all solvent
conditions, addressing Marie Curie's concern for reporting replicate counts,
standard deviations, and coefficient of variation.

Outputs:
    data/processed/replicate_statistics.json: Tabular summary of metrics
    figures/replicate_dashboard.png: Visual dashboard of statistics
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Import from project modules using verified API surface
from analysis.kinetic_metrics import load_kinetic_results, load_outlier_flags
from config import get_processed_data_path, get_figures_path, ensure_directories
from utils.seeds import set_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_kinetic_metrics_for_dashboard() -> pd.DataFrame:
    """
    Load kinetic metrics from the processed data file.
    
    Returns:
        DataFrame with columns: solvent, lifetime, ci_lower, ci_upper, is_outlier
    """
    metrics_path = get_processed_data_path() / "kinetic_metrics.csv"
    
    if not metrics_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {metrics_path}. "
            "Please ensure T026 (kinetic_metrics) has been executed."
        )
    
    df = pd.read_csv(metrics_path)
    
    # Ensure required columns exist
    required_cols = ['solvent', 'lifetime']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {metrics_path}: {missing_cols}")
    
    # Load outlier flags if available
    outlier_path = get_processed_data_path() / "outlier_flags.json"
    if outlier_path.exists():
        with open(outlier_path, 'r') as f:
            outlier_data = json.load(f)
        # Convert to DataFrame and merge
        outlier_df = pd.DataFrame([
            {'solvent': k, 'is_outlier': v} for k, v in outlier_data.items()
        ])
        df = df.merge(outlier_df, on='solvent', how='left')
        df['is_outlier'] = df['is_outlier'].fillna(False)
    else:
        df['is_outlier'] = False
    
    # Add CI columns if available
    if 'ci_lower' not in df.columns:
        df['ci_lower'] = np.nan
    if 'ci_upper' not in df.columns:
        df['ci_upper'] = np.nan
    
    return df

def calculate_replicate_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate aggregate statistics for each solvent condition.
    
    Args:
        df: DataFrame with individual run data
        
    Returns:
        DataFrame with aggregated statistics per solvent
    """
    stats = df.groupby('solvent').agg(
        n_runs=('lifetime', 'count'),
        mean_lifetime=('lifetime', 'mean'),
        std_lifetime=('lifetime', 'std'),
        min_lifetime=('lifetime', 'min'),
        max_lifetime=('lifetime', 'max'),
        ci_lower_min=('ci_lower', 'min'),
        ci_upper_max=('ci_upper', 'max'),
        outlier_count=('is_outlier', 'sum')
    ).reset_index()
    
    # Calculate coefficient of variation (CV = std / mean)
    stats['cv'] = stats['std_lifetime'] / stats['mean_lifetime']
    
    # Handle case where std is NaN (n=1)
    stats['cv'] = stats['cv'].fillna(0.0)
    
    # Format for reporting
    stats = stats.round(4)
    
    return stats

def generate_dashboard_table(stats_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a structured dictionary representation of the statistics table.
    
    Args:
        stats_df: DataFrame with calculated statistics
        
    Returns:
        Dictionary with table data and metadata
    """
    table_data = stats_df.to_dict(orient='records')
    
    report = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'total_solvents': len(stats_df),
        'total_runs': int(stats_df['n_runs'].sum()),
        'statistics': table_data,
        'summary': {
            'min_runs_per_solvent': int(stats_df['n_runs'].min()),
            'max_runs_per_solvent': int(stats_df['n_runs'].max()),
            'mean_cv': float(stats_df['cv'].mean()),
            'total_outliers': int(stats_df['outlier_count'].sum())
        }
    }
    
    return report

def plot_replicate_dashboard(stats_df: pd.DataFrame, output_path: Path) -> None:
    """
    Generate a visual dashboard of replicate statistics.
    
    Creates a multi-panel figure showing:
        1. Mean lifetime with error bars per solvent
        2. Number of replicates per solvent
        3. Coefficient of variation per solvent
        4. Outlier flags per solvent
        
    Args:
        stats_df: DataFrame with calculated statistics
        output_path: Path to save the figure
    """
    # Set style
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Replicate Statistics Dashboard - Photo-Fries Rearrangement', 
                fontsize=14, fontweight='bold')
    
    solvents = stats_df['solvent'].tolist()
    n_solvents = len(solvents)
    
    # Panel 1: Mean lifetime with error bars (95% CI approximation)
    ax1 = axes[0, 0]
    x_pos = np.arange(n_solvents)
    y_vals = stats_df['mean_lifetime'].values
    y_err_lower = stats_df['mean_lifetime'].values - stats_df['ci_lower_min'].values
    y_err_upper = stats_df['ci_upper_max'].values - stats_df['mean_lifetime'].values
    y_err = [y_err_lower, y_err_upper]
    
    bars = ax1.bar(x_pos, y_vals, yerr=y_err, capsize=5, alpha=0.7, color='steelblue')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(solvents, rotation=45, ha='right')
    ax1.set_ylabel('Mean Lifetime (s)')
    ax1.set_title('Mean Lifetime with Confidence Intervals')
    ax1.grid(True, alpha=0.3)
    
    # Highlight outliers
    outlier_mask = stats_df['outlier_count'] > 0
    if outlier_mask.any():
        for i, is_outlier in enumerate(outlier_mask):
            if is_outlier:
                bars[i].set_edgecolor('red')
                bars[i].set_linewidth(2)
    
    # Panel 2: Number of replicates per solvent
    ax2 = axes[0, 1]
    colors = ['green' if n >= 3 else 'orange' if n >= 2 else 'red' 
             for n in stats_df['n_runs'].values]
    bars2 = ax2.bar(x_pos, stats_df['n_runs'].values, color=colors, alpha=0.7)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(solvents, rotation=45, ha='right')
    ax2.set_ylabel('Number of Runs')
    ax2.set_title('Replicate Count per Solvent')
    ax2.set_ylim(0, max(stats_df['n_runs'].max() + 1, 5))
    
    # Add threshold line for recommended n=3
    ax2.axhline(y=3, color='gray', linestyle='--', label='Recommended n≥3')
    ax2.legend()
    
    # Panel 3: Coefficient of variation
    ax3 = axes[1, 0]
    colors_cv = ['green' if cv < 0.1 else 'orange' if cv < 0.2 else 'red' 
                for cv in stats_df['cv'].values]
    bars3 = ax3.bar(x_pos, stats_df['cv'].values, color=colors_cv, alpha=0.7)
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(solvents, rotation=45, ha='right')
    ax3.set_ylabel('Coefficient of Variation (CV)')
    ax3.set_title('Precision Measure (CV = σ/μ)')
    ax3.grid(True, alpha=0.3)
    
    # Panel 4: Outlier flags
    ax4 = axes[1, 1]
    outlier_counts = stats_df['outlier_count'].values
    colors_out = ['white' if c == 0 else 'lightcoral' for c in outlier_counts]
    bars4 = ax4.bar(x_pos, outlier_counts, color=colors_out, edgecolor='black', alpha=0.7)
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels(solvents, rotation=45, ha='right')
    ax4.set_ylabel('Number of Outliers')
    ax4.set_title('Outlier Detection Results')
    ax4.set_ylim(0, max(outlier_counts.max() + 1, 2))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Dashboard figure saved to: {output_path}")

def write_dashboard_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Write the statistics report to a JSON file.
    
    Args:
        report: Dictionary containing dashboard data
        output_path: Path to save the JSON file
    """
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Dashboard report saved to: {output_path}")

def run_replicate_dashboard_pipeline(seed: Optional[int] = None) -> Tuple[Path, Path]:
    """
    Execute the full replicate dashboard generation pipeline.
    
    Steps:
        1. Load kinetic metrics
        2. Calculate replicate statistics
        3. Generate dashboard table
        4. Create visual dashboard
        5. Write JSON report
        
    Args:
        seed: Optional random seed for reproducibility
        
    Returns:
        Tuple of (json_report_path, figure_path)
    """
    if seed is not None:
        set_seed(seed)
    
    ensure_directories()
    
    # Load data
    logger.info("Loading kinetic metrics...")
    df = load_kinetic_metrics_for_dashboard()
    
    if df.empty:
        raise ValueError("No kinetic metrics data found. Ensure T026 has been executed.")
    
    logger.info(f"Loaded {len(df)} kinetic measurements across {df['solvent'].nunique()} solvents")
    
    # Calculate statistics
    logger.info("Calculating replicate statistics...")
    stats_df = calculate_replicate_statistics(df)
    
    # Generate report
    logger.info("Generating dashboard report...")
    report = generate_dashboard_table(stats_df)
    
    # Define output paths
    json_path = get_processed_data_path() / "replicate_statistics.json"
    figure_path = get_figures_path() / "replicate_dashboard.png"
    
    # Write outputs
    write_dashboard_report(report, json_path)
    plot_replicate_dashboard(stats_df, figure_path)
    
    logger.info("Replicate dashboard generation complete!")
    logger.info(f"  - Statistics: {json_path}")
    logger.info(f"  - Dashboard: {figure_path}")
    
    return json_path, figure_path

def main():
    """CLI entry point for replicate dashboard generation."""
    parser = argparse.ArgumentParser(
        description='Generate replicate statistics dashboard for solvent series'
    )
    parser.add_argument(
        '--seed', 
        type=int, 
        default=None, 
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Override default output directory (not recommended)'
    )
    
    args = parser.parse_args()
    
    try:
        json_path, figure_path = run_replicate_dashboard_pipeline(seed=args.seed)
        print(f"Dashboard generated successfully:")
        print(f"  JSON Report: {json_path}")
        print(f"  Figure: {figure_path}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
