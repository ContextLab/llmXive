"""
Scaling analysis for social memory networks.

Implements power-law fitting for metric trends vs. agent count,
calculates confidence intervals for the exponent, and determines
sub-linearity.
"""
import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
import scipy.stats as stats
import scipy.optimize as optimize
import json

# Import local utilities if needed, but rely on standard libs + numpy/scipy
# Note: The API surface lists these imports for this file.

@dataclass
class PowerLawFitResult:
    """Result of fitting a power law y = a * x^beta."""
    beta: float
    beta_se: float
    ci_lower: float
    ci_upper: float
    r_squared: float
    is_sublinear: bool
    n_points: int
    alpha: float = 0.05  # Confidence level (95%)

@dataclass
class ScalingAnalysisResult:
    """Container for full scaling analysis results."""
    fit_results: Dict[str, PowerLawFitResult]
    raw_data: pd.DataFrame
    summary_stats: Dict[str, Any]
    sublinearity_note: str

def power_law_function(x: np.ndarray, a: float, beta: float) -> np.ndarray:
    """Power law function y = a * x^beta."""
    return a * np.power(x, beta)

def fit_power_law(x: np.ndarray, y: np.ndarray, 
                  method: str = "log_linear") -> PowerLawFitResult:
    """
    Fit a power law y = a * x^beta to the data.
    
    Args:
        x: Independent variable (agent count)
        y: Dependent variable (metric value)
        method: Fitting method ('log_linear' or 'nonlinear')
    
    Returns:
        PowerLawFitResult with parameters and confidence intervals.
    """
    if len(x) < 2:
        raise ValueError("At least 2 data points required for fitting.")
    
    if method == "log_linear":
        # Linearize: log(y) = log(a) + beta * log(x)
        # This is the standard approach for power-law fitting in this context
        log_x = np.log(x)
        log_y = np.log(y)
        
        # Fit linear model
        slope, intercept, r_value, p_value, std_err = stats.linregress(log_x, log_y)
        
        beta = slope
        beta_se = std_err
        r_squared = r_value ** 2
        
        # Calculate 95% confidence interval for beta
        # Using t-distribution for small sample sizes
        n = len(x)
        dof = n - 2
        if dof <= 0:
            raise ValueError("Not enough degrees of freedom for confidence interval.")
        
        t_crit = stats.t.ppf(1 - 0.025, dof)  # 95% CI
        ci_lower = beta - t_crit * beta_se
        ci_upper = beta + t_crit * beta_se
        
    elif method == "nonlinear":
        # Non-linear least squares fitting
        # Initial guess: a=1, beta=1
        try:
            popt, pcov = optimize.curve_fit(
                power_law_function, x, y, p0=[1.0, 1.0], 
                maxfev=5000, method='dogbox'
            )
            a, beta = popt
            perr = np.sqrt(np.diag(pcov))
            beta_se = perr[1]
            
            # Calculate R-squared for non-linear fit
            y_pred = power_law_function(x, *popt)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)
            
            # Confidence interval
            n = len(x)
            dof = n - 2
            t_crit = stats.t.ppf(1 - 0.025, dof)
            ci_lower = beta - t_crit * beta_se
            ci_upper = beta + t_crit * beta_se
            
        except Exception as e:
            # Fallback to log-linear if nonlinear fails
            return fit_power_law(x, y, method="log_linear")
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Determine sub-linearity: beta < 1
    # We check if the upper bound of CI is less than 1 for strong evidence,
    # or if the point estimate is less than 1 with the CI not crossing 1 significantly.
    # For this task, we define sub-linear if the point estimate beta < 1.
    is_sublinear = beta < 1.0
    
    return PowerLawFitResult(
        beta=beta,
        beta_se=beta_se,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        r_squared=r_squared,
        is_sublinear=is_sublinear,
        n_points=len(x),
        alpha=0.05
    )

