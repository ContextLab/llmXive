import os
import sys
import logging
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import yaml

# Import project utilities
from main import load_config, DataPathsConfig
from exceptions import E_NO_DATA

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_metrics(output_dir: str) -> Dict[str, pd.DataFrame]:
    """Load metrics from sensitivity analysis outputs."""
    grid_path = os.path.join(output_dir, 'sensitivity.csv')
    tol_path = os.path.join(output_dir, 'tolerance_sensitivity.csv')
    
    results = {}
    if os.path.exists(grid_path):
        results['grid'] = pd.read_csv(grid_path)
    if os.path.exists(tol_path):
        results['tolerance'] = pd.read_csv(tol_path)
        
    if not results:
        raise FileNotFoundError("No sensitivity analysis results found. Run sensitivity.py first.")
        
    return results

def load_flags(output_dir: str) -> pd.DataFrame:
    """Load the main pipeline flags."""
    path = os.path.join(output_dir, 'flags.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Flags file not found at {path}. Run main.py pipeline first.")
    return pd.read_csv(path)

def load_ground_truth(data_dir: str) -> pd.DataFrame:
    """Load ground truth events."""
    path = os.path.join(data_dir, 'ground_truth_events.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Ground truth file not found at {path}.")
    return pd.read_csv(path)

def create_summary_plot(metrics: Dict[str, pd.DataFrame], save_path: str):
    """
    Create a summary plot showing sensitivity of metrics (Precision, Recall, Delay)
    to different bandwidths and window sizes.
    """
    if 'grid' not in metrics:
        logger.warning("Grid results not found, skipping summary plot.")
        return

    df = metrics['grid']
    required_cols = ['precision', 'recall', 'detection_delay']
    if not all(col in df.columns for col in required_cols):
        logger.warning(f"Missing columns in grid data. Expected {required_cols}, found {df.columns.tolist()}")
        return

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Plot Precision
    ax = axes[0]
    # Group by bandwidth, mean over window sizes
    prec_bw = df.groupby('bandwidth')['precision'].mean()
    ax.bar(prec_bw.index.astype(str), prec_bw.values, color='skyblue', edgecolor='navy')
    ax.set_title('Mean Precision vs Bandwidth')
    ax.set_xlabel('Bandwidth (sigma)')
    ax.set_ylabel('Precision')
    ax.tick_params(axis='x', rotation=45)

    # Plot Recall
    ax = axes[1]
    rec_win = df.groupby('window_size')['recall'].mean()
    ax.bar(rec_win.index.astype(str), rec_win.values, color='lightgreen', edgecolor='darkgreen')
    ax.set_title('Mean Recall vs Window Size')
    ax.set_xlabel('Window Size (weeks)')
    ax.set_ylabel('Recall')
    ax.tick_params(axis='x', rotation=45)

    # Plot Detection Delay
    ax = axes[2]
    delay_combined = df.groupby(['bandwidth', 'window_size'])['detection_delay'].mean().reset_index()
    # Pivot for heatmap-like bar chart or just scatter
    # Let's do a grouped bar or scatter with color
    # Simple: mean delay by window size, colored by bandwidth
    unique_bw = delay_combined['bandwidth'].unique()
    colors = plt.cm.viridis(np.linspace(0, 1, len(unique_bw)))
    
    for i, bw in enumerate(unique_bw):
        subset = delay_combined[delay_combined['bandwidth'] == bw]
        ax.bar(subset['window_size'] + i*0.2, subset['detection_delay'], width=0.2, label=f'{bw:.2f}', color=colors[i])
    
    ax.set_title('Mean Detection Delay')
    ax.set_xlabel('Window Size (weeks)')
    ax.set_ylabel('Delay (weeks)')
    ax.legend(title='Bandwidth')
    ax.set_xticks(df['window_size'].unique() + 0.1)
    ax.set_xticklabels(df['window_size'].unique())

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Summary plot saved to {save_path}")

def create_tolerance_plot(metrics: Dict[str, pd.DataFrame], save_path: str):
    """
    Create a plot showing how metrics vary with week-alignment tolerance.
    """
    if 'tolerance' not in metrics:
        logger.warning("Tolerance results not found, skipping tolerance plot.")
        return

    df = metrics['tolerance']
    if 'tolerance' not in df.columns:
        logger.warning("Tolerance column missing in tolerance data.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot Precision, Recall, F1 vs Tolerance
    if 'precision' in df.columns:
        ax.plot(df['tolerance'], df['precision'], marker='o', label='Precision', linewidth=2)
    if 'recall' in df.columns:
        ax.plot(df['tolerance'], df['recall'], marker='s', label='Recall', linewidth=2)
    if 'f1' in df.columns:
        ax.plot(df['tolerance'], df['f1'], marker='^', label='F1 Score', linewidth=2)
        
    ax.set_title('Metric Sensitivity to Week-Alignment Tolerance')
    ax.set_xlabel('Tolerance (weeks)')
    ax.set_ylabel('Score')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.set_xticks(df['tolerance'].unique())
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Tolerance plot saved to {save_path}")

def create_timeline_plot(flags: pd.DataFrame, ground_truth: pd.DataFrame, save_path: str):
    """
    Create a timeline plot showing detected shifts vs ground truth events.
    """
    if flags.empty or ground_truth.empty:
        logger.warning("Empty flags or ground truth, skipping timeline plot.")
        return

    fig, ax = plt.subplots(figsize=(14, 6))

    # Plot Ground Truth Events as vertical shaded regions
    for _, row in ground_truth.iterrows():
        start = row['start_week']
        end = row['end_week']
        ax.axvspan(start, end, color='red', alpha=0.2, label='Ground Truth Event' if start == ground_truth['start_week'].iloc[0] else "")

    # Plot Detected Flags
    # Assuming flags has 'week' and 'is_shift' columns
    if 'week' in flags.columns and 'is_shift' in flags.columns:
        shift_weeks = flags[flags['is_shift']]['week']
        ax.scatter(shift_weeks, [0]*len(shift_weeks), color='blue', marker='x', s=100, label='Detected Shift', zorder=5)
        
        # Add text labels for detected weeks
        for w in shift_weeks:
            ax.text(w, 0.1, f"Detected", rotation=90, fontsize=8, va='bottom', ha='center')

    ax.set_title('Distribution Shift Detection Timeline')
    ax.set_xlabel('Week Index')
    ax.set_ylabel('Signal (0 = No Shift)')
    ax.set_yticks([])  # Hide y-axis as it's just a timeline
    ax.legend(loc='upper right')
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Timeline plot saved to {save_path}")

def generate_report(output_dir: str, data_dir: str, report_path: str):
    """
    Generate the final PDF report including:
    1. Executive Summary
    2. Sensitivity Analysis Summary (Grid & Tolerance)
    3. Variation Plots
    4. Detection Timeline
    """
    logger.info(f"Generating report at {report_path}")
    
    # Load data
    try:
        metrics = load_metrics(output_dir)
        flags = load_flags(output_dir)
        ground_truth = load_ground_truth(data_dir)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    # Create plots
    plots_dir = os.path.join(output_dir, 'figures')
    os.makedirs(plots_dir, exist_ok=True)
    
    summary_plot_path = os.path.join(plots_dir, 'sensitivity_summary.png')
    tolerance_plot_path = os.path.join(plots_dir, 'tolerance_sensitivity.png')
    timeline_plot_path = os.path.join(plots_dir, 'detection_timeline.png')
    
    create_summary_plot(metrics, summary_plot_path)
    create_tolerance_plot(metrics, tolerance_plot_path)
    create_timeline_plot(flags, ground_truth, timeline_plot_path)

    # Generate PDF using matplotlib's pdf backend directly or reportlab if available
    # Since we want to keep dependencies minimal and use existing matplotlib, we will construct a PDF
    # using matplotlib's PdfPages.
    
    from matplotlib.backends.backend_pdf import PdfPages
    
    with PdfPages(report_path) as pdf:
        # Page 1: Title and Summary
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis('off')
        plt.title('Distribution Shift Detection Report', fontsize=24, pad=20)
        plt.text(0.5, 0.9, 'Sensitivity Analysis Summary', fontsize=18, ha='center')
        
        # Add a table with key metrics if available
        if 'grid' in metrics:
            grid_df = metrics['grid']
            best_idx = grid_df['f1'].idxmax() if 'f1' in grid_df.columns else grid_df['recall'].idxmax()
            best_config = grid_df.loc[best_idx]
            
            table_data = [
                ['Configuration', 'Value'],
                ['Best Bandwidth', f"{best_config['bandwidth']:.2f}"],
                ['Best Window Size', f"{best_config['window_size']}"],
                ['Max Precision', f"{best_config['precision']:.3f}" if 'precision' in best_config else "N/A"],
                ['Max Recall', f"{best_config['recall']:.3f}" if 'recall' in best_config else "N/A"],
                ['Min Delay', f"{best_config['detection_delay']:.2f}" if 'detection_delay' in best_config else "N/A"]
            ]
            
            table = ax.table(cellText=table_data, loc='center', cellLoc='center', colWidths=[0.3, 0.3])
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            table.scale(1.2, 1.5)
            
            # Add a note about the Bonferroni correction
            plt.text(0.5, 0.4, 
                     f"Note: Statistical significance threshold adjusted via Bonferroni correction (α = 0.01/N).\n"
                     f"Permutation count dynamically adjusted for runtime constraints without altering threshold.",
                     fontsize=10, ha='center', style='italic')

        pdf.savefig(fig)
        plt.close(fig)

        # Page 2: Sensitivity Plots
        fig, axes = plt.subplots(2, 1, figsize=(8.5, 11))
        
        # Re-load images to display in PDF
        if os.path.exists(summary_plot_path):
            ax[0].imshow(plt.imread(summary_plot_path))
            ax[0].axis('off')
            ax[0].set_title('Sensitivity to Kernel & Window Parameters')
        else:
            ax[0].text(0.5, 0.5, 'Summary Plot Not Generated', ha='center')
            ax[0].axis('off')

        if os.path.exists(tolerance_plot_path):
            ax[1].imshow(plt.imread(tolerance_plot_path))
            ax[1].axis('off')
            ax[1].set_title('Sensitivity to Week-Alignment Tolerance')
        else:
            ax[1].text(0.5, 0.5, 'Tolerance Plot Not Generated', ha='center')
            ax[1].axis('off')

        plt.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

        # Page 3: Timeline
        fig, ax = plt.subplots(figsize=(8.5, 11))
        if os.path.exists(timeline_plot_path):
            ax.imshow(plt.imread(timeline_plot_path))
            ax.axis('off')
            ax.set_title('Detection Timeline vs Ground Truth')
        else:
            ax.text(0.5, 0.5, 'Timeline Plot Not Generated', ha='center')
            ax.axis('off')
        
        plt.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

    logger.info(f"Report successfully generated: {report_path}")

def main():
    """Entry point for report generation."""
    config = load_config()
    paths = DataPathsConfig()
    
    output_dir = paths.PROCESSED_DIR
    data_dir = paths.RAW_DIR
    report_path = os.path.join(output_dir, 'report.pdf')
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        generate_report(output_dir, data_dir, report_path)
        print(f"Report generation complete: {report_path}")
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise

if __name__ == "__main__":
    main()