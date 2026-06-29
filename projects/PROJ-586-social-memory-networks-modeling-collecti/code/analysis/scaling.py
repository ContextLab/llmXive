"""
Scaling Analysis Module

Implements power-law fitting for metric trends vs. agent count.
Fits models of the form: y = α * N^β where N is agent count.

This addresses US-3: Scaling Analysis Across Agent Populations
"""

import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, asdict
import json

# scipy for curve fitting
from scipy.optimize import curve_fit
from scipy import stats

# Import from project modules
from data.loaders import load_experiment_results
from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class PowerLawFitResult:
    """Result of power-law fitting for a single metric."""
    metric_name: str
    alpha: float  # coefficient
    beta: float   # exponent
    r_squared: float
    p_value: float
    std_err_beta: float
    ci_lower_beta: float
    ci_upper_beta: float
    sublinear: bool  # True if β < 1
    
@dataclass
class ScalingAnalysisResult:
    """Complete scaling analysis result."""
    agent_counts: List[int]
    metrics_summary: Dict[str, Any]
    power_law_fits: Dict[str, PowerLawFitResult]
    overall_scaling_factor: float
    
def power_law_function(N: np.ndarray, alpha: float, beta: float) -> np.ndarray:
    """
    Power-law function: y = α * N^β
    
    Args:
        N: Agent counts
        alpha: Coefficient
        beta: Exponent
    
    Returns:
        Fitted values
    """
    return alpha * np.power(N, beta)

def fit_power_law(
    agent_counts: np.ndarray,
    metric_values: np.ndarray,
    confidence_level: float = 0.95
) -> Tuple[PowerLawFitResult, Dict[str, Any]]:
    """
    Fit a power-law model to metric trends across agent counts.
    
    Args:
        agent_counts: Array of agent counts (N)
        metric_values: Array of metric values for each agent count
        confidence_level: Confidence level for CI (default 0.95)
    
    Returns:
        Tuple of (PowerLawFitResult, fit diagnostics dict)
    """
    if len(agent_counts) < 2:
        raise ValueError("Need at least 2 data points for power-law fitting")
    
    # Initial guesses: alpha ≈ mean metric value, beta ≈ 0.8 (sublinear)
    initial_alpha = np.mean(metric_values)
    initial_beta = 0.8
    
    try:
        # Fit the power-law model
        popt, pcov = curve_fit(
            power_law_function,
            agent_counts,
            metric_values,
            p0=[initial_alpha, initial_beta],
            maxfev=5000
        )
        
        alpha, beta = popt
        alpha_err, beta_err = np.sqrt(np.diag(pcov))
        
        # Calculate R-squared
        y_pred = power_law_function(agent_counts, alpha, beta)
        ss_res = np.sum((metric_values - y_pred) ** 2)
        ss_tot = np.sum((metric_values - np.mean(metric_values)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        # Calculate p-value for beta (test H0: beta = 0)
        t_stat = beta / beta_err if beta_err > 0 else 0
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), len(agent_counts) - 2))
        
        # Calculate confidence interval for beta
        degrees_of_freedom = len(agent_counts) - 2
        t_critical = stats.t.ppf((1 + confidence_level) / 2, degrees_of_freedom)
        ci_lower_beta = beta - t_critical * beta_err
        ci_upper_beta = beta + t_critical * beta_err
        
        # Check for sublinearity (β < 1)
        sublinear = beta < 1
        
        fit_result = PowerLawFitResult(
            metric_name="",  # Will be set by caller
            alpha=alpha,
            beta=beta,
            r_squared=r_squared,
            p_value=p_value,
            std_err_beta=beta_err,
            ci_lower_beta=ci_lower_beta,
            ci_upper_beta=ci_upper_beta,
            sublinear=sublinear
        )
        
        diagnostics = {
            'n_points': len(agent_counts),
            'converged': True,
            'initial_guess': [initial_alpha, initial_beta],
            'final_params': [alpha, beta],
        }
        
        return fit_result, diagnostics
        
    except Exception as e:
        logger.warning(f"Power-law fitting failed: {e}")
        
        # Return NaN result on failure
        fit_result = PowerLawFitResult(
            metric_name="",
            alpha=np.nan,
            beta=np.nan,
            r_squared=np.nan,
            p_value=np.nan,
            std_err_beta=np.nan,
            ci_lower_beta=np.nan,
            ci_upper_beta=np.nan,
            sublinear=False
        )
        
        diagnostics = {
            'n_points': len(agent_counts),
            'converged': False,
            'error': str(e),
        }
        
        return fit_result, diagnostics

