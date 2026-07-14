"""
Scaling analysis: Fit power-law curves to metric trends vs. agent count.

This module implements power-law fitting for specialization index and retrieval
efficiency as a function of agent population size, following the approach
described in Geoffrey West's work on scaling laws in complex systems.

Model: Y = a * N^b  =>  log(Y) = log(a) + b * log(N)
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

# Import from existing project modules
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PowerLawFitResult:
    """Results from fitting a power-law model Y = a * N^b."""
    metric_name: str
    exponent: float  # b in Y = a * N^b
    coefficient: float  # a in Y = a * N^b
    r_squared: float
    p_value: float
    std_err: float
    n_points: int
    min_n: float
    max_n: float


@dataclass
class ScalingAnalysisResult:
    """Complete scaling analysis results for both metrics."""
    specialization_fit: PowerLawFitResult
    retrieval_fit: PowerLawFitResult
    data_points: List[Dict[str, Any]]


def power_law(n: float, a: float, b: float) -> float:
    """Compute power-law prediction: Y = a * N^b."""
    if n <= 0 or a <= 0:
        return float('nan')
    return a * (n ** b)


def fit_power_law(
    n_values: np.ndarray,
    y_values: np.ndarray,
    metric_name: str
) -> Optional[PowerLawFitResult]:
    """
    Fit a power-law model Y = a * N^b using log-log linear regression.
    
    Args:
        n_values: Agent counts (must be positive)
        y_values: Metric values (must be positive)
        metric_name: Name of the metric being fitted
        
    Returns:
        PowerLawFitResult with fitted parameters and statistics, or None if fit fails
    """
    if len(n_values) < 3:
        logger.log("power_law_fit", status="skipped", reason="insufficient_data_points", n_points=len(n_values))
        return None
    
    # Filter out non-positive values
    valid_mask = (n_values > 0) & (y_values > 0)
    n_valid = n_values[valid_mask]
    y_valid = y_values[valid_mask]
    
    if len(n_valid) < 3:
        logger.log("power_law_fit", status="skipped", reason="insufficient_valid_points", n_points=len(n_valid))
        return None
    
    # Log-transform for linear regression
    log_n = np.log(n_valid)
    log_y = np.log(y_valid)
    
    # Perform linear regression: log(Y) = log(a) + b * log(N)
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_n, log_y)
    
    # Convert back to power-law parameters
    exponent = slope
    coefficient = math.exp(intercept)
    r_squared = r_value ** 2
    
    return PowerLawFitResult(
        metric_name=metric_name,
        exponent=exponent,
        coefficient=coefficient,
        r_squared=r_squared,
        p_value=p_value,
        std_err=std_err,
        n_points=len(n_valid),
        min_n=float(n_valid.min()),
        max_n=float(n_valid.max())
    )


def load_scaling_data(
    results_dir: pathlib.Path,
    context_condition: str = "full"
) -> List[Dict[str, Any]]:
    """
    Load scaling experiment results from CSV files.
    
    Args:
        results_dir: Directory containing results CSV files
        context_condition: 'full' or 'limited' context condition
        
    Returns:
        List of dictionaries with agent_count, specialization_index, retrieval_efficiency
    """
    data = []
    
    # Try to find scaling results file
    if context_condition == "full":
        csv_path = results_dir / "results_scaling_full.csv"
    else:
        csv_path = results_dir / "results_scaling_limited.csv"
    
    if not csv_path.exists():
        # Fallback: look for any scaling results
        for pattern in ["results_scaling*.csv", "scaling_results*.csv"]:
            matches = list(results_dir.glob(pattern))
            if matches:
                csv_path = matches[0]
                break
    
    if not csv_path.exists():
        logger.log("load_scaling_data", status="not_found", path=str(csv_path))
        return data
    
    logger.log("load_scaling_data", status="loading", path=str(csv_path))
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                entry = {
                    'game_id': int(row.get('game_id', 0)),
                    'agent_count': int(row.get('agent_count', row.get('agents', 0))),
                    'specialization_index': float(row.get('specialization_index', row.get('spec_index', 0))),
                    'retrieval_efficiency': float(row.get('retrieval_efficiency', row.get('ret_eff', 0))),
                    'context_condition': row.get('context_condition', context_condition)
                }
                data.append(entry)
            except (ValueError, KeyError) as e:
                logger.log("load_scaling_data", status="skip_row", error=str(e))
                continue
    
    logger.log("load_scaling_data", status="loaded", n_rows=len(data))
    return data


def aggregate_by_agent_count(
    data: List[Dict[str, Any]]
) -> Dict[int, Dict[str, List[float]]]:
    """
    Aggregate metrics by agent count, computing mean values.
    
    Args:
        data: List of game result dictionaries
        
    Returns:
        Dictionary mapping agent_count -> {specialization: [values], retrieval: [values]}
    """
    aggregated = {}
    
    for entry in data:
        n = entry['agent_count']
        if n not in aggregated:
            aggregated[n] = {'specialization': [], 'retrieval': []}
        
        spec = entry['specialization_index']
        ret = entry['retrieval_efficiency']
        
        if not math.isnan(spec) and spec >= 0:
            aggregated[n]['specialization'].append(spec)
        if not math.isnan(ret) and ret >= 0:
            aggregated[n]['retrieval'].append(ret)
    
    return aggregated


def run_scaling_analysis(
    data: List[Dict[str, Any]],
    output_dir: Optional[pathlib.Path] = None
) -> Optional[ScalingAnalysisResult]:
    """
    Run complete scaling analysis: aggregate data and fit power-law curves.
    
    Args:
        data: Raw game result data
        output_dir: Directory to write analysis results (optional)
        
    Returns:
        ScalingAnalysisResult with fitted power-law models
    """
    if not data:
        logger.log("run_scaling_analysis", status="no_data")
        return None
    
    # Aggregate by agent count
    aggregated = aggregate_by_agent_count(data)
    
    if len(aggregated) < 3:
        logger.log("run_scaling_analysis", status="insufficient_agent_counts", n_counts=len(aggregated))
        # Still try to fit with available data
    
    # Prepare arrays for fitting
    agent_counts = sorted(aggregated.keys())
    spec_means = []
    ret_means = []
    
    for n in agent_counts:
        spec_vals = aggregated[n]['specialization']
        ret_vals = aggregated[n]['retrieval']
        
        spec_means.append(np.mean(spec_vals) if spec_vals else np.nan)
        ret_means.append(np.mean(ret_vals) if ret_vals else np.nan)
    
    n_array = np.array(agent_counts, dtype=float)
    spec_array = np.array(spec_means, dtype=float)
    ret_array = np.array(ret_means, dtype=float)
    
    # Fit power-law curves
    spec_fit = fit_power_law(n_array, spec_array, "specialization_index")
    ret_fit = fit_power_law(n_array, ret_array, "retrieval_efficiency")
    
    if spec_fit is None and ret_fit is None:
        logger.log("run_scaling_analysis", status="fit_failed")
        return None
    
    # Prepare data points for output
    data_points = []
    for i, n in enumerate(agent_counts):
        data_points.append({
            'agent_count': n,
            'specialization_mean': float(spec_array[i]) if not math.isnan(spec_array[i]) else None,
            'retrieval_mean': float(ret_array[i]) if not math.isnan(ret_array[i]) else None,
            'spec_count': len(aggregated[n]['specialization']),
            'ret_count': len(aggregated[n]['retrieval'])
        })
    
    result = ScalingAnalysisResult(
        specialization_fit=spec_fit,
        retrieval_fit=ret_fit,
        data_points=data_points
    )
    
    # Write results if output_dir specified
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        results_path = output_dir / "scaling_analysis_results.json"
        
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump({
                'specialization': asdict(result.specialization_fit),
                'retrieval': asdict(result.retrieval_fit),
                'data_points': result.data_points
            }, f, indent=2)
        
        logger.log("run_scaling_analysis", status="saved", path=str(results_path))
    
    return result


def generate_scaling_plot(
    result: ScalingAnalysisResult,
    output_path: pathlib.Path
) -> None:
    """
    Generate a scaling plot with fitted power-law curves.
    
    Args:
        result: Scaling analysis results
        output_path: Path to save the plot (PDF or PNG)
    """
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Extract data
    agent_counts = [dp['agent_count'] for dp in result.data_points]
    spec_means = [dp['specialization_mean'] for dp in result.data_points if dp['specialization_mean'] is not None]
    ret_means = [dp['retrieval_mean'] for dp in result.data_points if dp['retrieval_mean'] is not None]
    
    # Plot specialization
    if spec_means:
        ax.scatter(agent_counts, spec_means, c='blue', label='Specialization Index (observed)', zorder=3)
        if result.specialization_fit:
            n_fit = np.linspace(min(agent_counts), max(agent_counts), 100)
            y_fit = result.specialization_fit.coefficient * (n_fit ** result.specialization_fit.exponent)
            ax.plot(n_fit, y_fit, 'b-', label=f'Specialization fit: Y = {result.specialization_fit.coefficient:.3f} N^{result.specialization_fit.exponent:.3f}')
    
    # Plot retrieval
    if ret_means:
        ax.scatter(agent_counts, ret_means, c='red', marker='s', label='Retrieval Efficiency (observed)', zorder=3)
        if result.retrieval_fit:
            n_fit = np.linspace(min(agent_counts), max(agent_counts), 100)
            y_fit = result.retrieval_fit.coefficient * (n_fit ** result.retrieval_fit.exponent)
            ax.plot(n_fit, y_fit, 'r-', label=f'Retrieval fit: Y = {result.retrieval_fit.coefficient:.3f} N^{result.retrieval_fit.exponent:.3f}')
    
    # Formatting
    ax.set_xlabel('Number of Agents (N)', fontsize=12)
    ax.set_ylabel('Metric Value', fontsize=12)
    ax.set_title('Scaling of Collective Remembering Metrics with Agent Population', fontsize=14)
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Add note about data points
    n_points = len(agent_counts)
    note = f"Note: {n_points} data points limit power-law reliability"
    ax.text(0.02, 0.98, note, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.log("generate_scaling_plot", status="saved", path=str(output_path), n_points=n_points)


def build_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser for scaling analysis."""
    parser = argparse.ArgumentParser(
        description="Fit power-law curves to scaling analysis results"
    )
    parser.add_argument(
        '--input-dir',
        type=str,
        default='projects/PROJ-586-social-memory-networks-modeling-collecti/results',
        help='Directory containing scaling results CSV files'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='projects/PROJ-586-social-memory-networks-modeling-collecti/results',
        help='Directory to save analysis results and plots'
    )
    parser.add_argument(
        '--context',
        type=str,
        choices=['full', 'limited'],
        default='full',
        help='Context condition to analyze'
    )
    parser.add_argument(
        '--plot',
        action='store_true',
        help='Generate scaling plot'
    )
    return parser


