"""
Scaling analysis for social memory networks.

Implements power-law fitting for metric trends vs. agent count.
Fits log-log curves for specialization index and retrieval efficiency.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import warnings
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import optimize

# Import from existing project modules
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PowerLawFitResult:
    """Result of a power-law fit: y = a * x^b"""
    exponent: float  # b in x^b
    coefficient: float  # a
    r_squared: float
    standard_error: Optional[float] = None
    n_points: int = 0
    success: bool = True
    message: str = ""


@dataclass
class ScalingAnalysisResult:
    """Complete scaling analysis results"""
    specialization_fit: PowerLawFitResult
    retrieval_fit: PowerLawFitResult
    raw_data: List[Dict[str, Any]]
    agent_counts: List[int]
    specialization_values: List[float]
    retrieval_values: List[float]


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power law function: y = a * x^b"""
    return a * np.power(x, b)


def fit_power_law(
    x: np.ndarray,
    y: np.ndarray,
    p0: Optional[Tuple[float, float]] = None
) -> PowerLawFitResult:
    """
    Fit a power law y = a * x^b to data using non-linear least squares.
    
    Args:
        x: Independent variable values (agent counts)
        y: Dependent variable values (metrics)
        p0: Initial guess for (a, b)
        
    Returns:
        PowerLawFitResult with fitted parameters and statistics
    """
    if len(x) < 3:
        # Need at least 3 points for meaningful fit
        return PowerLawFitResult(
            exponent=0.0,
            coefficient=1.0,
            r_squared=0.0,
            n_points=len(x),
            success=False,
            message="Insufficient data points (need >= 3)"
        )
    
    # Filter out non-positive values for log transformation
    mask = (x > 0) & (y > 0)
    x_valid = x[mask]
    y_valid = y[mask]
    
    if len(x_valid) < 3:
        return PowerLawFitResult(
            exponent=0.0,
            coefficient=1.0,
            r_squared=0.0,
            n_points=len(x),
            success=False,
            message="Insufficient positive data points for log transformation"
        )
    
    # Initial guess: use log-log linear regression for starting values
    log_x = np.log(x_valid)
    log_y = np.log(y_valid)
    
    # Linear fit on log-log scale: log(y) = log(a) + b * log(x)
    slope, intercept = np.polyfit(log_x, log_y, 1)
    a_init = np.exp(intercept)
    b_init = slope
    
    if p0 is None:
        p0 = (a_init, b_init)
    
    try:
        # Fit using non-linear least squares
        popt, pcov = optimize.curve_fit(
            power_law,
            x_valid,
            y_valid,
            p0=p0,
            bounds=(0, [np.inf, np.inf]),  # a > 0, b can be any value
            maxfev=10000
        )
        
        a_fit, b_fit = popt
        
        # Calculate R-squared
        y_pred = power_law(x_valid, a_fit, b_fit)
        ss_res = np.sum((y_valid - y_pred) ** 2)
        ss_tot = np.sum((y_valid - np.mean(y_valid)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        # Calculate standard error
        if pcov is not None:
            perr = np.sqrt(np.diag(pcov))
            standard_error = perr[1]  # Standard error of exponent
        else:
            standard_error = None
        
        return PowerLawFitResult(
            exponent=b_fit,
            coefficient=a_fit,
            r_squared=r_squared,
            standard_error=standard_error,
            n_points=len(x_valid),
            success=True,
            message="Fit successful"
        )
        
    except Exception as e:
        logger.log("fit_power_law_error", error=str(e))
        return PowerLawFitResult(
            exponent=0.0,
            coefficient=1.0,
            r_squared=0.0,
            n_points=len(x),
            success=False,
            message=f"Fit failed: {str(e)}"
        )


def load_scaling_data(
    input_path: str,
    specialization_col: str = "specialization_index",
    retrieval_col: str = "retrieval_efficiency",
    agent_count_col: str = "agent_count"
) -> Tuple[List[int], List[float], List[float], List[Dict[str, Any]]]:
    """
    Load scaling data from CSV file.
    
    Args:
        input_path: Path to CSV file with results
        specialization_col: Column name for specialization index
        retrieval_col: Column name for retrieval efficiency
        agent_count_col: Column name for agent count
        
    Returns:
        Tuple of (agent_counts, spec_values, ret_values, raw_rows)
    """
    agent_counts: List[int] = []
    spec_values: List[float] = []
    ret_values: List[float] = []
    raw_rows: List[Dict[str, Any]] = []
    
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                n = int(row[agent_count_col])
                spec = float(row[specialization_col])
                ret = float(row[retrieval_col])
                
                agent_counts.append(n)
                spec_values.append(spec)
                ret_values.append(ret)
                raw_rows.append(row)
            except (ValueError, KeyError) as e:
                logger.log("load_scaling_data_skip_row", error=str(e), row=row)
                continue
    
    return agent_counts, spec_values, ret_values, raw_rows


def aggregate_by_agent_count(
    agent_counts: List[int],
    spec_values: List[float],
    ret_values: List[float]
) -> Tuple[List[int], List[float], List[float]]:
    """
    Aggregate metrics by agent count (compute mean for each unique count).
    
    Args:
        agent_counts: List of agent counts
        spec_values: List of specialization indices
        ret_values: List of retrieval efficiencies
        
    Returns:
        Tuple of (unique_counts, mean_spec, mean_ret)
    """
    from collections import defaultdict
    
    spec_by_n: Dict[int, List[float]] = defaultdict(list)
    ret_by_n: Dict[int, List[float]] = defaultdict(list)
    
    for n, spec, ret in zip(agent_counts, spec_values, ret_values):
        spec_by_n[n].append(spec)
        ret_by_n[n].append(ret)
    
    unique_counts = sorted(spec_by_n.keys())
    mean_spec = [np.mean(spec_by_n[n]) for n in unique_counts]
    mean_ret = [np.mean(ret_by_n[n]) for n in unique_counts]
    
    return unique_counts, mean_spec, mean_ret


def run_scaling_analysis(
    input_path: str,
    output_path: Optional[str] = None
) -> ScalingAnalysisResult:
    """
    Run complete scaling analysis: load data, aggregate, fit power laws.
    
    Args:
        input_path: Path to CSV with experiment results
        output_path: Optional path to write JSON results
        
    Returns:
        ScalingAnalysisResult with all computed values
    """
    # Load data
    agent_counts, spec_values, ret_values, raw_rows = load_scaling_data(input_path)
    
    if len(agent_counts) < 3:
        logger.log("run_scaling_analysis_insufficient_data", count=len(agent_counts))
        # Create minimal result with failure indicators
        result = ScalingAnalysisResult(
            specialization_fit=PowerLawFitResult(
                exponent=0.0, coefficient=1.0, r_squared=0.0,
                n_points=len(agent_counts), success=False,
                message="Insufficient data points"
            ),
            retrieval_fit=PowerLawFitResult(
                exponent=0.0, coefficient=1.0, r_squared=0.0,
                n_points=len(agent_counts), success=False,
                message="Insufficient data points"
            ),
            raw_data=raw_rows,
            agent_counts=agent_counts,
            specialization_values=spec_values,
            retrieval_values=ret_values
        )
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(result), f, indent=2)
        
        return result
    
    # Aggregate by agent count
    unique_counts, mean_spec, mean_ret = aggregate_by_agent_count(
        agent_counts, spec_values, ret_values
    )
    
    # Fit power laws
    x = np.array(unique_counts)
    y_spec = np.array(mean_spec)
    y_ret = np.array(mean_ret)
    
    spec_fit = fit_power_law(x, y_spec)
    ret_fit = fit_power_law(x, y_ret)
    
    logger.log(
        "scaling_analysis_complete",
        n_points=len(unique_counts),
        spec_exponent=spec_fit.exponent,
        ret_exponent=ret_fit.exponent,
        spec_r_squared=spec_fit.r_squared,
        ret_r_squared=ret_fit.r_squared
    )
    
    result = ScalingAnalysisResult(
        specialization_fit=spec_fit,
        retrieval_fit=ret_fit,
        raw_data=raw_rows,
        agent_counts=unique_counts,
        specialization_values=mean_spec,
        retrieval_values=mean_ret
    )
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(result), f, indent=2)
    
    return result