def load_scaling_data(
    results_dir: Path,
    agent_counts: List[int] = [3, 5, 7]
) -> pd.DataFrame:
    """
    Load and aggregate scaling experiment results.
    
    Args:
        results_dir: Directory containing experiment results
        agent_counts: List of agent counts to include
    
    Returns:
        DataFrame with agent_count, metric_name, and metric_value columns
    """
    all_data = []
    
    for n_agents in agent_counts:
        result_file = results_dir / f"results_n{n_agents}.csv"
        if result_file.exists():
            df = pd.read_csv(result_file)
            df['agent_count'] = n_agents
            all_data.append(df)
            logger.info(f"Loaded {len(df)} results for {n_agents} agents")
        else:
            logger.warning(f"Result file not found: {result_file}")
    
    if not all_data:
        raise FileNotFoundError("No scaling experiment results found")
    
    combined_df = pd.concat(all_data, ignore_index=True)
    return combined_df

def aggregate_metrics_by_agent_count(
    df: pd.DataFrame,
    metric_columns: List[str] = ['specialization_index', 'retrieval_efficiency']
) -> Dict[str, Dict[int, List[float]]]:
    """
    Aggregate metric values by agent count.
    
    Args:
        df: DataFrame with experiment results
        metric_columns: Columns containing metric values
    
    Returns:
        Nested dict: {metric_name: {agent_count: [values]}}
    """
    aggregated = {metric: {} for metric in metric_columns}
    
    for metric in metric_columns:
        if metric not in df.columns:
            logger.warning(f"Metric column '{metric}' not found in data")
            continue
        
        for n_agents in df['agent_count'].unique():
            subset = df[df['agent_count'] == n_agents]
            values = subset[metric].dropna().tolist()
            aggregated[metric][int(n_agents)] = values
    
    return aggregated

def run_scaling_analysis(
    results_dir: Path,
    agent_counts: List[int] = [3, 5, 7],
    metric_columns: List[str] = ['specialization_index', 'retrieval_efficiency'],
    confidence_level: float = 0.95
) -> ScalingAnalysisResult:
    """
    Run complete scaling analysis with power-law fitting.
    
    Args:
        results_dir: Directory containing experiment results
        agent_counts: Agent counts to analyze
        metric_columns: Metrics to analyze
        confidence_level: Confidence level for CI
    
    Returns:
        ScalingAnalysisResult with all fitting results
    """
    logger.info(f"Running scaling analysis for agent counts: {agent_counts}")
    
    # Load data
    df = load_scaling_data(results_dir, agent_counts)
    logger.info(f"Loaded {len(df)} game results")
    
    # Aggregate metrics
    aggregated = aggregate_metrics_by_agent_count(df, metric_columns)
    
    # Fit power laws
    power_law_fits = {}
    metrics_summary = {}
    
    for metric in metric_columns:
        if metric not in aggregated:
            continue
        
        agent_counts_arr = np.array(sorted(aggregated[metric].keys()))
        metric_means = []
        metric_stds = []
        
        for n in agent_counts_arr:
            values = aggregated[metric][n]
            if len(values) > 0:
                metric_means.append(np.mean(values))
                metric_stds.append(np.std(values))
            else:
                metric_means.append(np.nan)
                metric_stds.append(np.nan)
        
        metric_means = np.array(metric_means)
        metric_stds = np.array(metric_stds)
        
        # Fit power law to means
        fit_result, diagnostics = fit_power_law(
            agent_counts_arr, metric_means, confidence_level
        )
        fit_result.metric_name = metric
        
        power_law_fits[metric] = fit_result
        
        metrics_summary[metric] = {
            'means': metric_means.tolist(),
            'stds': metric_stds.tolist(),
            'n_per_count': [len(aggregated[metric][n]) for n in agent_counts_arr],
            'fit_r_squared': fit_result.r_squared,
            'fit_beta': fit_result.beta,
            'fit_alpha': fit_result.alpha,
            'sublinear': fit_result.sublinear,
            'ci_lower': fit_result.ci_lower_beta,
            'ci_upper': fit_result.ci_upper_beta,
            'p_value': fit_result.p_value
        }
        
        # Log sublinearity finding
        if not np.isnan(fit_result.beta):
            if fit_result.sublinear:
                logger.info(f"  {metric}: Sublinear scaling (β={fit_result.beta:.3f} < 1)")
            else:
                logger.info(f"  {metric}: Linear or superlinear scaling (β={fit_result.beta:.3f})")
    
    # Calculate overall scaling factor (average beta across metrics)
    betas = [fit.beta for fit in power_law_fits.values() if not np.isnan(fit.beta)]
    overall_scaling_factor = np.mean(betas) if betas else np.nan
    
    result = ScalingAnalysisResult(
        agent_counts=agent_counts,
        metrics_summary=metrics_summary,
        power_law_fits=power_law_fits,
        overall_scaling_factor=overall_scaling_factor
    )
    
    logger.info(f"Scaling analysis complete. Overall scaling factor: {overall_scaling_factor:.3f}")
    return result

