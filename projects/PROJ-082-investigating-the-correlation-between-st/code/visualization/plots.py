import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import seaborn as sns

from utils.logger import get_logger
from utils.config import get_figure_path, ensure_directory

logger = get_logger(__name__)


def load_analysis_results(json_path: Path) -> Dict[str, Any]:
    """Load the meta-analysis results JSON."""
    if not json_path.exists():
        raise FileNotFoundError(f"Analysis results file not found: {json_path}")
    
    with open(json_path, 'r') as f:
        return json.load(f)


def load_effect_sizes_for_plotting(json_path: Path) -> Tuple[List[float], List[float], List[str]]:
    """Extract effect sizes, standard errors, and labels for plotting."""
    data = load_analysis_results(json_path)
    
    effects = []
    ses = []
    labels = []
    
    # Handle both narrative and quantitative results
    if 'quantitative_results' in data and data['quantitative_results']:
        studies = data['quantitative_results'].get('studies', [])
        for study in studies:
            if 'effect_size_r' in study and 'se' in study:
                effects.append(study['effect_size_r'])
                ses.append(study['se'])
                labels.append(study.get('study_id', f"Study_{len(effects)}"))
    
    return effects, ses, labels


def create_forest_plot(
    effects: List[float],
    ses: List[float],
    labels: List[str],
    weighted_mean_r: float,
    output_path: Path
) -> None:
    """
    Create a forest plot with summary diamond aligned to weighted_mean_r.
    
    Args:
        effects: List of effect sizes (r values)
        ses: List of standard errors
        labels: List of study labels
        weighted_mean_r: The pooled effect size for the summary diamond
        output_path: Path to save the plot
    """
    if not effects:
        logger.warning("No effect sizes provided for forest plot. Creating empty plot.")
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "No studies available for forest plot", 
               transform=ax.transAxes, ha='center', va='center')
        ax.set_xlim(-1, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ensure_directory(output_path.parent)
        fig.savefig(output_path, dpi=150, optimize=True, bbox_inches='tight')
        plt.close(fig)
        return

    n = len(effects)
    fig, ax = plt.subplots(figsize=(12, max(6, n * 0.4 + 2)))
    
    # Plot individual studies
    y_positions = range(n)
    errors = [[e - se, e + se] for e, se in zip(effects, ses)]
    
    ax.errorbar(effects, y_positions, xerr=ses, fmt='o', color='steelblue', 
               ecolor='gray', capsize=3, markersize=6, label='Individual Studies')
    
    # Plot summary diamond at weighted_mean_r
    diamond_width = 2 * 0.1  # Approximate 95% CI width for summary
    ax.scatter([weighted_mean_r], [-0.5], marker='D', s=200, color='darkred', 
              label=f'Summary (r={weighted_mean_r:.3f})', zorder=5)
    
    # Draw diamond shape manually for better control
    diamond = mpatches.Polygon(
        [[weighted_mean_r - diamond_width/2, -0.5 - diamond_width/4],
         [weighted_mean_r, -0.5 - diamond_width/2],
         [weighted_mean_r + diamond_width/2, -0.5 - diamond_width/4],
         [weighted_mean_r, -0.5 + diamond_width/2]],
        closed=True,
        color='darkred',
        alpha=0.6,
        label='Pooled Effect'
    )
    ax.add_patch(diamond)
    
    # Reference line at r=0
    ax.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.7)
    
    # Reference line at pooled effect
    ax.axvline(x=weighted_mean_r, color='darkred', linestyle=':', linewidth=1, alpha=0.7)
    
    # Labels and formatting
    ax.set_xlabel('Effect Size (Correlation Coefficient r)', fontsize=12)
    ax.set_ylabel('Studies', fontsize=12)
    ax.set_title('Forest Plot: Brain Connectivity vs Music Preferences', fontsize=14, fontweight='bold')
    
    # Y-axis labels
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels)
    
    # X-axis limits
    ax.set_xlim(-1.1, 1.1)
    
    # Add legend
    ax.legend(loc='lower right', fontsize=10)
    
    # Grid
    ax.grid(True, alpha=0.3, axis='x')
    
    ensure_directory(output_path.parent)
    fig.savefig(output_path, dpi=150, optimize=True, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Forest plot saved to {output_path}")


def create_funnel_plot(
    effects: List[float],
    ses: List[float],
    pooled_effect: float,
    output_path: Path
) -> None:
    """
    Create a funnel plot (standard error vs effect size) with symmetry line at pooled effect.
    
    Args:
        effects: List of effect sizes
        ses: List of standard errors
        pooled_effect: The pooled effect size for the symmetry line
        output_path: Path to save the plot
    """
    if not effects:
        logger.warning("No effect sizes provided for funnel plot. Creating empty plot.")
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "No studies available for funnel plot", 
               transform=ax.transAxes, ha='center', va='center')
        ax.set_xlim(-1, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ensure_directory(output_path.parent)
        fig.savefig(output_path, dpi=150, optimize=True, bbox_inches='tight')
        plt.close(fig)
        return

    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Scatter plot of effect size vs standard error
    ax.scatter(effects, ses, color='steelblue', alpha=0.6, s=60, edgecolors='black', linewidth=0.5)
    
    # Symmetry line at pooled effect
    ax.axvline(x=pooled_effect, color='darkred', linestyle='--', linewidth=2, 
              label=f'Symmetry Line (r={pooled_effect:.3f})')
    
    # Pseudo 95% confidence limits (funnel boundaries)
    se_max = max(ses) * 1.1
    se_min = min(ses) * 0.9 if min(ses) > 0 else 0.001
    
    se_range = np.linspace(se_min, se_max, 100)
    ax.fill_betweenx(se_range, 
                    pooled_effect - 1.96 * se_range, 
                    pooled_effect + 1.96 * se_range, 
                    color='gray', alpha=0.2, label='95% CI Funnel')
    
    ax.set_xlabel('Effect Size (Correlation Coefficient r)', fontsize=12)
    ax.set_ylabel('Standard Error', fontsize=12)
    ax.set_title('Funnel Plot: Assessing Publication Bias', fontsize=14, fontweight='bold')
    
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Invert Y-axis so smaller SE is at top (standard funnel plot convention)
    ax.invert_yaxis()
    
    ensure_directory(output_path.parent)
    fig.savefig(output_path, dpi=150, optimize=True, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Funnel plot saved to {output_path}")


def create_correlation_summary_plot(
    effects: List[float],
    labels: List[str],
    output_path: Path
) -> None:
    """
    Create a correlation summary plot showing the distribution of effect sizes.
    
    Args:
        effects: List of effect sizes
        labels: List of study labels
        output_path: Path to save the plot
    """
    if not effects:
        logger.warning("No effect sizes provided for correlation summary plot. Creating empty plot.")
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "No studies available for correlation summary", 
               transform=ax.transAxes, ha='center', va='center')
        ax.set_xlim(-1, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ensure_directory(output_path.parent)
        fig.savefig(output_path, dpi=150, optimize=True, bbox_inches='tight')
        plt.close(fig)
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Create a horizontal bar chart of effect sizes
    y_positions = range(len(effects))
    colors = ['steelblue' if e >= 0 else 'salmon' for e in effects]
    
    bars = ax.barh(y_positions, effects, color=colors, edgecolor='black', alpha=0.7)
    
    # Add value labels on bars
    for i, (bar, effect) in enumerate(zip(bars, effects)):
        x_val = bar.get_width() + (0.01 if effect >= 0 else -0.01)
        ax.text(x_val, i, f'{effect:.3f}', va='center', fontsize=9, fontweight='bold')
    
    # Reference line at zero
    ax.axvline(x=0, color='black', linestyle='-', linewidth=1)
    
    # Reference line at mean
    mean_effect = np.mean(effects)
    ax.axvline(x=mean_effect, color='darkred', linestyle='--', linewidth=2, 
              label=f'Mean r = {mean_effect:.3f}')
    
    ax.set_xlabel('Effect Size (Correlation Coefficient r)', fontsize=12)
    ax.set_ylabel('Study', fontsize=12)
    ax.set_title('Correlation Summary: Effect Sizes by Study', fontsize=14, fontweight='bold')
    
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels)
    
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3, axis='x')
    
    ensure_directory(output_path.parent)
    fig.savefig(output_path, dpi=150, optimize=True, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Correlation summary plot saved to {output_path}")


def run_visualization_analysis(
    input_json_path: Path,
    output_dir: Path,
    weighted_mean_r: Optional[float] = None,
    pooled_effect: Optional[float] = None
) -> Dict[str, str]:
    """
    Run all visualization analyses and save plots to output directory.
    
    Args:
        input_json_path: Path to the meta-analysis results JSON
        output_dir: Directory to save generated plots
        weighted_mean_r: Optional override for weighted mean (if not in JSON)
        pooled_effect: Optional override for pooled effect (if not in JSON)
        
    Returns:
        Dictionary mapping plot type to output file path
    """
    ensure_directory(output_dir)
    
    results = {
        'forest_plot': str(output_dir / 'forest_plot.png'),
        'funnel_plot': str(output_dir / 'funnel_plot.png'),
        'correlation_summary': str(output_dir / 'correlation_summary.png')
    }
    
    # Load data
    effects, ses, labels = load_effect_sizes_for_plotting(input_json_path)
    
    # Determine pooled effect
    if pooled_effect is None:
        data = load_analysis_results(input_json_path)
        if 'quantitative_results' in data and data['quantitative_results']:
            pooled_effect = data['quantitative_results'].get('weighted_mean_r', 0.0)
        else:
            pooled_effect = np.mean(effects) if effects else 0.0
    
    if weighted_mean_r is None:
        weighted_mean_r = pooled_effect
    
    # Generate plots
    if effects:
        create_forest_plot(effects, ses, labels, weighted_mean_r, 
                         output_dir / 'forest_plot.png')
        create_funnel_plot(effects, ses, pooled_effect, 
                         output_dir / 'funnel_plot.png')
        create_correlation_summary_plot(effects, labels, 
                                      output_dir / 'correlation_summary.png')
    else:
        # Create empty plots with messages
        create_forest_plot([], [], [], 0.0, output_dir / 'forest_plot.png')
        create_funnel_plot([], [], 0.0, output_dir / 'funnel_plot.png')
        create_correlation_summary_plot([], [], output_dir / 'correlation_summary.png')
    
    logger.info(f"All visualization plots saved to {output_dir}")
    return results


def main():
    """Main entry point for running visualization analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate visualization plots for meta-analysis')
    parser.add_argument('--input', '-i', type=str, required=True,
                      help='Path to input JSON file with analysis results')
    parser.add_argument('--output', '-o', type=str, default='data/derived/plots',
                      help='Output directory for generated plots')
    parser.add_argument('--weighted-mean', '-w', type=float, default=None,
                      help='Override weighted mean effect size')
    parser.add_argument('--pooled-effect', '-p', type=float, default=None,
                      help='Override pooled effect size')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    try:
        results = run_visualization_analysis(
            input_path,
            output_path,
            weighted_mean_r=args.weighted_mean,
            pooled_effect=args.pooled_effect
        )
        
        print("Visualization completed successfully!")
        for plot_type, file_path in results.items():
            print(f"  {plot_type}: {file_path}")
            
    except Exception as e:
        logger.error(f"Visualization analysis failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()