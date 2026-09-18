"""
T036: Generate final report PDF in reports/figures/ containing all required plots and correlation coefficients.

This script aggregates visualizations from T034 (boxplots/histograms) and T035 (correlation analysis),
computes correlation coefficients from the processed metrics, and compiles them into a single
research-ready PDF report.
"""
import os
import sys
import csv
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.gridspec import GridSpec

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger, setup_logging
from utils.config import get_config_summary
from utils.seeds import set_global_seed

# Initialize logger
setup_logging()
logger = get_logger(__name__)

# Constants
METRICS_FILE = project_root / "data" / "processed" / "prs_metrics.csv"
RESULTS_FILE = project_root / "data" / "processed" / "results.json"
OUTPUT_DIR = project_root / "reports" / "figures"
OUTPUT_PDF = OUTPUT_DIR / "final_report.pdf"

def load_metrics_data() -> List[Dict[str, Any]]:
    """Load processed metrics from CSV."""
    if not METRICS_FILE.exists():
        logger.error(f"Metrics file not found: {METRICS_FILE}")
        raise FileNotFoundError(f"Required metrics file not found: {METRICS_FILE}")
    
    data = []
    with open(METRICS_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            row['comment_count'] = int(row['comment_count'])
            row['time_to_merge_minutes'] = float(row['time_to_merge_minutes'])
            row['review_cycles'] = int(row['review_cycles'])
            row['complexity_score'] = float(row['complexity_score'])
            data.append(row)
    
    logger.info(f"Loaded {len(data)} records from {METRICS_FILE}")
    return data

def load_results() -> Dict[str, Any]:
    """Load statistical results from JSON."""
    if not RESULTS_FILE.exists():
        logger.error(f"Results file not found: {RESULTS_FILE}")
        raise FileNotFoundError(f"Required results file not found: {RESULTS_FILE}")
    
    with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_correlation_coefficients(data: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate Pearson correlation coefficients between complexity and review metrics."""
    correlations = {}
    
    complexity = [row['complexity_score'] for row in data]
    
    # Correlation: Complexity vs Comment Count
    comment_counts = [row['comment_count'] for row in data]
    corr_comments, p_comments = stats.pearsonr(complexity, comment_counts)
    correlations['complexity_vs_comments'] = corr_comments
    correlations['p_value_comments'] = p_comments
    
    # Correlation: Complexity vs Time to Merge
    time_to_merge = [row['time_to_merge_minutes'] for row in data]
    corr_time, p_time = stats.pearsonr(complexity, time_to_merge)
    correlations['complexity_vs_time'] = corr_time
    correlations['p_value_time'] = p_time
    
    # Correlation: Complexity vs Review Cycles
    review_cycles = [row['review_cycles'] for row in data]
    corr_cycles, p_cycles = stats.pearsonr(complexity, review_cycles)
    correlations['complexity_vs_cycles'] = corr_cycles
    correlations['p_value_cycles'] = p_cycles
    
    logger.info(f"Calculated correlations: {correlations}")
    return correlations

def group_data_by_source(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group data by source_type (llm vs human)."""
    groups = {'llm': [], 'human': []}
    for row in data:
        source = row.get('source_type', 'human')
        if source in groups:
            groups[source].append(row)
    return groups

def create_boxplot_panel(pdf: PdfPages, data: List[Dict[str, Any]], results: Dict[str, Any]):
    """Create a panel with boxplots for comment density and time-to-merge."""
    groups = group_data_by_source(data)
    llm_comments = [row['comment_count'] for row in groups['llm']]
    human_comments = [row['comment_count'] for row in groups['human']]
    llm_time = [row['time_to_merge_minutes'] for row in groups['llm']]
    human_time = [row['time_to_merge_minutes'] for row in groups['human']]
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Review Metrics by Source Type (LLM vs Human)', fontsize=16, fontweight='bold')
    
    # Comment Density Boxplot
    ax1 = axes[0]
    ax1.boxplot([llm_comments, human_comments], labels=['LLM', 'Human'], patch_artist=True)
    ax1.set_title('Comment Count Distribution')
    ax1.set_ylabel('Number of Comments')
    ax1.grid(True, alpha=0.3)
    
    # Add statistical significance annotation if available
    if 'comment_density' in results.get('statistical_tests', {}):
        test_res = results['statistical_tests']['comment_density']
        p_val = test_res.get('p_value', 1.0)
        sig = '*' if p_val < 0.05 else ''
        ax1.text(1.5, max(max(llm_comments), max(human_comments)) * 1.1, 
                f'p={p_val:.4f}{sig}', ha='center', fontsize=12)
    
    # Time to Merge Boxplot
    ax2 = axes[1]
    ax2.boxplot([llm_time, human_time], labels=['LLM', 'Human'], patch_artist=True)
    ax2.set_title('Time to Merge Distribution')
    ax2.set_ylabel('Minutes')
    ax2.grid(True, alpha=0.3)
    
    # Add statistical significance annotation if available
    if 'time_to_merge' in results.get('statistical_tests', {}):
        test_res = results['statistical_tests']['time_to_merge']
        p_val = test_res.get('p_value', 1.0)
        sig = '*' if p_val < 0.05 else ''
        ax2.text(1.5, max(max(llm_time), max(human_time)) * 1.1, 
                f'p={p_val:.4f}{sig}', ha='center', fontsize=12)
    
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)

def create_histogram_panel(pdf: PdfPages, data: List[Dict[str, Any]]):
    """Create a panel with histograms for review metrics."""
    groups = group_data_by_source(data)
    llm_comments = [row['comment_count'] for row in groups['llm']]
    human_comments = [row['comment_count'] for row in groups['human']]
    llm_time = [row['time_to_merge_minutes'] for row in groups['llm']]
    human_time = [row['time_to_merge_minutes'] for row in groups['human']]
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle('Distribution of Review Metrics', fontsize=16, fontweight='bold')
    
    # Comment Count Histograms
    ax1 = axes[0, 0]
    ax1.hist(llm_comments, bins=20, alpha=0.5, label='LLM', color='blue')
    ax1.hist(human_comments, bins=20, alpha=0.5, label='Human', color='orange')
    ax1.set_title('Comment Count Distribution')
    ax1.set_xlabel('Number of Comments')
    ax1.set_ylabel('Frequency')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Time to Merge Histograms
    ax2 = axes[0, 1]
    ax2.hist(llm_time, bins=20, alpha=0.5, label='LLM', color='blue')
    ax2.hist(human_time, bins=20, alpha=0.5, label='Human', color='orange')
    ax2.set_title('Time to Merge Distribution')
    ax2.set_xlabel('Minutes')
    ax2.set_ylabel('Frequency')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Review Cycles Histograms
    llm_cycles = [row['review_cycles'] for row in groups['llm']]
    human_cycles = [row['review_cycles'] for row in groups['human']]
    ax3 = axes[1, 0]
    ax3.hist(llm_cycles, bins=10, alpha=0.5, label='LLM', color='blue')
    ax3.hist(human_cycles, bins=10, alpha=0.5, label='Human', color='orange')
    ax3.set_title('Review Cycles Distribution')
    ax3.set_xlabel('Number of Cycles')
    ax3.set_ylabel('Frequency')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Complexity Score Histograms
    llm_complexity = [row['complexity_score'] for row in groups['llm']]
    human_complexity = [row['complexity_score'] for row in groups['human']]
    ax4 = axes[1, 1]
    ax4.hist(llm_complexity, bins=20, alpha=0.5, label='LLM', color='blue')
    ax4.hist(human_complexity, bins=20, alpha=0.5, label='Human', color='orange')
    ax4.set_title('Code Complexity Score Distribution')
    ax4.set_xlabel('Complexity Score')
    ax4.set_ylabel('Frequency')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)