def generate_scaling_plot(
    result: ScalingAnalysisResult,
    output_path: Path
) -> Path:
    """
    Generate scaling plot PDF with fitted power-law curves.
    
    Args:
        result: Scaling analysis result
        output_path: Path for output PDF
    
    Returns:
        Path to generated PDF
    """
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    
    # Create figure with subplots for each metric
    metrics = list(result.power_law_fits.keys())
    n_metrics = len(metrics)
    
    if n_metrics == 0:
        logger.warning("No metrics to plot")
        return output_path
    
    fig, axes = plt.subplots(1, n_metrics, figsize=(6 * n_metrics, 5))
    if n_metrics == 1:
        axes = [axes]
    
    for i, metric in enumerate(metrics):
        ax = axes[i]
        fit = result.power_law_fits[metric]
        
        # Plot data points with error bars
        means = result.metrics_summary[metric]['means']
        stds = result.metrics_summary[metric]['stds']
        
        ax.errorbar(
            result.agent_counts,
            means,
            yerr=stds,
            fmt='o',
            capsize=5,
            label='Experimental data',
            markersize=8,
            alpha=0.7
        )
        
        # Plot fitted power-law curve
        N_fit = np.linspace(min(result.agent_counts), max(result.agent_counts), 100)
        y_fit = power_law_function(N_fit, fit.alpha, fit.beta)
        ax.plot(N_fit, y_fit, 'r-', linewidth=2, label=f'Power-law fit (β={fit.beta:.3f})')
        
        # Add annotation
        annotation = (
            f"β = {fit.beta:.3f}\n"
            f"95% CI: [{fit.ci_lower_beta:.3f}, {fit.ci_upper_beta:.3f}]\n"
            f"R² = {fit.r_squared:.3f}\n"
            f"Sublinear: {'Yes' if fit.sublinear else 'No'}\n"
            f"(Note: Only 3 data points)"
        )
        
        ax.annotate(
            annotation,
            xy=(0.02, 0.98),
            xycoords='axes fraction',
            fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )
        
        ax.set_xlabel('Number of Agents (N)')
        ax.set_ylabel(metric.replace('_', ' ').title())
        ax.set_title(f'{metric.replace("_", " ").title()} Scaling')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Set log scale for x-axis to better visualize power law
        ax.set_xscale('log')
    
    # Add overall note about 3-point limitation
    fig.suptitle(
        'Scaling Analysis: Power-Law Fitting for Collective Memory Metrics\n'
        '(Caution: Only 3 agent counts limit power-law reliability)',
        fontsize=12,
        y=1.02
    )
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Scaling plot saved to {output_path}")
    return output_path

def main():
    """Main entry point for scaling analysis CLI."""
    parser = argparse.ArgumentParser(
        description='Scaling analysis for multi-agent memory networks'
    )
    parser.add_argument(
        '--results-dir',
        type=Path,
        default=Path('results'),
        help='Directory containing experiment results'
    )
    parser.add_argument(
        '--agent-counts',
        type=int,
        nargs='+',
        default=[3, 5, 7],
        help='Agent counts to analyze'
    )
    parser.add_argument(
        '--metrics',
        type=str,
        nargs='+',
        default=['specialization_index', 'retrieval_efficiency'],
        help='Metrics to analyze'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('scaling_plot.pdf'),
        help='Output PDF path'
    )
    parser.add_argument(
        '--confidence',
        type=float,
        default=0.95,
        help='Confidence level for CI'
    )
    
    args = parser.parse_args()
    
    # Ensure results directory exists
    if not args.results_dir.exists():
        logger.error(f"Results directory not found: {args.results_dir}")
        return 1
    
    # Run analysis
    result = run_scaling_analysis(
        args.results_dir,
        args.agent_counts,
        args.metrics,
        args.confidence
    )
    
    # Generate plot
    generate_scaling_plot(result, args.output)
    
    # Generate summary report
    summary_path = args.output.parent / 'scaling_analysis_summary.json'
    with open(summary_path, 'w') as f:
        json.dump({
            'agent_counts': result.agent_counts,
            'metrics_summary': result.metrics_summary,
            'overall_scaling_factor': result.overall_scaling_factor,
            'power_law_fits': {k: asdict(v) for k, v in result.power_law_fits.items()}
        }, f, indent=2, default=str)
    
    logger.info(f"Summary saved to {summary_path}")
    return 0

if __name__ == '__main__':
    sys.exit(main())