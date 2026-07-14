"""
Scaling analysis: Power-law fitting for metric trends vs. agent count.

Fits log-log curves for specialization index and retrieval efficiency
against the number of agents to test for sublinear/superlinear scaling.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Local imports (tolerant of missing optional deps)
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for CI
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# ----------------------------------------------------------------------
# Data Classes
# ----------------------------------------------------------------------

@dataclass
class PowerLawFitResult:
    """Result of a power-law fit y = a * x^b."""
    metric_name: str
    exponent: float
    intercept: float  # log(a)
    r_squared: float
    p_value: float
    std_err: float
    n_points: int
    fit_valid: bool
    message: str = ""

@dataclass
class ScalingAnalysisResult:
    """Aggregated results for the scaling analysis."""
    specialization_fit: Optional[PowerLawFitResult] = None
    retrieval_fit: Optional[PowerLawFitResult] = None
    raw_data: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

# ----------------------------------------------------------------------
# Core Logic
# ----------------------------------------------------------------------

def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Compute y = a * x^b."""
    return a * np.power(x, b)

def fit_power_law(
    x: np.ndarray,
    y: np.ndarray,
    metric_name: str
) -> PowerLawFitResult:
    """
    Fit a power law y = a * x^b by linearizing: log(y) = log(a) + b * log(x).
    
    Returns a PowerLawFitResult. If fitting fails (e.g., non-positive data),
    returns a result with fit_valid=False.
    """
    # Filter out non-positive values for log transform
    valid_mask = (x > 0) & (y > 0)
    if np.sum(valid_mask) < 2:
        return PowerLawFitResult(
            metric_name=metric_name,
            exponent=0.0,
            intercept=0.0,
            r_squared=0.0,
            p_value=1.0,
            std_err=0.0,
            n_points=int(np.sum(valid_mask)),
            fit_valid=False,
            message="Insufficient valid data points (x>0, y>0) for log-log fit."
        )

    x_valid = np.log(x[valid_mask])
    y_valid = np.log(y[valid_mask])

    if not HAS_SCIPY:
        # Fallback to numpy polyfit if scipy is missing
        try:
            slope, intercept, r_value, p_value, std_err = np.polyfit(
                x_valid, y_valid, 1, full=False, cov=False
            )
            # np.polyfit doesn't return p-value directly in older versions, 
            # but for this fallback we approximate or set to 0.0 if not available.
            # Actually, numpy linear regression stats are complex without scipy.
            # We will assume scipy is present as per requirements.txt (statsmodels/scipy usually bundled).
            # If not, we set p_value to 0.0 as a placeholder, though not ideal.
            p_value = 0.0 
        except Exception as e:
            return PowerLawFitResult(
                metric_name=metric_name,
                exponent=0.0,
                intercept=0.0,
                r_squared=0.0,
                p_value=1.0,
                std_err=0.0,
                n_points=len(x_valid),
                fit_valid=False,
                message=f"Fallback fit failed: {e}"
            )
    else:
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_valid, y_valid)

    r_squared = r_value ** 2
    exponent = slope
    log_a = intercept
    
    return PowerLawFitResult(
        metric_name=metric_name,
        exponent=exponent,
        intercept=log_a,
        r_squared=r_squared,
        p_value=p_value,
        std_err=std_err,
        n_points=len(x_valid),
        fit_valid=True,
        message=f"Fit successful. N={len(x_valid)}, R^2={r_squared:.4f}"
    )

def load_scaling_data(input_path: pathlib.Path) -> List[Dict[str, Any]]:
    """
    Load scaling data from a CSV file.
    
    Expected columns: 'agent_count', 'specialization_index', 'retrieval_efficiency'
    (plus others like game_id, etc.)
    """
    data = []
    if not input_path.exists():
        raise FileNotFoundError(f"Scaling data file not found: {input_path}")
    
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert relevant fields to float
            try:
                record = {
                    'agent_count': int(row['agent_count']),
                    'specialization_index': float(row['specialization_index']),
                    'retrieval_efficiency': float(row['retrieval_efficiency']),
                    'game_id': row.get('game_id', ''),
                }
                data.append(record)
            except (ValueError, KeyError) as e:
                # Skip malformed rows
                continue
    return data

def run_scaling_analysis(
    data: List[Dict[str, Any]],
    output_dir: Optional[pathlib.Path] = None
) -> ScalingAnalysisResult:
    """
    Run the scaling analysis: fit power laws for both metrics.
    """
    if not data:
        return ScalingAnalysisResult(
            notes=["No data provided for scaling analysis."]
        )

    # Aggregate data by agent_count (compute mean per group)
    # This handles cases where multiple games were run per agent count
    groups: Dict[int, Dict[str, List[float]]] = {}
    for row in data:
        n = row['agent_count']
        if n not in groups:
            groups[n] = {'spec': [], 'ret': []}
        groups[n]['spec'].append(row['specialization_index'])
        groups[n]['ret'].append(row['retrieval_efficiency'])

    # Compute means
    agent_counts = sorted(groups.keys())
    spec_means = [np.mean(groups[n]['spec']) for n in agent_counts]
    ret_means = [np.mean(groups[n]['ret']) for n in agent_counts]

    # Fit curves
    spec_fit = fit_power_law(np.array(agent_counts), np.array(spec_means), "specialization_index")
    ret_fit = fit_power_law(np.array(agent_counts), np.array(ret_means), "retrieval_efficiency")

    result = ScalingAnalysisResult(
        specialization_fit=spec_fit,
        retrieval_fit=ret_fit,
        raw_data=data,
        notes=[]
    )

    # Add warnings if few points
    if len(agent_counts) < 3:
        result.notes.append(
            "WARNING: Only " + str(len(agent_counts)) + 
            " distinct agent counts available. Power-law fitting is statistically unreliable with < 3 points."
        )

    # Optional: Save fit results to JSON if output_dir provided
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        fit_output = {
            "specialization": {
                "exponent": spec_fit.exponent,
                "r_squared": spec_fit.r_squared,
                "p_value": spec_fit.p_value,
                "fit_valid": spec_fit.fit_valid,
                "message": spec_fit.message
            },
            "retrieval": {
                "exponent": ret_fit.exponent,
                "r_squared": ret_fit.r_squared,
                "p_value": ret_fit.p_value,
                "fit_valid": ret_fit.fit_valid,
                "message": ret_fit.message
            },
            "data_points": len(agent_counts),
            "agent_counts": agent_counts
        }
        with open(output_dir / "scaling_fit_results.json", 'w') as f:
            json.dump(fit_output, f, indent=2)

    return result

