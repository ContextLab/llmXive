import os
import sys
import logging
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server/headless environments
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from main import load_config
from evaluate import load_flags, load_ground_truth
from sensitivity_aggregator import load_grid_results, load_tolerance_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_metrics(report_path: str = 'data/processed/report_metrics.json') -> Dict:
    """Load metrics from the evaluation report if available."""
    if os.path.exists(report_path):
        try:
            # Assuming JSON format for metrics
            with open(report_path, 'r') as f:
                import json
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load metrics from {report_path}: {e}")
    return {}

def load_flags(flags_path: str = 'data/processed/flags.csv') -> pd.DataFrame:
    """Load the flags CSV."""
    if os.path.exists(flags_path):
        return pd.read_csv(flags_path)
    return pd.DataFrame()

def load_ground_truth(gt_path: str = 'data/raw/ground_truth_events.csv') -> pd.DataFrame:
    """Load ground truth events."""
    if os.path.exists(gt_path):
        return pd.read_csv(gt_path)
    return pd.DataFrame()

def create_summary_plot(metrics: Dict, sensitivity_results: pd.DataFrame, output_path: str):
    """Create a summary plot showing MMD performance vs sensitivity parameters."""
    plt.figure(figsize=(12, 8))
    
    if sensitivity_results.empty:
        plt.text(0.5, 0.5, 'No sensitivity data available', ha='center', va='center', fontsize=12)
    else:
        # Plot Precision vs Bandwidth for different window sizes
        unique_windows = sensitivity_results['window_size'].unique()
        colors = plt.cm.Set3(np.linspace(0, 1, len(unique_windows)))
        
        for i, window in enumerate(unique_windows):
            subset = sensitivity_results[sensitivity_results['window_size'] == window]
            plt.plot(subset['bandwidth'], subset['precision'], 
                     marker='o', label=f'Window={window}', color=colors[i])
        
        plt.xlabel('Bandwidth (sigma)')
        plt.ylabel('Precision')
        plt.title('Sensitivity Analysis: Precision vs Bandwidth by Window Size')
        plt.legend()
        plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved summary plot to {output_path}")

def create_tolerance_plot(tolerance_results: pd.DataFrame, output_path: str):
    """Create a plot showing metric variation across tolerance windows."""
    plt.figure(figsize=(10, 6))
    
    if tolerance_results.empty:
        plt.text(0.5, 0.5, 'No tolerance data available', ha='center', va='center', fontsize=12)
    else:
        # Plot Recall vs Tolerance
        plt.plot(tolerance_results['tolerance_weeks'], tolerance_results['recall'], 
                 marker='s', color='blue', linewidth=2, markersize=8)
        plt.plot(tolerance_results['tolerance_weeks'], tolerance_results['precision'], 
                 marker='^', color='red', linewidth=2, markersize=8)
        
        plt.xlabel('Tolerance (weeks)')
        plt.ylabel('Metric Score')
        plt.title('Sensitivity Analysis: Metric Variation vs Detection Tolerance')
        plt.legend(['Recall', 'Precision'])
        plt.grid(True, alpha=0.3)
        plt.xticks(tolerance_results['tolerance_weeks'])
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved tolerance plot to {output_path}")

def create_timeline_plot(flags_df: pd.DataFrame, ground_truth_df: pd.DataFrame, output_path: str):
    """Create a timeline plot showing detected shifts vs ground truth events."""
    plt.figure(figsize=(14, 6))
    
    if not flags_df.empty:
        # Plot ILI data if available (assuming a column 'ili_value' or similar)
        # If not, just plot the flags
        if 'week' in flags_df.columns and 'ili_value' in flags_df.columns:
            plt.plot(flags_df['week'], flags_df['ili_value'], 'k-', alpha=0.5, label='ILI Value')
        
        # Plot flags
        flagged_weeks = flags_df[flags_df['is_shift'] == 1]['week']
        plt.scatter(flagged_weeks, 
                    [flags_df[flags_df['week'] == w]['ili_value'].values[0] if 'ili_value' in flags_df.columns else 0 
                     for w in flagged_weeks],
                    color='red', s=100, marker='x', label='Detected Shift (MMD)', zorder=5)
    
    if not ground_truth_df.empty:
        # Plot ground truth events as vertical bands
        for _, row in ground_truth_df.iterrows():
            start = row.get('start_week')
            end = row.get('end_week')
            if pd.notna(start) and pd.notna(end):
                plt.axvspan(start, end, color='green', alpha=0.2, label='Ground Truth Event' if start == ground_truth_df.iloc[0]['start_week'] else "")
                plt.axvline(start, color='green', linestyle='--', alpha=0.5)
    
    plt.xlabel('Week')
    plt.ylabel('Value')
    plt.title('Distribution Shift Detection: MMD Flags vs Ground Truth Events')
    plt.legend(loc='upper left')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved timeline plot to {output_path}")

