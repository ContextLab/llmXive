import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, Dict, Any
import logging
import os
from scipy import stats
import matplotlib.pyplot as plt
import json
from dataclasses import dataclass
from config import SimulationConfig, get_simulation_grid, LOG_EPSILON

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StabilityResult:
    sample_size: int
    distribution_type: str
    test_type: str
    error_rate: float
    ci_lower: float
    ci_upper: float
    slope: float
    p_value_slope: float
    is_stable: bool

def load_simulation_results() -> pd.DataFrame:
    """Load raw p-values from the simulation engine."""
    path = "data/processed/raw_pvalues.csv"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Simulation results not found at {path}. Run simulation first.")
    return pd.read_csv(path)

def aggregate_results(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate results by sample size, distribution, and test type."""
    def compute_error_rate(group):
        # For Type I error (null hypothesis), p < alpha is an error.
        # We assume the input data includes a column 'hypothesis_type' or we infer from effect size if available.
        # Based on T018 schema: sample_size, distribution_type, test_type, p_value, hypothesis_type.
        # If hypothesis_type is not present, we assume all are null for this specific stability check 
        # (or the caller filters for null scenarios).
        if 'hypothesis_type' in group.columns:
            null_mask = group['hypothesis_type'].str.lower().str.contains('null')
            null_group = group[null_mask]
            if len(null_group) == 0:
                return pd.Series({'error_rate': np.nan, 'count': 0})
            errors = (null_group['p_value'] < 0.05).sum()
            total = len(null_group)
        else:
            # Fallback: assume all are null if column missing (strict for T026b context)
            errors = (group['p_value'] < 0.05).sum()
            total = len(group)
        
        rate = errors / total if total > 0 else np.nan
        return pd.Series({'error_rate': rate, 'count': total})

    agg = df.groupby(['sample_size', 'distribution_type', 'test_type']).apply(compute_error_rate).reset_index()
    return agg

def compute_bootstrap_ci(outcomes: np.ndarray, n_resamples: int = 1000, alpha: float = 0.05) -> Tuple[float, float]:
    """Compute bootstrap confidence interval for binary outcomes (error vs correct)."""
    n = len(outcomes)
    if n == 0:
        return (np.nan, np.nan)
    
    boot_means = []
    for _ in range(n_resamples):
        sample = np.random.choice(outcomes, size=n, replace=True)
        boot_means.append(np.mean(sample))
    
    boot_means = np.array(boot_means)
    lower = np.percentile(boot_means, 100 * alpha / 2)
    upper = np.percentile(boot_means, 100 * (1 - alpha / 2))
    return (lower, upper)

def analyze_stability_trend(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze stability by calculating Type I error rate for each sample size.
    Perform linear regression of error rate vs sample size.
    """
    results = []
    
    # Ensure we are working with null hypothesis data only for Type I error stability
    if 'hypothesis_type' in df.columns:
        df_null = df[df['hypothesis_type'].str.lower().str.contains('null')].copy()
    else:
        df_null = df.copy()
    
    if df_null.empty:
        logger.warning("No null hypothesis data found for stability analysis.")
        return pd.DataFrame()

    grouped = df_null.groupby(['sample_size', 'distribution_type', 'test_type'])
    
    for (n, dist, test), group in grouped:
        if len(group) < 2:
            continue
        
        # Calculate error rate
        errors = (group['p_value'] < 0.05).sum()
        total = len(group)
        error_rate = errors / total
        
        # Bootstrap CI for this specific point
        outcomes = (group['p_value'] < 0.05).astype(int).values
        ci_lower, ci_upper = compute_bootstrap_ci(outcomes)
        
        results.append({
            'sample_size': n,
            'distribution_type': dist,
            'test_type': test,
            'error_rate': error_rate,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'count': total
        })
    
    result_df = pd.DataFrame(results)
    if result_df.empty:
        return result_df

    # Perform trend analysis (Linear Regression) for each (distribution, test) pair
    trend_results = []
    
    for (dist, test), sub_df in result_df.groupby(['distribution_type', 'test_type']):
        if len(sub_df) < 2:
            continue
        
        X = sub_df['sample_size'].values
        y = sub_df['error_rate'].values
        
        # Linear regression
        slope, intercept, r_value, p_value_slope, std_err = stats.linregress(X, y)
        
        # Robustness check: SC-002 requires slope < 0.01 (absolute value usually, but spec says slope < 0.01)
        # We interpret this as the magnitude of the trend. If slope is negative, it's stabilizing downwards.
        # We check if the absolute trend is small enough.
        is_stable = abs(slope) < 0.01
        
        trend_results.append({
            'distribution_type': dist,
            'test_type': test,
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_value**2,
            'p_value_slope': p_value_slope,
            'is_stable': is_stable
        })
    
    trend_df = pd.DataFrame(trend_results)
    return trend_df

def plot_stability_trend(result_df: pd.DataFrame, trend_df: pd.DataFrame) -> str:
    """Generate a plot of error rate vs sample size with trend lines."""
    if result_df.empty:
        logger.warning("No data to plot for stability trend.")
        return ""
    
    plt.figure(figsize=(10, 6))
    
    # Group by distribution and test to plot separate lines
    for (dist, test), sub_df in result_df.groupby(['distribution_type', 'test_type']):
        sub_df = sub_df.sort_values('sample_size')
        plt.errorbar(
            sub_df['sample_size'], 
            sub_df['error_rate'], 
            yerr=[sub_df['error_rate'] - sub_df['ci_lower'], sub_df['ci_upper'] - sub_df['error_rate']],
            label=f'{dist} - {test}',
            capsize=5,
            marker='o'
        )
        
        # Add trend line
        trend_row = trend_df[(trend_df['distribution_type'] == dist) & (trend_df['test_type'] == test)]
        if not trend_row.empty:
            slope = trend_row['slope'].values[0]
            intercept = trend_row['intercept'].values[0]
            X = sub_df['sample_size'].values
            plt.plot(X, slope * X + intercept, linestyle='--', alpha=0.7)
    
    plt.xlabel('Sample Size (n)')
    plt.ylabel('Type I Error Rate')
    plt.title('Stability Trend: Error Rate vs Sample Size')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    output_dir = "data/processed/plots"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "stability_trend.png")
    plt.savefig(output_path)
    plt.close()
    
    logger.info(f"Stability trend plot saved to {output_path}")
    return output_path

