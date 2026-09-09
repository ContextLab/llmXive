"""
Reporting module for generating timescale-accuracy curves and comparison plots.

Implements T017: Generate timescale-accuracy curves (MAE vs. Duration) with uncertainty bands.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class PlotConfig:
    """Configuration for plot generation."""
    output_dir: str = "data/processed/figures"
    style: str = "seaborn-v0_8-whitegrid"
    dpi: int = 300
    figsize: Tuple[int, int] = (10, 6)
    font_size: int = 12
    color_palette: str = "muted"
    
    # Uncertainty band settings
    uncertainty_method: str = "std"  # 'std' or 'ci'
    ci_level: float = 0.95
    
    # Linearity threshold for reference
    r2_threshold: float = 0.95

def load_diffusion_results(results_path: str) -> List[Dict[str, Any]]:
    """
    Load diffusion analysis results from JSON files.
    
    Args:
        results_path: Path to directory containing diffusion_results_*.json files
        
    Returns:
        List of dictionaries containing simulation results
    """
    results = []
    results_dir = Path(results_path)
    
    if not results_dir.exists():
        logger.warning(f"Results directory not found: {results_path}")
        return results
    
    json_files = list(results_dir.glob("diffusion_results_*.json"))
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    results.extend(data)
                else:
                    results.append(data)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load {json_file}: {e}")
    
    return results

def calculate_uncertainty_bands(
    durations: np.ndarray,
    maes: np.ndarray,
    method: str = "std",
    ci_level: float = 0.95
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate uncertainty bands for MAE vs Duration plot.
    
    Args:
        durations: Array of simulation durations (ns)
        maes: Array of corresponding MAE values
        method: 'std' for standard deviation bands, 'ci' for confidence intervals
        ci_level: Confidence level for CI calculation (default 0.95)
        
    Returns:
        Tuple of (lower_bound, upper_bound) arrays
    """
    if len(durations) != len(maes):
        raise ValueError("durations and maes must have the same length")
    
    if len(durations) < 2:
        logger.warning("Insufficient data points for uncertainty bands")
        return maes, maes
    
    # Group by duration to calculate statistics
    unique_durations = np.unique(durations)
    lower_bounds = np.zeros_like(durations)
    upper_bounds = np.zeros_like(durations)
    
    for duration in unique_durations:
        mask = durations == duration
        maes_at_duration = maes[mask]
        
        if len(maes_at_duration) == 1:
            # Single point, use as is
            lower_bounds[mask] = maes_at_duration[0]
            upper_bounds[mask] = maes_at_duration[0]
        else:
            if method == "std":
                mean_val = np.mean(maes_at_duration)
                std_val = np.std(maes_at_duration, ddof=1)
                lower_bounds[mask] = mean_val - std_val
                upper_bounds[mask] = mean_val + std_val
            elif method == "ci":
                mean_val = np.mean(maes_at_duration)
                std_err = stats.sem(maes_at_duration)
                ci = stats.t.interval(ci_level, len(maes_at_duration)-1, loc=mean_val, scale=std_err)
                lower_bounds[mask] = ci[0]
                upper_bounds[mask] = ci[1]
            else:
                raise ValueError(f"Unknown uncertainty method: {method}")
    
    return lower_bounds, upper_bounds