def generate_report(output_path: str = 'figures/report.pdf'):
    """
    Generate the final report PDF including:
    1. Executive Summary
    2. MMD Detection Results
    3. Sensitivity Analysis Summary (T033 requirement)
    4. Variation Plots
    5. Baseline Comparison (if available)
    """
    logger.info("Generating report PDF...")
    
    # Load data
    config = load_config()
    flags_df = load_flags()
    ground_truth_df = load_ground_truth()
    grid_results = load_grid_results()
    tolerance_results = load_tolerance_results()
    metrics = load_metrics()
    
    # Create plots directory if needed
    plots_dir = 'figures'
    os.makedirs(plots_dir, exist_ok=True)
    
    # Generate plots
    summary_plot_path = os.path.join(plots_dir, 'sensitivity_summary.png')
    tolerance_plot_path = os.path.join(plots_dir, 'tolerance_variation.png')
    timeline_plot_path = os.path.join(plots_dir, 'detection_timeline.png')
    
    create_summary_plot(metrics, grid_results, summary_plot_path)
    create_tolerance_plot(tolerance_results, tolerance_plot_path)
    create_timeline_plot(flags_df, ground_truth_df, timeline_plot_path)
    
    # Create the PDF report using matplotlib
    # Note: For a full PDF with text, we use a multi-page figure approach
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Distribution Shift Detection Report\nGenerated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', fontsize=14, fontweight='bold')
    
    # Page 1: Overview and Timeline
    ax1 = axs[0, 0]
    ax1.text(0.1, 0.9, 'Executive Summary', fontsize=12, fontweight='bold')
    ax1.text(0.1, 0.8, f'Total weeks analyzed: {len(flags_df) if not flags_df.empty else 0}', fontsize=10)
    ax1.text(0.1, 0.75, f'Shifts detected: {len(flags_df[flags_df["is_shift"] == 1]) if not flags_df.empty else 0}', fontsize=10)
    if not ground_truth_df.empty:
        ax1.text(0.1, 0.7, f'Ground truth events: {len(ground_truth_df)}', fontsize=10)
    
    # Insert timeline image
    ax1.imshow(plt.imread(timeline_plot_path))
    ax1.axis('off')
    
    # Page 1: Sensitivity Summary
    ax2 = axs[0, 1]
    ax2.text(0.1, 0.9, 'Sensitivity Analysis: Parameter Grid', fontsize=12, fontweight='bold')
    if not grid_results.empty:
        ax2.imshow(plt.imread(summary_plot_path))
    else:
        ax2.text(0.5, 0.5, 'No grid search results available', ha='center', va='center')
    ax2.axis('off')
    
    # Page 1: Tolerance Sensitivity
    ax3 = axs[1, 0]
    ax3.text(0.1, 0.9, 'Sensitivity Analysis: Tolerance Sweep', fontsize=12, fontweight='bold')
    if not tolerance_results.empty:
        ax3.imshow(plt.imread(tolerance_plot_path))
    else:
        ax3.text(0.5, 0.5, 'No tolerance sweep results available', ha='center', va='center')
    ax3.axis('off')
    
    # Page 1: Metrics Summary Table
    ax4 = axs[1, 1]
    ax4.text(0.1, 0.9, 'Key Metrics', fontsize=12, fontweight='bold')
    if metrics:
        rows = list(metrics.keys())
        vals = [str(v) for v in metrics.values()]
        table_data = [[r, v] for r, v in zip(rows, vals)]
        table = ax4.table(cellText=table_data, colLabels=['Metric', 'Value'], 
                         loc='center', cellLoc='left')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)
        ax4.axis('off')
    else:
        ax4.text(0.5, 0.5, 'No metrics available', ha='center', va='center')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Report generated successfully: {output_path}")
    return output_path

def main():
    """Main entry point for report generation."""
    logger.info("Starting report generation...")
    try:
        output_path = generate_report()
        logger.info(f"Report generation complete. Output: {output_path}")
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise

if __name__ == "__main__":
    main()