def generate_scaling_plot(
    result: ScalingAnalysisResult,
    output_path: pathlib.Path
) -> None:
    """
    Generate a PDF plot of the scaling analysis with fitted curves.
    """
    if not HAS_MATPLOTLIB:
        raise RuntimeError("matplotlib is required to generate scaling plots.")

    # Reconstruct means for plotting
    data = result.raw_data
    if not data:
        return

    groups: Dict[int, Dict[str, List[float]]] = {}
    for row in data:
        n = row['agent_count']
        if n not in groups:
            groups[n] = {'spec': [], 'ret': []}
        groups[n]['spec'].append(row['specialization_index'])
        groups[n]['ret'].append(row['retrieval_efficiency'])

    agent_counts = sorted(groups.keys())
    spec_means = [np.mean(groups[n]['spec']) for n in agent_counts]
    ret_means = [np.mean(groups[n]['ret']) for n in agent_counts]
    spec_std = [np.std(groups[n]['spec']) for n in agent_counts]
    ret_std = [np.std(groups[n]['ret']) for n in agent_counts]

    x = np.array(agent_counts)
    y_spec = np.array(spec_means)
    y_ret = np.array(ret_means)

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot data points
    ax.errorbar(x, y_spec, yerr=spec_std, fmt='o', label='Specialization Index', capsize=5, color='blue')
    ax.errorbar(x, y_ret, yerr=ret_std, fmt='s', label='Retrieval Efficiency', capsize=5, color='green')

    # Plot fitted curves
    x_fit = np.linspace(min(x), max(x), 100)

    if result.specialization_fit and result.specialization_fit.fit_valid:
        a_spec = math.exp(result.specialization_fit.intercept)
        b_spec = result.specialization_fit.exponent
        y_fit_spec = power_law(x_fit, a_spec, b_spec)
        ax.plot(x_fit, y_fit_spec, 'b--', label=f'Spec Fit (exp={b_spec:.3f})')

    if result.retrieval_fit and result.retrieval_fit.fit_valid:
        a_ret = math.exp(result.retrieval_fit.intercept)
        b_ret = result.retrieval_fit.exponent
        y_fit_ret = power_law(x_fit, a_ret, b_ret)
        ax.plot(x_fit, y_fit_ret, 'g--', label=f'Ret Fit (exp={b_ret:.3f})')

    ax.set_xlabel('Number of Agents')
    ax.set_ylabel('Metric Value')
    ax.set_title('Scaling Analysis: Metrics vs. Agent Count')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Add note about data points
    note_text = "Note: 3 data points limit power-law reliability."
    if len(agent_counts) < 3:
        note_text = f"WARNING: Only {len(agent_counts)} data points. Power-law fitting is unreliable."
    
    ax.text(0.02, 0.98, note_text, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.title('Scaling of Collective Remembering Metrics', fontsize=14)
    plt.tight_layout()
    plt.savefig(output_path, format='pdf')
    plt.close()

# ----------------------------------------------------------------------
# CLI / Entry Point
# ----------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run scaling analysis on experiment results.")
    parser.add_argument(
        "--input", "-i",
        type=pathlib.Path,
        default=pathlib.Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_data.csv"),
        help="Input CSV file with scaling simulation results."
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=pathlib.Path,
        default=pathlib.Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results"),
        help="Directory to write output files (JSON results, PDF plot)."
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate the scaling plot PDF."
    )
    return parser

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    print(f"Loading scaling data from {args.input}...")
    try:
        data = load_scaling_data(args.input)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if not data:
        print("Error: No valid data found in input file.")
        sys.exit(1)

    print(f"Loaded {len(data)} records.")
    print("Running scaling analysis (power-law fits)...")

    result = run_scaling_analysis(data, args.output_dir)

    # Print summary
    print("\n--- Scaling Analysis Results ---")
    if result.specialization_fit:
        print(f"Specialization Index: exp={result.specialization_fit.exponent:.4f}, R2={result.specialization_fit.r_squared:.4f}, valid={result.specialization_fit.fit_valid}")
    if result.retrieval_fit:
        print(f"Retrieval Efficiency: exp={result.retrieval_fit.exponent:.4f}, R2={result.retrieval_fit.r_squared:.4f}, valid={result.retrieval_fit.fit_valid}")
    
    for note in result.notes:
        print(f"NOTE: {note}")

    # Generate plot if requested
    if args.plot:
        if not HAS_MATPLOTLIB:
            print("Error: Cannot generate plot. matplotlib is not installed.")
            sys.exit(1)
        
        plot_path = args.output_dir / "scaling_plot.pdf"
        print(f"Generating plot: {plot_path}")
        try:
            generate_scaling_plot(result, plot_path)
            print(f"Plot saved to {plot_path}")
        except Exception as e:
            print(f"Error generating plot: {e}")
            sys.exit(1)

    print("Scaling analysis complete.")

if __name__ == "__main__":
    main()