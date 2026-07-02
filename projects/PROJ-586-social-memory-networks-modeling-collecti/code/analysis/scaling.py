import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
import json
import scipy.stats as stats
from scipy.optimize import curve_fit

# Ensure the path to parent code directory is available for imports if running standalone
# In a standard project run, this is handled by the environment setup.
if __name__ == "__main__" and "code" not in sys.path:
    code_root = Path(__file__).resolve().parent.parent
    if code_root.name == "code":
        sys.path.insert(0, str(code_root))

from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from data.loaders import load_experiment_results
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PowerLawFitResult:
    """Result of a power-law fit y = a * x^beta."""
    alpha: float  # Pre-factor 'a'
    beta: float   # Exponent 'beta'
    r_squared: float
    standard_error: float
    ci_lower: float  # 95% CI lower bound for beta
    ci_upper: float  # 95% CI upper bound for beta
    is_sublinear: bool  # True if beta < 1 (and CI confirms)
    n_points: int
    p_value: float


@dataclass
class ScalingAnalysisResult:
    """Container for the full scaling analysis results."""
    agent_counts: List[int]
    specialization_means: List[float]
    specialization_stds: List[float]
    retrieval_means: List[float]
    retrieval_stds: List[float]
    specialization_fit: Optional[PowerLawFitResult]
    retrieval_fit: Optional[PowerLawFitResult]
    notes: List[str] = field(default_factory=list)


def power_law_function(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """
    Power law function: y = a * x^b
    
    Args:
        x: Independent variable (agent count)
        a: Pre-factor
        b: Exponent
        
    Returns:
        y: Dependent variable value
    """
    return a * np.power(x, b)


def fit_power_law(x: np.ndarray, y: np.ndarray) -> PowerLawFitResult:
    """
    Fit a power law y = a * x^b to data using log-log linear regression.
    
    This method transforms the power law to a linear form:
    log(y) = log(a) + b * log(x)
    
    We then perform linear regression on the log-transformed data to estimate
    'b' (the exponent) and its confidence interval.
    
    Args:
        x: Independent variable values (must be > 0)
        y: Dependent variable values (must be > 0)
        
    Returns:
        PowerLawFitResult containing fitted parameters and statistics
    """
    if len(x) < 2:
        raise ValueError("Need at least 2 data points to fit a power law")
        
    # Filter out non-positive values to allow log transformation
    mask = (x > 0) & (y > 0)
    x_filtered = x[mask]
    y_filtered = y[mask]
    
    if len(x_filtered) < 2:
        raise ValueError("Need at least 2 positive data points to fit a power law")
        
    # Log-transform the data
    log_x = np.log(x_filtered)
    log_y = np.log(y_filtered)
    
    # Perform linear regression: log(y) = intercept + slope * log(x)
    # slope corresponds to beta, intercept corresponds to log(a)
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_x, log_y)
    
    # Calculate the exponent beta and its standard error
    beta = slope
    beta_se = std_err
    
    # Calculate 95% confidence interval for beta
    # Using t-distribution for small sample sizes
    n = len(x_filtered)
    dof = n - 2
    if dof <= 0:
        raise ValueError("Not enough degrees of freedom for confidence interval")
        
    t_critical = stats.t.ppf(0.975, dof)
    ci_lower = beta - t_critical * beta_se
    ci_upper = beta + t_critical * beta_se
    
    # Determine if the fit is sublinear (beta < 1)
    # We consider it sublinear if the upper bound of the 95% CI is < 1
    is_sublinear = ci_upper < 1.0
    
    # Calculate R-squared
    r_squared = r_value ** 2
    
    # Calculate pre-factor a
    alpha = np.exp(intercept)
    
    return PowerLawFitResult(
        alpha=alpha,
        beta=beta,
        r_squared=r_squared,
        standard_error=beta_se,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        is_sublinear=is_sublinear,
        n_points=n,
        p_value=p_value
    )