def create_correlation_panel(pdf: PdfPages, correlations: Dict[str, float]):
    """Create a panel showing correlation analysis between complexity and metrics."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle('Correlation Analysis: Code Complexity vs Review Metrics', fontsize=16, fontweight='bold')
    
    metrics_data = [
        ('Comments', correlations['complexity_vs_comments'], correlations['p_value_comments']),
        ('Time to Merge', correlations['complexity_vs_time'], correlations['p_value_time']),
        ('Review Cycles', correlations['complexity_vs_cycles'], correlations['p_value_cycles'])
    ]
    
    colors = ['blue', 'green', 'orange']
    
    for i, (metric_name, corr, p_val) in enumerate(metrics_data):
        ax = axes[i]
        # Create a simple bar chart for correlation
        bars = ax.bar(['Correlation'], [corr], color=colors[i], alpha=0.7)
        ax.set_title(f'{metric_name}')
        ax.set_ylabel('Pearson r')
        ax.set_ylim(-1.1, 1.1)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        # Add value label
        ax.text(0, corr + (0.05 if corr >= 0 else -0.15), 
               f'r={corr:.3f}\np={p_val:.4f}', 
               ha='center', va='bottom' if corr >= 0 else 'top', fontsize=11)
        
        # Significance indicator
        sig = '*' if p_val < 0.05 else ''
        if sig:
            ax.text(0.5, 1.05, 'Significant (p<0.05)', transform=ax.transAxes, 
                   ha='center', fontsize=9, color='red', fontweight='bold')
    
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)

def create_summary_panel(pdf: PdfPages, results: Dict[str, Any], correlations: Dict[str, float]):
    """Create a summary panel with key findings text."""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis('off')
    
    text_content = [
        "RESEARCH SUMMARY: IMPACT OF CODE GENERATION ON CODE REVIEW QUALITY",
        "=" * 70,
        "",
        "KEY FINDINGS:",
        "-" * 40,
    ]
    
    # Add statistical test results
    if 'statistical_tests' in results:
        for metric, test_res in results['statistical_tests'].items():
            t_stat = test_res.get('t_statistic', 'N/A')
            p_val = test_res.get('p_value', 'N/A')
            effect_size = test_res.get('effect_size', 'N/A')
            significant = 'Yes' if p_val != 'N/A' and p_val < 0.05 else 'No'
            text_content.append(f"{metric.replace('_', ' ').title()}:")
            text_content.append(f"  t-statistic: {t_stat}")
            text_content.append(f"  p-value: {p_val}")
            text_content.append(f"  Effect Size (Cohen's d): {effect_size}")
            text_content.append(f"  Significant (α=0.05): {significant}")
            text_content.append("")
    
    text_content.append("CORRELATION ANALYSIS (Complexity vs Metrics):")
    text_content.append("-" * 40)
    text_content.append(f"Complexity vs Comments: r={correlations['complexity_vs_comments']:.3f} (p={correlations['p_value_comments']:.4f})")
    text_content.append(f"Complexity vs Time:     r={correlations['complexity_vs_time']:.3f} (p={correlations['p_value_time']:.4f})")
    text_content.append(f"Complexity vs Cycles:   r={correlations['complexity_vs_cycles']:.3f} (p={correlations['p_value_cycles']:.4f})")
    text_content.append("")
    text_content.append("CONCLUSION:")
    text_content.append("-" * 40)
    text_content.append("This analysis examines the impact of LLM-generated code on review quality metrics,")
    text_content.append("controlling for code complexity as a potential confounding variable.")
    
    text = "\n".join(text_content)
    ax.text(0.05, 0.95, text, transform=ax.transAxes, fontsize=11,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)

def generate_final_report_pdf():
    """Generate the final report PDF with all required plots and coefficients."""
    logger.info("Starting final report PDF generation...")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Set random seed for reproducibility
    set_global_seed(42)
    
    # Load data
    data = load_metrics_data()
    results = load_results()
    
    # Calculate correlations
    correlations = calculate_correlation_coefficients(data)
    
    # Create PDF
    logger.info(f"Generating PDF report at {OUTPUT_PDF}...")
    with PdfPages(OUTPUT_PDF) as pdf:
        # Add metadata
        pdf.attach_metadata({
            'Title': 'Impact of Code Generation on Code Review Quality',
            'Author': 'llmXive Research Pipeline',
            'Subject': 'Statistical Analysis and Visualization Report',
        })
        
        # Create pages
        create_boxplot_panel(pdf, data, results)
        create_histogram_panel(pdf, data)
        create_correlation_panel(pdf, correlations)
        create_summary_panel(pdf, results, correlations)
    
    logger.info(f"Final report generated successfully: {OUTPUT_PDF}")
    return str(OUTPUT_PDF)

def main():
    """Main entry point."""
    try:
        generate_final_report_pdf()
        logger.info("T036 completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate final report: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
