"""
Report Generator Module

Generates a comprehensive PDF report containing MMD detection metrics,
ground truth comparison, and statistical summaries.
"""
import os
import sys
import logging
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for PDF generation
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from contracts import validate_output_data

# Configure logging
logger = logging.getLogger(__name__)

def load_metrics(metrics_path: str) -> Dict[str, Any]:
    """
    Load evaluation metrics from the metrics CSV file.
    
    Args:
        metrics_path: Path to the metrics CSV file (e.g., data/processed/metrics.csv)
        
    Returns:
        Dictionary containing precision, recall, detection_delay, etc.
    """
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    df = pd.read_csv(metrics_path)
    metrics = {}
    
    # Extract scalar metrics (assuming first row for summary)
    if len(df) > 0:
        metrics['precision'] = float(df.iloc[0].get('precision', 0.0))
        metrics['recall'] = float(df.iloc[0].get('recall', 0.0))
        metrics['f1_score'] = float(df.iloc[0].get('f1_score', 0.0))
        metrics['detection_delay_mean'] = float(df.iloc[0].get('detection_delay_mean', 0.0))
        metrics['detection_delay_std'] = float(df.iloc[0].get('detection_delay_std', 0.0))
        metrics['total_flags'] = int(df.iloc[0].get('total_flags', 0))
        metrics['true_positives'] = int(df.iloc[0].get('true_positives', 0))
        metrics['false_positives'] = int(df.iloc[0].get('false_positives', 0))
        metrics['false_negatives'] = int(df.iloc[0].get('false_negatives', 0))
        metrics['total_ground_truth_events'] = int(df.iloc[0].get('total_ground_truth_events', 0))
    else:
        # Default values if file is empty
        metrics = {
            'precision': 0.0, 'recall': 0.0, 'f1_score': 0.0,
            'detection_delay_mean': 0.0, 'detection_delay_std': 0.0,
            'total_flags': 0, 'true_positives': 0, 'false_positives': 0,
            'false_negatives': 0, 'total_ground_truth_events': 0
        }
        
    return metrics

def load_flags(flags_path: str) -> pd.DataFrame:
    """
    Load flagged weeks from the flags CSV.
    
    Args:
        flags_path: Path to the flags CSV file
        
    Returns:
        DataFrame with flagged weeks
    """
    if not os.path.exists(flags_path):
        raise FileNotFoundError(f"Flags file not found: {flags_path}")
    return pd.read_csv(flags_path)

def load_ground_truth(gt_path: str) -> pd.DataFrame:
    """
    Load ground truth events.
    
    Args:
        gt_path: Path to the ground truth CSV file
        
    Returns:
        DataFrame with ground truth events
    """
    if not os.path.exists(gt_path):
        raise FileNotFoundError(f"Ground truth file not found: {gt_path}")
    return pd.read_csv(gt_path)