def generate_scaling_plot(
    result: ScalingAnalysisResult,
    output_path: str,
    dpi: int = 150
) -> None:
    """
    Generate a scaling plot with fitted power-law curves.
    
    Args:
        result: ScalingAnalysisResult with fitted parameters
        output_path: Path to save the plot (PDF/PNG)
        dpi: Resolution for the plot
    """
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    
    if not result.specialization_fit.success or not result.retrieval_fit.success:
        logger.log("generate_scaling_plot_skip", reason="Fit failed")
        # Create a minimal plot showing the issue
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "Fit failed - insufficient data", 
               transform=ax.transAxes, ha='center', va='center', fontsize=14)
        ax.set_title("Scaling Analysis - Fit Failed")
        fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
        return
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.array(result.agent_counts)
    y_spec = np.array(result.specialization_values)
    y_ret = np.array(result.retrieval_values)
    
    # Plot raw data points
    ax.scatter(x, y_spec, color='blue', label='Specialization Index (measured)', alpha=0.7, s=80)
    ax.scatter(x, y_ret, color='red', label='Retrieval Efficiency (measured)', alpha=0.7, s=80)
    
    # Generate smooth curve for fits
    x_smooth = np.linspace(min(x), max(x), 100)
    
    # Specialization fit curve
    a_spec = result.specialization_fit.coefficient
    b_spec = result.specialization_fit.exponent
    y_spec_fit = power_law(x_smooth, a_spec, b_spec)
    ax.plot(x_smooth, y_spec_fit, 'b--', linewidth=2, 
           label=f'Specialization fit: y = {a_spec:.3f} * x^{b_spec:.3f}')
    
    # Retrieval fit curve
    a_ret = result.retrieval_fit.coefficient
    b_ret = result.retrieval_fit.exponent
    y_ret_fit = power_law(x_smooth, a_ret, b_ret)
    ax.plot(x_smooth, y_ret_fit, 'r--', linewidth=2,
           label=f'Retrieval fit: y = {a_ret:.3f} * x^{b_ret:.3f}')
    
    # Add note about data limitations
    note_text = f"Note: {len(x)} data points limit power-law reliability"
    ax.text(0.02, 0.02, note_text, transform=ax.transAxes, 
           fontsize=10, verticalalignment='bottom',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    ax.set_xlabel('Number of Agents', fontsize=12)
    ax.set_ylabel('Metric Value', fontsize=12)
    ax.set_title('Scaling of Collective Remembering Metrics with Agent Count', fontsize=14)
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Set log scale for x-axis if appropriate
    if min(x) > 0:
        ax.set_xscale('log')
    
    fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    logger.log("generate_scaling_plot_complete", output_path=output_path)


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for scaling analysis CLI."""
    parser = argparse.ArgumentParser(
        description="Analyze scaling of memory metrics with agent count"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input CSV file with experiment results"
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Output JSON file for analysis results"
    )
    parser.add_argument(
        "--output-plot",
        type=str,
        default=None,
        help="Output plot file (PDF/PNG)"
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="Plot resolution (default: 150)"
    )
    return parser


def main() -> None:
    """Main entry point for scaling analysis."""
    parser = build_parser()
    args = parser.parse_args()
    
    logger.log("scaling_analysis_start", input=args.input)
    
    result = run_scaling_analysis(
        input_path=args.input,
        output_path=args.output_json
    )
    
    if args.output_plot:
        generate_scaling_plot(result, args.output_plot, dpi=args.dpi)
    
    logger.log(
        "scaling_analysis_end",
        spec_exponent=result.specialization_fit.exponent,
        ret_exponent=result.retrieval_fit.exponent,
        spec_success=result.specialization_fit.success,
        ret_success=result.retrieval_fit.success
    )


if __name__ == "__main__":
    main()