def main() -> int:
    """Main entry point for scaling analysis."""
    parser = build_parser()
    args = parser.parse_args()
    
    input_dir = pathlib.Path(args.input_dir)
    output_dir = pathlib.Path(args.output_dir)
    
    if not input_dir.exists():
        logger.log("main", status="error", reason="input_dir_not_found", path=str(input_dir))
        return 1
    
    # Load data
    data = load_scaling_data(input_dir, context_condition=args.context)
    
    if not data:
        logger.log("main", status="no_data_loaded")
        return 1
    
    logger.log("main", status="running", n_games=len(data), context=args.context)
    
    # Run analysis
    result = run_scaling_analysis(data, output_dir=output_dir)
    
    if result is None:
        logger.log("main", status="analysis_failed")
        return 1
    
    # Print summary
    print(f"\n=== Scaling Analysis Results ({args.context} context) ===")
    print(f"Data points: {len(result.data_points)} agent configurations")
    
    if result.specialization_fit:
        print(f"\nSpecialization Index:")
        print(f"  Fit: Y = {result.specialization_fit.coefficient:.4f} * N^{result.specialization_fit.exponent:.4f}")
        print(f"  R² = {result.specialization_fit.r_squared:.4f}, p = {result.specialization_fit.p_value:.4f}")
    
    if result.retrieval_fit:
        print(f"\nRetrieval Efficiency:")
        print(f"  Fit: Y = {result.retrieval_fit.coefficient:.4f} * N^{result.retrieval_fit.exponent:.4f}")
        print(f"  R² = {result.retrieval_fit.r_squared:.4f}, p = {result.retrieval_fit.p_value:.4f}")
    
    # Generate plot if requested
    if args.plot:
        plot_path = output_dir / "scaling_plot.pdf"
        generate_scaling_plot(result, plot_path)
        print(f"\nPlot saved to: {plot_path}")
    
    logger.log("main", status="completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())