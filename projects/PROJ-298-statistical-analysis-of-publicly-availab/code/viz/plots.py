"""
Visualization module for generating multi-panel decomposition plots with confidence intervals.
Uses templates.py to inject mandatory limitation headers per FR-011.
"""
import os
import json
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Import from existing API surface
from viz.templates import create_plot_with_limitation, get_limitation_header, get_limitation_footer


def load_processed_data() -> Dict[str, Any]:
    """Load processed monthly frequency data."""
    processed_path = PROJECT_ROOT / "data" / "processed" / "monthly_tag_frequencies.json"
    if not processed_path.exists():
        raise FileNotFoundError(f"Processed data not found at {processed_path}")
    
    with open(processed_path, 'r') as f:
        return json.load(f)


def load_decomposition_results() -> Dict[str, Any]:
    """Load decomposition analysis results."""
    results_path = PROJECT_ROOT / "data" / "processed" / "decomposition_results.json"
    if not results_path.exists():
        raise FileNotFoundError(f"Decomposition results not found at {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)


def load_trend_results() -> Dict[str, Any]:
    """Load trend analysis results for slope information."""
    results_path = PROJECT_ROOT / "data" / "processed" / "trend_results.json"
    if not results_path.exists():
        raise FileNotFoundError(f"Trend results not found at {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)


def create_decomposition_plot(
    tag_name: str,
    observed: List[float],
    trend: List[float],
    seasonal: List[float],
    residual: List[float],
    months: List[str],
    confidence_interval: Optional[Tuple[List[float], List[float]]] = None,
    ljung_box_p: Optional[float] = None,
    rayleigh_p: Optional[float] = None,
    output_path: Optional[Path] = None
) -> None:
    """
    Create a multi-panel decomposition plot with confidence intervals.
    
    Args:
        tag_name: The technology tag name
        observed: Observed time series values
        trend: Trend component values
        seasonal: Seasonal component values
        residual: Residual component values
        months: List of month labels (YYYY-MM format)
        confidence_interval: Optional tuple of (lower_bounds, upper_bounds) for confidence intervals
        ljung_box_p: P-value from Ljung-Box test
        rayleigh_p: P-value from Rayleigh test
        output_path: Path to save the plot (optional)
    """
    n_points = len(observed)
    x = np.arange(n_points)
    
    # Create figure with 4 rows
    fig = plt.figure(figsize=(14, 12))
    gs = GridSpec(4, 1, figure=fig, height_ratios=[3, 2, 2, 2], hspace=0.3)
    
    # Panel 1: Observed with confidence interval
    ax1 = fig.add_subplot(gs[0])
    ax1.plot(x, observed, 'b-', linewidth=1.5, label='Observed')
    ax1.set_ylabel('Frequency', fontsize=11)
    ax1.set_title(f'Tag: {tag_name} - Time Series Decomposition', fontsize=14, fontweight='bold')
    
    if confidence_interval is not None:
        lower, upper = confidence_interval
        ax1.fill_between(x, lower, upper, alpha=0.2, color='blue', label='95% CI')
        ax1.legend(loc='upper right', fontsize=9)
    
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(labelsize=9)
    
    # Panel 2: Trend component
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax2.plot(x, trend, 'r-', linewidth=2, label='Trend')
    ax2.set_ylabel('Trend', fontsize=11)
    ax2.legend(loc='upper right', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(labelsize=9)
    
    # Panel 3: Seasonal component
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    ax3.plot(x, seasonal, 'g-', linewidth=1.5, label='Seasonal')
    ax3.set_ylabel('Seasonal', fontsize=11)
    ax3.legend(loc='upper right', fontsize=9)
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(labelsize=9)
    
    # Panel 4: Residual component
    ax4 = fig.add_subplot(gs[3], sharex=ax1)
    ax4.plot(x, residual, 'm-', linewidth=1, label='Residual')
    ax4.set_ylabel('Residual', fontsize=11)
    ax4.set_xlabel('Time (Months)', fontsize=11)
    
    # Add test results as text
    stats_text = []
    if ljung_box_p is not None:
        stats_text.append(f"Ljung-Box p-value: {ljung_box_p:.4f}")
    if rayleigh_p is not None:
        stats_text.append(f"Rayleigh p-value: {rayleigh_p:.4f}")
    
    if stats_text:
        stats_str = '\n'.join(stats_text)
        ax4.text(0.02, 0.95, stats_str, transform=ax4.transAxes, 
                fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    ax4.legend(loc='upper right', fontsize=9)
    ax4.grid(True, alpha=0.3)
    ax4.tick_params(labelsize=9)
    
    # Set x-axis labels only on the bottom plot
    for i, month in enumerate(months):
        if i % max(1, len(months) // 6) == 0:  # Show ~6 labels
            ax4.set_xticks([i])
            ax4.set_xticklabels([month], rotation=45, ha='right', fontsize=9)
    
    # Apply limitation header/footer using templates module
    fig = create_plot_with_limitation(fig, 
                                    title=f"Decomposition Analysis: {tag_name}",
                                    footer_text="See FR-011 for data limitations and methodology constraints.")
    
    # Save or show
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
    else:
        plt.show()


def generate_all_decomposition_plots(
    output_dir: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Generate decomposition plots for all tags in the decomposition results.
    
    Args:
        output_dir: Directory to save plots (default: data/figures/decomposition)
        
    Returns:
        List of dictionaries with plot metadata
    """
    if output_dir is None:
        output_dir = PROJECT_ROOT / "data" / "figures" / "decomposition"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    try:
        decomposition_results = load_decomposition_results()
    except FileNotFoundError as e:
        raise RuntimeError(f"Cannot generate plots: {e}")
    
    if "results" not in decomposition_results:
        raise ValueError("Invalid decomposition results format: missing 'results' key")
    
    plots_metadata = []
    
    for tag_data in decomposition_results["results"]:
        tag_name = tag_data.get("tag")
        if not tag_name:
            continue
        
        # Extract time series components
        observed = tag_data.get("observed", [])
        trend = tag_data.get("trend", [])
        seasonal = tag_data.get("seasonal", [])
        residual = tag_data.get("residual", [])
        months = tag_data.get("months", [])
        
        if not all([observed, trend, seasonal, residual, months]):
            print(f"Skipping {tag_name}: missing required data components")
            continue
        
        # Get confidence intervals if available
        confidence_interval = None
        if "confidence_interval" in tag_data:
            ci = tag_data["confidence_interval"]
            confidence_interval = (ci.get("lower", []), ci.get("upper", []))
        
        # Get test statistics
        ljung_box_p = tag_data.get("ljung_box", {}).get("p_value")
        rayleigh_p = tag_data.get("rayleigh_test", {}).get("p_value")
        
        # Generate plot
        output_path = output_dir / f"{tag_name}_decomposition.png"
        
        try:
            create_decomposition_plot(
                tag_name=tag_name,
                observed=observed,
                trend=trend,
                seasonal=seasonal,
                residual=residual,
                months=months,
                confidence_interval=confidence_interval,
                ljung_box_p=ljung_box_p,
                rayleigh_p=rayleigh_p,
                output_path=output_path
            )
            
            plots_metadata.append({
                "tag": tag_name,
                "output_file": str(output_path.relative_to(PROJECT_ROOT)),
                "status": "success"
            })
            print(f"Generated plot for {tag_name}: {output_path}")
            
        except Exception as e:
            print(f"Error generating plot for {tag_name}: {e}")
            plots_metadata.append({
                "tag": tag_name,
                "output_file": None,
                "status": "failed",
                "error": str(e)
            })
    
    return plots_metadata


def create_comparison_plot(
    tags: List[str],
    trend_slopes: Dict[str, float],
    output_path: Optional[Path] = None
) -> None:
    """
    Create a comparison bar plot of trend slopes for multiple tags.
    
    Args:
        tags: List of tag names to compare
        trend_slopes: Dictionary mapping tag names to their trend slopes
        output_path: Path to save the plot (optional)
    """
    valid_tags = [tag for tag in tags if tag in trend_slopes]
    if not valid_tags:
        raise ValueError("No valid tags found in trend_slopes")
    
    slopes = [trend_slopes[tag] for tag in valid_tags]
    colors = ['green' if s > 0 else 'red' if s < 0 else 'gray' for s in slopes]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(valid_tags, slopes, color=colors, alpha=0.7)
    
    ax.set_xlabel('Technology Tag', fontsize=11)
    ax.set_ylabel('Theil-Sen Slope (Monthly Change)', fontsize=11)
    ax.set_title('Technology Growth/Decline Comparison', fontsize=14, fontweight='bold')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    # Add value labels on bars
    for bar, slope in zip(bars, slopes):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{slope:.4f}',
               ha='center', va='bottom' if height > 0 else 'top',
               fontsize=9)
    
    # Apply limitation header/footer
    fig = create_plot_with_limitation(fig,
                                    title="Technology Trend Comparison",
                                    footer_text="See FR-011 for data limitations and methodology constraints.")
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
    else:
        plt.show()


def main():
    """Main entry point for generating decomposition plots."""
    print("Starting decomposition plot generation...")
    
    try:
        metadata = generate_all_decomposition_plots()
        
        # Generate summary
        success_count = sum(1 for m in metadata if m["status"] == "success")
        fail_count = sum(1 for m in metadata if m["status"] == "failed")
        
        print(f"\nGeneration complete: {success_count} successful, {fail_count} failed")
        
        if fail_count > 0:
            print("\nFailed tags:")
            for m in metadata:
                if m["status"] == "failed":
                    print(f"  - {m['tag']}: {m.get('error', 'Unknown error')}")
        
        return metadata
        
    except Exception as e:
        print(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()