def generate_timescale_accuracy_plot(
    results: List[Dict[str, Any]],
    config: Optional[PlotConfig] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Generate timescale-accuracy curve (MAE vs Duration) with uncertainty bands.
    
    Args:
        results: List of diffusion analysis results
        config: Plot configuration
        output_path: Optional custom output path
        
    Returns:
        Path to generated plot file
    """
    if config is None:
        config = PlotConfig()
    
    # Apply seaborn style
    sns.set_style(config.style)
    plt.rcParams['font.size'] = config.font_size
    
    # Extract data
    durations = []
    maes = []
    solvents = []
    r2_values = []
    
    for result in results:
        # Extract duration from simulation config or metadata
        duration = result.get('duration_ns')
        if duration is None:
            # Try to extract from analysis metadata
            duration = result.get('analysis', {}).get('duration_ns')
        
        # Extract MAE
        mae = result.get('mae')
        if mae is None:
            # Calculate MAE if not present
            predicted = result.get('diffusion_coefficient')
            solvent = result.get('solvent', 'unknown')
            # We would need NIST refs here, but for plotting we assume MAE is pre-calculated
            continue
        
        # Extract solvent
        solvent = result.get('solvent', 'unknown')
        
        # Extract R2 for filtering
        r2 = result.get('r_squared', 0.0)
        
        if duration is not None and mae is not None:
            durations.append(duration)
            maes.append(mae)
            solvents.append(solvent)
            r2_values.append(r2)
    
    if not durations:
        logger.warning("No valid data points found for plotting")
        # Create empty plot
        fig, ax = plt.subplots(figsize=config.figsize)
        ax.set_xlabel("Simulation Duration (ns)")
        ax.set_ylabel("Mean Absolute Error (m²/s)")
        ax.set_title("Timescale-Accuracy Curve (No Data Available)")
        ax.axhline(y=0, color='r', linestyle='--', alpha=0.5)
        
        # Ensure output directory exists
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if output_path is None:
            output_path = str(output_dir / "timescale_accuracy_empty.png")
        
        plt.savefig(output_path, dpi=config.dpi, bbox_inches='tight')
        plt.close()
        return output_path
    
    # Convert to numpy arrays
    durations = np.array(durations)
    maes = np.array(maes)
    r2_values = np.array(r2_values)
    
    # Filter for linear fits only (R² >= threshold)
    valid_mask = r2_values >= config.r2_threshold
    if not np.all(valid_mask):
        logger.info(f"Filtering {np.sum(~valid_mask)} points with R² < {config.r2_threshold}")
    
    durations_valid = durations[valid_mask]
    maes_valid = maes[valid_mask]
    
    # Calculate uncertainty bands
    lower, upper = calculate_uncertainty_bands(
        durations_valid,
        maes_valid,
        method=config.uncertainty_method,
        ci_level=config.ci_level
    )
    
    # Sort by duration for smooth plotting
    sort_idx = np.argsort(durations_valid)
    durations_sorted = durations_valid[sort_idx]
    maes_sorted = maes_valid[sort_idx]
    lower_sorted = lower[sort_idx]
    upper_sorted = upper[sort_idx]
    
    # Create figure
    fig, ax = plt.subplots(figsize=config.figsize)
    
    # Plot uncertainty band
    ax.fill_between(
        durations_sorted,
        lower_sorted,
        upper_sorted,
        alpha=0.3,
        color='gray',
        label='Uncertainty Band'
    )
    
    # Plot mean trend
    ax.plot(
        durations_sorted,
        maes_sorted,
        'o-',
        color='blue',
        linewidth=2,
        markersize=8,
        label='Mean MAE'
    )
    
    # Add individual points
    for solvent in sorted(set(solvents)):
        solvent_mask = [s == solvent for s in solvents]
        if any(solvent_mask):
            d_sol = durations[solvent_mask]
            m_sol = maes[solvent_mask]
            ax.scatter(
                d_sol,
                m_sol,
                alpha=0.6,
                label=solvent.capitalize(),
                edgecolors='black',
                linewidth=0.5
            )
    
    # Add reference line for convergence (optional)
    if maes_valid.size > 0:
        min_mae = np.min(maes_valid)
        ax.axhline(y=min_mae, color='green', linestyle='--', alpha=0.5, 
                  label=f'Best MAE: {min_mae:.2e}')
    
    ax.set_xlabel("Simulation Duration (ns)", fontsize=config.font_size + 2)
    ax.set_ylabel("Mean Absolute Error (m²/s)", fontsize=config.font_size + 2)
    ax.set_title("Timescale-Accuracy Curve: MD vs. NIST References", 
                fontsize=config.font_size + 4, fontweight='bold')
    ax.legend(loc='best', fontsize=config.font_size)
    ax.grid(True, alpha=0.3)
    
    # Ensure output directory exists
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if output_path is None:
        output_path = str(output_dir / "timescale_accuracy_curve.png")
    
    plt.savefig(output_path, dpi=config.dpi, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Timescale-accuracy plot saved to: {output_path}")
    return output_path

def generate_multi_solvent_comparison(
    results: List[Dict[str, Any]],
    config: Optional[PlotConfig] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Generate multi-solvent comparison plot showing MAE trends across solvents.
    
    Args:
        results: List of diffusion analysis results
        config: Plot configuration
        output_path: Optional custom output path
        
    Returns:
        Path to generated plot file
    """
    if config is None:
        config = PlotConfig()
    
    sns.set_style(config.style)
    plt.rcParams['font.size'] = config.font_size
    
    # Group results by solvent and duration
    solvent_data = {}
    for result in results:
        solvent = result.get('solvent', 'unknown')
        duration = result.get('duration_ns')
        mae = result.get('mae')
        
        if duration is None or mae is None:
            continue
        
        if solvent not in solvent_data:
            solvent_data[solvent] = {'durations': [], 'maes': [], 'mae_std': []}
        
        solvent_data[solvent]['durations'].append(duration)
        solvent_data[solvent]['maes'].append(mae)
    
    if not solvent_data:
        logger.warning("No valid data for multi-solvent comparison")
        fig, ax = plt.subplots(figsize=config.figsize)
        ax.set_title("Multi-Solvent Comparison (No Data Available)")
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        if output_path is None:
            output_path = str(output_dir / "multi_solvent_comparison_empty.png")
        plt.savefig(output_path, dpi=config.dpi, bbox_inches='tight')
        plt.close()
        return output_path
    
    # Create figure
    fig, ax = plt.subplots(figsize=config.figsize)
    
    colors = sns.color_palette(config.color_palette, len(solvent_data))
    
    for (solvent, data), color in zip(solvent_data.items(), colors):
        durations = np.array(data['durations'])
        maes = np.array(data['maes'])
        
        # Sort by duration
        sort_idx = np.argsort(durations)
        durations = durations[sort_idx]
        maes = maes[sort_idx]
        
        # Calculate error bars
        maes_std = np.std(maes) if len(maes) > 1 else 0
        
        ax.errorbar(
            durations,
            maes,
            yerr=maes_std,
            label=solvent.capitalize(),
            color=color,
            marker='o',
            linewidth=2,
            capsize=5
        )
    
    ax.set_xlabel("Simulation Duration (ns)", fontsize=config.font_size + 2)
    ax.set_ylabel("Mean Absolute Error (m²/s)", fontsize=config.font_size + 2)
    ax.set_title("Multi-Solvent Comparison: MD Accuracy vs. Timescale", 
                fontsize=config.font_size + 4, fontweight='bold')
    ax.legend(loc='best', fontsize=config.font_size)
    ax.grid(True, alpha=0.3)
    
    # Ensure output directory exists
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if output_path is None:
        output_path = str(output_dir / "multi_solvent_comparison.png")
    
    plt.savefig(output_path, dpi=config.dpi, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Multi-solvent comparison plot saved to: {output_path}")
    return output_path

def main():
    """Main entry point for generating plots from diffusion results."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate timescale-accuracy plots")
    parser.add_argument(
        "--results-dir",
        type=str,
        default="data/processed/analysis",
        help="Directory containing diffusion results JSON files"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed/figures",
        help="Output directory for generated plots"
    )
    parser.add_argument(
        "--style",
        type=str,
        default="seaborn-v0_8-whitegrid",
        help="Seaborn style to use"
    )
    parser.add_argument(
        "--r2-threshold",
        type=float,
        default=0.95,
        help="R² threshold for filtering valid results"
    )
    
    args = parser.parse_args()
    
    # Setup logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info(f"Loading results from: {args.results_dir}")
    results = load_diffusion_results(args.results_dir)
    logger.info(f"Loaded {len(results)} results")
    
    if not results:
        logger.error("No results found. Cannot generate plots.")
        return 1
    
    # Create configuration
    config = PlotConfig(
        output_dir=args.output_dir,
        style=args.style,
        r2_threshold=args.r2_threshold
    )
    
    # Generate timescale-accuracy plot
    logger.info("Generating timescale-accuracy curve...")
    plot_path = generate_timescale_accuracy_plot(results, config)
    logger.info(f"Generated: {plot_path}")
    
    # Generate multi-solvent comparison
    logger.info("Generating multi-solvent comparison...")
    comparison_path = generate_multi_solvent_comparison(results, config)
    logger.info(f"Generated: {comparison_path}")
    
    logger.info("Plot generation complete.")
    return 0

if __name__ == "__main__":
    exit(main())