def export_stability_results(result_df: pd.DataFrame, trend_df: pd.DataFrame) -> str:
    """Export stability analysis results to CSV."""
    if result_df.empty or trend_df.empty:
        logger.warning("No data to export for stability results.")
        return ""
    
    # Merge results with trend info for a comprehensive report
    # We join on distribution_type and test_type
    merged = result_df.merge(trend_df, on=['distribution_type', 'test_type'], how='left')
    
    output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "stability_trend.csv")
    merged.to_csv(output_path, index=False)
    
    logger.info(f"Stability trend results exported to {output_path}")
    return output_path

def analyze_and_export() -> Dict[str, Any]:
    """Main entry point for T026b: Stability Measurement."""
    logger.info("Starting stability measurement analysis (T026b)...")
    
    # 1. Load data
    df = load_simulation_results()
    
    # 2. Aggregate by sample size
    agg_df = aggregate_results(df)
    
    # 3. Analyze stability trend
    trend_df = analyze_stability_trend(df)
    
    # 4. Generate plot
    plot_path = plot_stability_trend(agg_df, trend_df)
    
    # 5. Export results
    csv_path = export_stability_results(agg_df, trend_df)
    
    # 6. Verify robustness claim (SC-002)
    all_stable = trend_df['is_stable'].all() if not trend_df.empty else False
    summary = {
        'total_scenarios_analyzed': len(trend_df),
        'stable_scenarios': trend_df['is_stable'].sum() if not trend_df.empty else 0,
        'all_stable': all_stable,
        'plot_path': plot_path,
        'csv_path': csv_path
    }
    
    logger.info(f"Stability analysis complete. All stable: {all_stable}")
    return summary

def main():
    """CLI entry point for stability analysis."""
    result = analyze_and_export()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