def create_summary_plot(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Create a bar chart visualization of key metrics.
    
    Args:
        metrics: Dictionary of metrics to visualize
        output_path: Path to save the plot image
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    categories = ['Precision', 'Recall', 'F1-Score']
    values = [metrics['precision'], metrics['recall'], metrics['f1_score']]
    
    bars = ax.bar(categories, values, color=['#3498db', '#2ecc71', '#e74c3c'], edgecolor='black')
    ax.set_ylim(0, 1.0)
    ax.set_ylabel('Score')
    ax.set_title('MMD Detection Performance Metrics')
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add value labels on bars
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{val:.3f}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Summary plot saved to {output_path}")

def create_timeline_plot(flags: pd.DataFrame, ground_truth: pd.DataFrame, 
                         output_path: str) -> None:
    """
    Create a timeline visualization showing flagged weeks and ground truth events.
    
    Args:
        flags: DataFrame of flagged weeks
        ground_truth: DataFrame of ground truth events
        output_path: Path to save the plot image
    """
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Plot flags as points
    if not flags.empty:
        ax.scatter(flags['week'], [0.5] * len(flags), 
                  marker='|', s=200, color='red', label='MMD Flags', zorder=5)
    
    # Plot ground truth events as shaded regions
    if not ground_truth.empty:
        for _, event in ground_truth.iterrows():
            start = event['start_week']
            end = event.get('end_week', start)
            # Ensure numeric
            start = float(start)
            end = float(end)
            ax.axvspan(start, end, color='blue', alpha=0.3, 
                      label='Ground Truth' if _ == ground_truth.index[0] else "")
    
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xlabel('Week')
    ax.set_title('Distribution Shift Detection Timeline')
    ax.legend(loc='upper right')
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Timeline plot saved to {output_path}")

def generate_report(metrics_path: str, flags_path: str, gt_path: str, 
                   output_pdf: str) -> None:
    """
    Generate a comprehensive PDF report with metrics and visualizations.
    
    Args:
        metrics_path: Path to the metrics CSV
        flags_path: Path to the flags CSV
        gt_path: Path to the ground truth CSV
        output_pdf: Path to save the final PDF report
    """
    logger.info(f"Generating report: {output_pdf}")
    
    # Load data
    metrics = load_metrics(metrics_path)
    flags = load_flags(flags_path)
    ground_truth = load_ground_truth(gt_path)
    
    # Create temporary directory for plots if needed
    plots_dir = os.path.join(os.path.dirname(output_pdf), 'plots')
    os.makedirs(plots_dir, exist_ok=True)
    
    summary_plot_path = os.path.join(plots_dir, 'summary_metrics.png')
    timeline_plot_path = os.path.join(plots_dir, 'timeline.png')
    
    # Generate plots
    create_summary_plot(metrics, summary_plot_path)
    create_timeline_plot(flags, ground_truth, timeline_plot_path)
    
    # Create PDF using matplotlib's pdf pages
    from matplotlib.backends.backend_pdf import PdfPages
    
    with PdfPages(output_pdf) as pdf:
        # Cover Page
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis('off')
        ax.text(0.5, 0.8, 'Distribution Shift Detection Report', 
               fontsize=24, ha='center', va='center', weight='bold')
        ax.text(0.5, 0.7, 'MMD-Based Analysis of CDC FluView ILI Data',
               fontsize=16, ha='center', va='center')
        ax.text(0.5, 0.6, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
               fontsize=12, ha='center', va='center')
        ax.text(0.5, 0.4, 'User Story 1: Automated Shift Detection',
               fontsize=14, ha='center', va='center')
        pdf.savefig(fig)
        plt.close(fig)
        
        # Executive Summary Page
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis('off')
        
        y_pos = 0.85
        title = "Executive Summary"
        ax.text(0.1, y_pos, title, fontsize=18, weight='bold')
        y_pos -= 0.15
        
        summary_text = (
            f"Precision: {metrics['precision']:.4f}\n"
            f"Recall: {metrics['recall']:.4f}\n"
            f"F1-Score: {metrics['f1_score']:.4f}\n"
            f"Mean Detection Delay: {metrics['detection_delay_mean']:.2f} weeks\n"
            f"Std Detection Delay: {metrics['detection_delay_std']:.2f} weeks\n\n"
            f"Total Flags Generated: {metrics['total_flags']}\n"
            f"True Positives: {metrics['true_positives']}\n"
            f"False Positives: {metrics['false_positives']}\n"
            f"False Negatives: {metrics['false_negatives']}\n"
            f"Total Ground Truth Events: {metrics['total_ground_truth_events']}"
        )
        ax.text(0.1, y_pos, summary_text, fontsize=12, verticalalignment='top')
        pdf.savefig(fig)
        plt.close(fig)
        
        # Metrics Visualization Page
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis('off')
        ax.text(0.1, 0.95, 'Performance Metrics Visualization', 
               fontsize=16, weight='bold')
        # Load the saved image and display it
        img = plt.imread(summary_plot_path)
        ax.imshow(img)
        ax.axis('off')
        pdf.savefig(fig)
        plt.close(fig)
        
        # Timeline Visualization Page
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis('off')
        ax.text(0.1, 0.95, 'Detection Timeline', 
               fontsize=16, weight='bold')
        img = plt.imread(timeline_plot_path)
        ax.imshow(img)
        ax.axis('off')
        pdf.savefig(fig)
        plt.close(fig)
        
        # Data Tables Page
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis('off')
        ax.text(0.1, 0.95, 'Flagged Weeks', fontsize=16, weight='bold')
        
        if not flags.empty:
            table_data = flags[['week', 'mmd_statistic', 'p_value']].head(20).values.tolist()
            col_labels = flags[['week', 'mmd_statistic', 'p_value']].columns.tolist()
            table = ax.table(cellText=table_data, colLabels=col_labels,
                             loc='center', cellLoc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 1.5)
            ax.set_title('Top 20 Flagged Weeks (by MMD Statistic)')
        else:
            ax.text(0.5, 0.5, 'No flags generated', ha='center', va='center', fontsize=14)
        
        pdf.savefig(fig)
        plt.close(fig)
        
        # Ground Truth Events Page
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis('off')
        ax.text(0.1, 0.95, 'Ground Truth Events', fontsize=16, weight='bold')
        
        if not ground_truth.empty:
            table_data = ground_truth[['start_week', 'end_week', 'event_name']].values.tolist()
            col_labels = ground_truth[['start_week', 'end_week', 'event_name']].columns.tolist()
            table = ax.table(cellText=table_data, colLabels=col_labels,
                             loc='center', cellLoc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 1.5)
        else:
            ax.text(0.5, 0.5, 'No ground truth events found', ha='center', va='center', fontsize=14)
        
        pdf.savefig(fig)
        plt.close(fig)
    
    logger.info(f"Report successfully generated at {output_pdf}")

def main():
    """
    Main entry point for report generation.
    Reads configuration and paths, then generates the PDF report.
    """
    # Setup logging
    from logging_setup import setup_logging
    setup_logging()
    
    # Default paths (can be overridden by config in a full implementation)
    metrics_path = 'data/processed/metrics.csv'
    flags_path = 'data/processed/flags.csv'
    gt_path = 'data/raw/ground_truth_events.csv'
    output_pdf = 'data/processed/report.pdf'
    
    # Validate output schema
    validate_output_data({
        'metrics_path': metrics_path,
        'flags_path': flags_path,
        'ground_truth_path': gt_path,
        'output_path': output_pdf
    })
    
    try:
        generate_report(metrics_path, flags_path, gt_path, output_pdf)
        logger.info("Report generation completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