def load_scaling_data(results_dir: Path) -> pd.DataFrame:
    """
    Load scaling experiment results from CSV files.
    
    Expected files: results_scaling_3.csv, results_scaling_5.csv, results_scaling_7.csv
    Or a single aggregated file if T027 produced one.
    """
    # Try to find the aggregated file first
    aggregated_path = results_dir / "results_scaling_aggregated.csv"
    if aggregated_path.exists():
        return pd.read_csv(aggregated_path)
    
    # Otherwise, load individual files and combine
    agent_counts = [3, 5, 7]
    dfs = []
    
    for count in agent_counts:
        file_path = results_dir / f"results_scaling_{count}.csv"
        if file_path.exists():
            df = pd.read_csv(file_path)
            df['agent_count'] = count
            dfs.append(df)
    
    if not dfs:
        raise FileNotFoundError("No scaling result files found in results directory.")
    
    return pd.concat(dfs, ignore_index=True)

def aggregate_metrics_by_agent_count(df: pd.DataFrame, 
                                     metric_cols: List[str] = None) -> pd.DataFrame:
    """
    Aggregate metrics by agent count, computing mean and std.
    
    Args:
        df: Raw results dataframe with 'agent_count' column
        metric_cols: List of metric columns to aggregate. Defaults to 
                    ['specialization_index', 'retrieval_efficiency']
    
    Returns:
        Aggregated dataframe with one row per agent count.
    """
    if metric_cols is None:
        metric_cols = ['specialization_index', 'retrieval_efficiency']
    
    # Filter to only relevant columns
    cols_to_use = ['agent_count'] + [c for c in metric_cols if c in df.columns]
    df_subset = df[cols_to_use].dropna()
    
    # Group by agent count and compute mean
    aggregated = df_subset.groupby('agent_count').agg({
        col: ['mean', 'std', 'count'] 
        for col in metric_cols if col in df_subset.columns
    }).reset_index()
    
    # Flatten column names
    aggregated.columns = ['agent_count'] + [
        f"{col}_{stat}" if stat != 'mean' else col 
        for col, stat in aggregated.columns[1:]
    ]
    
    return aggregated

def run_scaling_analysis(results_dir: Path, 
                         metric: str = 'specialization_index') -> ScalingAnalysisResult:
    """
    Run full scaling analysis for a given metric.
    
    Args:
        results_dir: Path to directory containing result CSVs
        metric: Which metric to analyze ('specialization_index' or 'retrieval_efficiency')
    
    Returns:
        ScalingAnalysisResult with fit results and summary.
    """
    # Load and aggregate data
    raw_data = load_scaling_data(results_dir)
    aggregated = aggregate_metrics_by_agent_count(raw_data, [metric])
    
    if len(aggregated) < 2:
        raise ValueError("Insufficient data points for scaling analysis.")
    
    x = aggregated['agent_count'].values.astype(float)
    y = aggregated[metric].values.astype(float)
    
    # Remove any NaN values
    mask = ~np.isnan(y)
    x = x[mask]
    y = y[mask]
    
    if len(x) < 2:
        raise ValueError("Insufficient valid data points after filtering.")
    
    # Fit power law
    fit_result = fit_power_law(x, y, method="log_linear")
    
    # Generate summary note
    note_parts = []
    note_parts.append(f"Power-law exponent β = {fit_result.beta:.3f} (95% CI: [{fit_result.ci_lower:.3f}, {fit_result.ci_upper:.3f}]).")
    
    if fit_result.is_sublinear:
        note_parts.append("The exponent is less than 1, indicating sub-linear scaling.")
        if fit_result.ci_upper < 1.0:
            note_parts.append("The 95% confidence interval lies entirely below 1, providing strong evidence for sub-linearity.")
        else:
            note_parts.append("While the point estimate suggests sub-linearity, the confidence interval includes 1, so the evidence is not statistically significant at the 95% level.")
    else:
        note_parts.append("The exponent is not less than 1, indicating linear or super-linear scaling.")
    
    note_parts.append(f"R² = {fit_result.r_squared:.3f}. Note: Only {fit_result.n_points} data points limit the reliability of the power-law fit.")
    
    sublinearity_note = " ".join(note_parts)
    
    return ScalingAnalysisResult(
        fit_results={metric: fit_result},
        raw_data=raw_data,
        summary_stats={
            'metric': metric,
            'agent_counts': list(x),
            'means': list(y),
            'n_points': fit_result.n_points
        },
        sublinearity_note=sublinearity_note
    )

