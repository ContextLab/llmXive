"""
T050 Implementation: Generate a high-resolution "Jagged Line" histogram for the worst-case scenario.

This script loads the worst-case scenario identified in T049, retrieves the corresponding
p-values, and generates a detailed histogram with a large number of bins to reveal
the "jaggedness" and deviation from the theoretical uniform distribution.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORST_CASE_FILE = PROJECT_ROOT / "data" / "results" / "worst_case_summary.json"
PVALUES_DIR = PROJECT_ROOT / "data" / "results"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "plots"
OUTPUT_FILE = OUTPUT_DIR / "jagged_line_worst_case_detail.png"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_worst_case_scenario() -> Dict[str, Any]:
    """Load the worst-case scenario summary from T049."""
    if not WORST_CASE_FILE.exists():
        raise FileNotFoundError(
            f"Worst case summary file not found at {WORST_CASE_FILE}. "
            "Please ensure T049 has been completed successfully."
        )
    
    with open(WORST_CASE_FILE, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded worst-case scenario: seed={data.get('seed')}, "
                f"n={data.get('n')}, p={data.get('p')}, "
                f"rho={data.get('rho')}, dist={data.get('distribution_type')}, "
                f"ks_stat={data.get('ks_stat')}")
    return data

def load_pvalues_for_seed(seed: int) -> np.ndarray:
    """Load p-values for a specific seed from the results CSV."""
    pvalues_file = PVALUES_DIR / f"pvalues_{seed}.csv"
    
    if not pvalues_file.exists():
        raise FileNotFoundError(
            f"P-values file not found for seed {seed} at {pvalues_file}. "
            "Please ensure T022c has been completed successfully."
        )
    
    pvalues = []
    with open(pvalues_file, 'r') as f:
        # Skip header
        next(f)
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 2:
                try:
                    p_val = float(parts[1])
                    pvalues.append(p_val)
                except ValueError:
                    continue
    
    if not pvalues:
        raise ValueError(f"No valid p-values found in {pvalues_file}")
    
    return np.array(pvalues)

def generate_jagged_line_plot(
    pvalues: np.ndarray,
    worst_case_params: Dict[str, Any],
    output_path: Path,
    num_bins: int = 100
) -> None:
    """
    Generate a high-resolution histogram of p-values to reveal jaggedness.
    
    Args:
        pvalues: Array of p-values from the worst-case scenario.
        worst_case_params: Dictionary containing scenario parameters.
        output_path: Path to save the plot.
        num_bins: Number of bins for the histogram (default 100 for high resolution).
    """
    logger.info(f"Generating jagged line plot with {num_bins} bins...")
    
    fig = plt.figure(figsize=(14, 10))
    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.1)
    
    # Main plot: Histogram with theoretical uniform line
    ax1 = fig.add_subplot(gs[0])
    
    # Calculate histogram
    counts, bin_edges = np.histogram(pvalues, bins=num_bins, range=(0, 1))
    bin_widths = np.diff(bin_edges)
    bin_centers = bin_edges[:-1] + bin_widths / 2
    
    # Theoretical uniform height (total count / num_bins)
    theoretical_height = len(pvalues) / num_bins
    
    # Plot histogram as bars (unsmoothed)
    ax1.bar(bin_centers, counts, width=bin_widths, 
            align='center', alpha=0.7, color='steelblue', 
            edgecolor='black', linewidth=0.5, label='Observed (Jagged)')
    
    # Plot theoretical uniform line
    ax1.axhline(y=theoretical_height, color='red', linestyle='--', 
               linewidth=2, label=f'Theoretical Uniform (y={theoretical_height:.1f})')
    
    # Highlight deviations
    deviations = counts - theoretical_height
    for i, (center, count, dev) in enumerate(zip(bin_centers, counts, deviations)):
        if abs(dev) > theoretical_height * 0.5:  # Significant deviation
            color = 'orange' if dev > 0 else 'purple'
            ax1.axvline(x=center, ymin=0, ymax=count/len(pvalues), 
                       color=color, alpha=0.3, linewidth=1)
    
    ax1.set_xlabel('p-value', fontsize=12)
    ax1.set_ylabel('Frequency', fontsize=12)
    ax1.set_title(f'Jagged Line: High-Dimensional p-value Distribution\n'
                 f'ρ={worst_case_params.get("rho", "N/A")}, '
                 f'p={worst_case_params.get("p", "N/A")}, '
                 f'n={worst_case_params.get("n", "N/A")}, '
                 f'dist={worst_case_params.get("distribution_type", "N/A")}',
                 fontsize=14, fontweight='bold')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3, linestyle=':')
    ax1.set_xlim(0, 1)
    
    # Annotation with KS statistic
    ks_stat = worst_case_params.get('ks_stat', 0)
    annotation_text = (f"KS Statistic: {ks_stat:.4f}\n"
                     f"Deviation from Uniform: {abs(ks_stat - 0.0):.4f}")
    ax1.annotate(annotation_text, 
                xy=(0.95, 0.95), xycoords='axes fraction',
                fontsize=11, verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="black", alpha=0.8))
    
    # Bottom plot: Residuals (Observed - Theoretical)
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax2.bar(bin_centers, deviations, width=bin_widths, 
            align='center', alpha=0.7, color='darkred', 
            edgecolor='black', linewidth=0.5)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax2.set_xlabel('p-value', fontsize=12)
    ax2.set_ylabel('Deviation from Expected', fontsize=12)
    ax2.set_title('Deviation from Theoretical Uniform Distribution', 
                 fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle=':')
    ax2.set_xlim(0, 1)
    
    # Add a text box explaining the "mess"
    explanation_text = (
        "Feynman's 'Jagged Line':\n"
        "Standard theory assumes smooth uniform distribution.\n"
        "High-dimensional correlation creates 'jagged' noise.\n"
        "This plot reveals the breakdown of the 'ritual'."
    )
    fig.text(0.02, 0.02, explanation_text, fontsize=10, 
            verticalalignment='bottom', 
            bbox=dict(boxstyle="round,pad=0.5", fc="lightyellow", ec="orange", alpha=0.8))
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    plt.close(fig)
    
    logger.info(f"Jagged line plot saved to {output_path}")

def main():
    """Main entry point for T050."""
    try:
        # Load worst-case scenario
        worst_case = load_worst_case_scenario()
        
        # Load p-values for the worst-case seed
        seed = worst_case.get('seed')
        pvalues = load_pvalues_for_seed(seed)
        
        logger.info(f"Loaded {len(pvalues)} p-values for seed {seed}")
        
        # Generate the plot with high resolution (100+ bins)
        generate_jagged_line_plot(
            pvalues=pvalues,
            worst_case_params=worst_case,
            output_path=OUTPUT_FILE,
            num_bins=100  # High resolution to show jaggedness
        )
        
        # Verify output exists
        if OUTPUT_FILE.exists():
            logger.info(f"SUCCESS: T050 artifact created at {OUTPUT_FILE}")
            return 0
        else:
            logger.error(f"FAILED: Output file {OUTPUT_FILE} was not created")
            return 1
            
    except Exception as e:
        logger.error(f"ERROR in T050 execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