def load_scaling_data(results_dir: Path) -> pd.DataFrame:
    """
    Load and aggregate scaling experiment results.
    
    Args:
        results_dir: Directory containing experiment result CSV files
        
    Returns:
        DataFrame with columns: game_id, agent_count, specialization_index, retrieval_efficiency
    """
    # Look for scaling experiment results
    scaling_files = list(results_dir.glob("results_scaling_*.csv"))
    
    if not scaling_files:
        # Try generic scaling results file
        generic_file = results_dir / "results_scaling.csv"
        if generic_file.exists():
            scaling_files = [generic_file]
        else:
            # Fallback: try to find any results file with agent_count
            all_results = list(results_dir.glob("results_*.csv"))
            for f in all_results:
                try:
                    df = pd.read_csv(f)
                    if 'agent_count' in df.columns:
                        scaling_files = [f]
                        break
                except Exception:
                    continue
            
            if not scaling_files:
                raise FileNotFoundError(
                    f"No scaling result files found in {results_dir}. "
                    "Expected files like 'results_scaling_*.csv' or a file with 'agent_count' column."
                )
    
    # Load and combine results
    dfs = []
    for file_path in scaling_files:
        try:
            df = pd.read_csv(file_path)
            dfs.append(df)
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")
    
    if not dfs:
        raise FileNotFoundError("Could not load any scaling result files")
        
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Ensure required columns exist
    required_cols = ['agent_count', 'specialization_index', 'retrieval_efficiency']
    missing_cols = [col for col in required_cols if col not in combined_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in result files: {missing_cols}")
        
    return combined_df


def aggregate_metrics_by_agent_count(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Aggregate metrics by agent count.
    
    Args:
        df: DataFrame with agent_count, specialization_index, retrieval_efficiency
        
    Returns:
        Tuple of (agent_counts, spec_means, spec_stds, retrieval_means, retrieval_stds, counts)
    """
    grouped = df.groupby('agent_count').agg({
        'specialization_index': ['mean', 'std', 'count'],
        'retrieval_efficiency': ['mean', 'std']
    }).reset_index()
    
    # Flatten column names
    grouped.columns = ['agent_count', 'spec_mean', 'spec_std', 'spec_count', 'retrieval_mean', 'retrieval_std']
    
    agent_counts = grouped['agent_count'].values.astype(int)
    spec_means = grouped['spec_mean'].values
    spec_stds = grouped['spec_std'].values
    retrieval_means = grouped['retrieval_mean'].values
    retrieval_stds = grouped['retrieval_std'].values
    counts = grouped['spec_count'].values
    
    return agent_counts, spec_means, spec_stds, retrieval_means, retrieval_stds, counts


def run_scaling_analysis(results_dir: Path) -> ScalingAnalysisResult:
    """
    Run full scaling analysis on experiment results.
    
    Args:
        results_dir: Directory containing experiment result CSV files
        
    Returns:
        ScalingAnalysisResult with fitted power laws and statistics
    """
    logger.info(f"Loading scaling data from {results_dir}")
    df = load_scaling_data(results_dir)
    
    logger.info(f"Loaded {len(df)} records")
    
    agent_counts, spec_means, spec_stds, retrieval_means, retrieval_stds, counts = aggregate_metrics_by_agent_count(df)
    
    logger.info(f"Aggregated data for {len(agent_counts)} agent counts: {list(agent_counts)}")
    
    notes = []
    
    # Fit power law to specialization index
    specialization_fit = None
    if len(agent_counts) >= 2:
        try:
            logger.info("Fitting power law to specialization index...")
            specialization_fit = fit_power_law(agent_counts, spec_means)
            
            notes.append(
                f"Specialization scaling: beta = {specialization_fit.beta:.4f} "
                f"(95% CI: [{specialization_fit.ci_lower:.4f}, {specialization_fit.ci_upper:.4f}])"
            )
            
            if specialization_fit.is_sublinear:
                notes.append(
                    f"Specialization index shows SUBLINEAR scaling (beta < 1) with 95% confidence. "
                    f"Exponent beta = {specialization_fit.beta:.4f} indicates efficiency gains as agent count increases."
                )
            else:
                notes.append(
                    f"Specialization index does NOT show statistically significant sublinear scaling. "
                    f"95% CI [{specialization_fit.ci_lower:.4f}, {specialization_fit.ci_upper:.4f}] includes or exceeds 1.0."
                )
                
        except Exception as e:
            logger.error(f"Failed to fit specialization power law: {e}")
            notes.append(f"Failed to fit specialization power law: {e}")
    
    # Fit power law to retrieval efficiency
    retrieval_fit = None
    if len(agent_counts) >= 2:
        try:
            logger.info("Fitting power law to retrieval efficiency...")
            retrieval_fit = fit_power_law(agent_counts, retrieval_means)
            
            notes.append(
                f"Retrieval scaling: beta = {retrieval_fit.beta:.4f} "
                f"(95% CI: [{retrieval_fit.ci_lower:.4f}, {retrieval_fit.ci_upper:.4f}])"
            )
            
            if retrieval_fit.is_sublinear:
                notes.append(
                    f"Retrieval efficiency shows SUBLINEAR scaling (beta < 1) with 95% confidence."
                )
            else:
                notes.append(
                    f"Retrieval efficiency does NOT show statistically significant sublinear scaling."
                )
                
        except Exception as e:
            logger.error(f"Failed to fit retrieval power law: {e}")
            notes.append(f"Failed to fit retrieval power law: {e}")
    
    # Add note about limited data points
    if len(agent_counts) <= 3:
        notes.append(
            f"WARNING: Only {len(agent_counts)} data points available for power-law fitting. "
            f"Power-law fits with few points have limited statistical reliability. "
            f"Results should be interpreted with caution and validated with additional agent counts."
        )
    
    return ScalingAnalysisResult(
        agent_counts=list(agent_counts),
        specialization_means=list(spec_means),
        specialization_stds=list(spec_stds),
        retrieval_means=list(retrieval_means),
        retrieval_stds=list(retrieval_stds),
        specialization_fit=specialization_fit,
        retrieval_fit=retrieval_fit,
        notes=notes
    )


def generate_scaling_plot(result: ScalingAnalysisResult, output_path: Path) -> None:
    """
    Generate a scaling plot with fitted power-law curves.
    
    Args:
        result: ScalingAnalysisResult from run_scaling_analysis
        output_path: Path to save the plot PDF
    """
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    x = np.array(result.agent_counts)
    
    # Plot Specialization Index
    ax1.errorbar(
        x, 
        result.specialization_means, 
        yerr=result.specialization_stds,
        fmt='o', 
        capsize=5, 
        label='Measured',
        color='blue'
    )
    
    if result.specialization_fit:
        # Generate smooth curve for power law fit
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit = result.specialization_fit.alpha * np.power(x_fit, result.specialization_fit.beta)
        ax1.plot(x_fit, y_fit, 'r-', label=f'Power-law fit (β={result.specialization_fit.beta:.2f})')
        
        # Add annotation for sublinearity
        if result.specialization_fit.is_sublinear:
            ax1.annotate(
                f'Sublinear (β < 1)\n95% CI: [{result.specialization_fit.ci_lower:.2f}, {result.specialization_fit.ci_upper:.2f}]',
                xy=(0.05, 0.95),
                xycoords='axes fraction',
                fontsize=9,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            )
    
    ax1.set_xlabel('Number of Agents')
    ax1.set_ylabel('Specialization Index')
    ax1.set_title('Specialization Index Scaling')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot Retrieval Efficiency
    ax2.errorbar(
        x, 
        result.retrieval_means, 
        yerr=result.retrieval_stds,
        fmt='o', 
        capsize=5, 
        label='Measured',
        color='green'
    )
    
    if result.retrieval_fit:
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit = result.retrieval_fit.alpha * np.power(x_fit, result.retrieval_fit.beta)
        ax2.plot(x_fit, y_fit, 'r-', label=f'Power-law fit (β={result.retrieval_fit.beta:.2f})')
        
        if result.retrieval_fit.is_sublinear:
            ax2.annotate(
                f'Sublinear (β < 1)\n95% CI: [{result.retrieval_fit.ci_lower:.2f}, {result.retrieval_fit.ci_upper:.2f}]',
                xy=(0.05, 0.95),
                xycoords='axes fraction',
                fontsize=9,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            )
    
    ax2.set_xlabel('Number of Agents')
    ax2.set_ylabel('Retrieval Efficiency')
    ax2.set_title('Retrieval Efficiency Scaling')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Add overall note about data points
    fig.suptitle(
        f'Scaling Analysis: Collective Remembering in Multi-Agent Systems\n'
        f'Note: Based on {len(x)} agent counts. Power-law fits with few points have limited reliability.',
        fontsize=12,
        y=1.02
    )
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"Saved scaling plot to {output_path}")


def main():
    """Main entry point for scaling analysis."""
    parser = argparse.ArgumentParser(description='Run scaling analysis on multi-agent experiment results')
    parser.add_argument('--results-dir', type=str, default='results',
                      help='Directory containing experiment result CSV files')
    parser.add_argument('--output-dir', type=str, default='results',
                      help='Directory to save analysis results and plots')
    
    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir)
    
    if not results_dir.exists():
        logger.error(f"Results directory does not exist: {results_dir}")
        sys.exit(1)
    
    try:
        logger.info("Running scaling analysis...")
        result = run_scaling_analysis(results_dir)
        
        # Save results as JSON
        results_json = {
            'agent_counts': result.agent_counts,
            'specialization_means': result.specialization_means,
            'specialization_stds': result.specialization_stds,
            'retrieval_means': result.retrieval_means,
            'retrieval_stds': result.retrieval_stds,
            'specialization_fit': vars(result.specialization_fit) if result.specialization_fit else None,
            'retrieval_fit': vars(result.retrieval_fit) if result.retrieval_fit else None,
            'notes': result.notes
        }
        
        output_json_path = output_dir / 'scaling_analysis_results.json'
        with open(output_json_path, 'w') as f:
            json.dump(results_json, f, indent=2)
        logger.info(f"Saved results to {output_json_path}")
        
        # Generate plot
        plot_path = output_dir / 'scaling_plot.pdf'
        generate_scaling_plot(result, plot_path)
        
        # Print summary
        print("\n=== Scaling Analysis Summary ===")
        for note in result.notes:
            print(f"  - {note}")
        print(f"\nResults saved to: {output_json_path}")
        print(f"Plot saved to: {plot_path}")
        
    except Exception as e:
        logger.error(f"Scaling analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()