def generate_scaling_plot(results_dir: Path, 
                          output_path: Optional[Path] = None,
                          metrics: List[str] = None) -> None:
    """
    Generate a scaling plot with fitted power-law curves.
    
    Args:
        results_dir: Path to results directory
        output_path: Path to save the plot. Defaults to results/scaling_plot.pdf
        metrics: List of metrics to plot. Defaults to standard metrics.
    """
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    
    if output_path is None:
        output_path = results_dir / "scaling_plot.pdf"
    
    if metrics is None:
        metrics = ['specialization_index', 'retrieval_efficiency']
    
    # Load data
    raw_data = load_scaling_data(results_dir)
    
    fig, axes = plt.subplots(1, len(metrics), figsize=(5 * len(metrics), 4))
    if len(metrics) == 1:
        axes = [axes]
    
    for idx, metric in enumerate(metrics):
        if metric not in raw_data.columns:
            continue
        
        ax = axes[idx]
        
        # Aggregate
        agg = aggregate_metrics_by_agent_count(raw_data, [metric])
        x = agg['agent_count'].values
        y = agg[metric].values
        
        # Fit and get result for annotation
        fit_res = fit_power_law(x, y)
        
        # Plot data points
        ax.scatter(x, y, s=100, alpha=0.7, label='Observed')
        
        # Plot fitted curve
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit = fit_res.beta  # This is just the exponent, need to reconstruct
        # Reconstruct a from the fit: log(a) = intercept
        log_x = np.log(x)
        log_y = np.log(y)
        _, intercept, _, _, _ = stats.linregress(log_x, log_y)
        a = np.exp(intercept)
        y_fit = a * np.power(x_fit, fit_res.beta)
        
        ax.plot(x_fit, y_fit, 'r--', linewidth=2, label=f'Power Law (β={fit_res.beta:.2f})')
        
        ax.set_xlabel('Number of Agents')
        ax.set_ylabel(metric.replace('_', ' ').title())
        ax.set_title(f'{metric.replace("_", " ").title()}\n{fit_res.beta:.3f} (95% CI: [{fit_res.ci_lower:.2f}, {fit_res.ci_upper:.2f}])')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Add sublinearity note
        if fit_res.is_sublinear:
            note = "Sub-linear (β < 1)"
        else:
            note = "Not sub-linear"
        ax.text(0.05, 0.95, note, transform=ax.transAxes, 
               fontsize=9, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Scaling plot saved to {output_path}")

def main():
    """Main entry point for scaling analysis CLI."""
    parser = argparse.ArgumentParser(description="Scaling analysis for social memory networks")
    parser.add_argument("--results-dir", type=str, default="data",
                      help="Directory containing result CSV files")
    parser.add_argument("--output-dir", type=str, default="results",
                      help="Directory to save analysis outputs")
    parser.add_argument("--metric", type=str, default="specialization_index",
                      choices=["specialization_index", "retrieval_efficiency"],
                      help="Metric to analyze")
    parser.add_argument("--generate-plot", action="store_true",
                      help="Generate scaling plot")
    
    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Run analysis
        result = run_scaling_analysis(results_dir, metric=args.metric)
        
        # Save results to JSON
        output_file = output_dir / f"scaling_analysis_{args.metric}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'fit': {
                    'beta': result.fit_results[args.metric].beta,
                    'beta_se': result.fit_results[args.metric].beta_se,
                    'ci_lower': result.fit_results[args.metric].ci_lower,
                    'ci_upper': result.fit_results[args.metric].ci_upper,
                    'r_squared': result.fit_results[args.metric].r_squared,
                    'is_sublinear': result.fit_results[args.metric].is_sublinear,
                    'n_points': result.fit_results[args.metric].n_points
                },
                'summary': result.summary_stats,
                'sublinearity_note': result.sublinearity_note
            }, f, indent=2)
        
        print(f"Analysis results saved to {output_file}")
        print(f"\n{result.sublinearity_note}")
        
        # Generate plot if requested
        if args.generate_plot:
            generate_scaling_plot(results_dir, output_dir / "scaling_plot.pdf")
            
    except Exception as e:
        print(f"Error during scaling analysis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()