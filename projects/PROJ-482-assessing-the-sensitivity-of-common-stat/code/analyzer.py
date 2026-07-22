import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, Dict, Any
import logging
import os
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_simulation_results(filepath: str = "data/processed/raw_pvalues.csv") -> pd.DataFrame:
    """
    Load the raw p-values and simulation metadata from the CSV file.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Simulation results file not found at {filepath}")
    
    logger.info(f"Loading simulation results from {filepath}")
    df = pd.read_csv(filepath)
    
    required_cols = ['sample_size', 'distribution_type', 'test_type', 'p_value', 'hypothesis_type']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {filepath}: {missing}")
    
    return df

def aggregate_results(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate results by (sample_size, distribution_type, test_type).
    Calculates the observed Type I error rate (proportion of rejections under Null).
    """
    logger.info("Aggregating simulation results")
    
    # Define rejection: p_value < alpha (0.05)
    alpha = 0.05
    df['rejected'] = (df['p_value'] < alpha).astype(int)
    
    # Filter for Type I error calculation (Hypothesis Type = Null)
    # Note: Depending on data, hypothesis_type might be 'Null' or 'Alternative'
    # We specifically need the rate of rejection when the Null is TRUE.
    # Assuming 'hypothesis_type' column distinguishes them.
    null_df = df[df['hypothesis_type'].str.lower().str.contains('null', na=False)]
    
    if null_df.empty:
        logger.warning("No Null hypothesis scenarios found in data. Cannot calculate Type I error.")
        # Fallback to full data if column naming is inconsistent, but log warning
        # This handles cases where the column might be named differently or data is mixed
        # However, strictly following the spec, we need Null scenarios.
        # If the data contains mixed types, we must isolate the Null ones.
        # If the column doesn't exist or is empty, we might need to infer or fail.
        # For robustness, let's assume if the specific filter fails, we check the raw data.
        # But the spec says "Calculate the Type I error rate for each sample size".
        # This implies we are looking at the Null scenarios.
        raise ValueError("No Null hypothesis scenarios found to calculate Type I error rate.")

    # Group by sample_size, distribution_type, test_type
    grouped = null_df.groupby(['sample_size', 'distribution_type', 'test_type'])
    
    agg_df = grouped.agg(
        total_replicates=('rejected', 'count'),
        rejections=('rejected', 'sum'),
        type_i_error_rate=('rejected', 'mean')
    ).reset_index()
    
    logger.info(f"Aggregated {len(agg_df)} unique configurations")
    return agg_df

def compute_bootstrap_ci(outcomes: np.ndarray, n_bootstrap: int = 1000, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Compute Bootstrap Resampling confidence interval for a proportion.
    
    Args:
        outcomes: Binary array (0 or 1) of outcomes.
        n_bootstrap: Number of bootstrap samples.
        alpha: Significance level for CI.
        
    Returns:
        Tuple (lower_bound, upper_bound)
    """
    n = len(outcomes)
    if n == 0:
        return (0.0, 0.0)
        
    boot_means = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(outcomes, size=n, replace=True)
        boot_means.append(np.mean(sample))
    
    boot_means = np.array(boot_means)
    lower = np.percentile(boot_means, 100 * alpha / 2)
    upper = np.percentile(boot_means, 100 * (1 - alpha / 2))
    
    return (lower, upper)

def analyze_stability_trend(
    aggregated_df: pd.DataFrame, 
    output_csv: str = "data/processed/stability_trend.csv",
    plot_path: Optional[str] = "data/processed/stability_trend.png"
) -> pd.DataFrame:
    """
    Calculate Type I error rate for each sample size and perform trend analysis.
    
    This function:
    1. Groups aggregated data by sample_size (and potentially other factors if needed).
    2. Calculates the mean Type I error rate per sample size.
    3. Performs a linear regression of error rate vs. log(sample_size) to verify stability.
    4. Outputs a CSV with the trend analysis results.
    5. Generates a plot of error rate vs. sample size.
    
    Args:
        aggregated_df: DataFrame from aggregate_results.
        output_csv: Path to save the trend analysis CSV.
        plot_path: Path to save the plot.
        
    Returns:
        DataFrame containing the trend analysis results.
    """
    logger.info("Analyzing stability trend...")
    
    # Ensure we have data
    if aggregated_df.empty:
        logger.error("Aggregated DataFrame is empty. Cannot analyze trend.")
        return pd.DataFrame()
    
    # Group by sample_size to get overall trend (ignoring distribution/test for the main trend plot
    # unless we want to facet. The task asks for "error rate for each sample size".
    # We will calculate the mean error rate across all distributions/tests for each n.
    trend_df = aggregated_df.groupby('sample_size').agg(
        mean_error_rate=('type_i_error_rate', 'mean'),
        std_error_rate=('type_i_error_rate', 'std'),
        count=('type_i_error_rate', 'count')
    ).reset_index()
    
    # Sort by sample size
    trend_df = trend_df.sort_values('sample_size')
    
    # Perform Trend Analysis: Linear Regression of Error Rate vs Log(Sample Size)
    # SC-002 Verification: We expect the error rate to stabilize around alpha (0.05) as n increases.
    # A significant slope might indicate instability or systematic bias.
    trend_df['log_n'] = np.log(trend_df['sample_size'])
    
    # Fit simple linear regression
    X = trend_df['log_n'].values
    y = trend_df['mean_error_rate'].values
    
    # Handle potential division by zero or constant X if only one sample size exists
    if len(np.unique(X)) < 2:
        logger.warning("Not enough unique sample sizes to perform regression trend analysis.")
        slope = 0.0
        intercept = y[0] if len(y) > 0 else 0.0
        r_squared = 0.0
        p_value = 1.0
    else:
        slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)
        r_squared = r_value**2
    
    # Add regression results to the dataframe for export
    trend_df['regression_slope'] = slope
    trend_df['regression_intercept'] = intercept
    trend_df['regression_p_value'] = p_value
    trend_df['regression_r_squared'] = r_squared
    
    # Calculate Bootstrap CI for the mean error rate at each sample size
    # We need to go back to the raw data or the aggregated data to get the distribution of errors?
    # The aggregated_df has 'type_i_error_rate' which is a mean of replicates.
    # To get a CI for the mean error rate, we would ideally need the raw replicates or the count.
    # Since we have 'rejections' and 'total_replicates', we can approximate or use the aggregated mean.
    # However, the task asks for "Bootstrap Resampling confidence intervals for final reporting" in T026.
    # Here in T026b, we are doing trend analysis. We will compute CI for the mean error rate.
    # Since we don't have the raw binary outcomes for the *mean* (we have the mean itself),
    # we can use the standard error if we assume normality, or we can reconstruct if we had raw data.
    # Given the aggregated data, we can use the standard deviation of the error rates across tests/distros
    # as a proxy for variability, or just report the mean.
    # Let's compute a CI for the mean error rate using the standard error of the mean (SEM) if we have multiple tests/distros per n.
    # Or, if we treat the 'mean_error_rate' as the point estimate, we can't bootstrap without the underlying distribution.
    # We will use the standard error of the mean (SEM) from the grouped std for the CI band in the plot.
    # For the CSV, we will just export the regression stats and the mean rates.
    
    # If we have multiple entries per sample_size (different tests/dists), we can compute CI on the mean_error_rate values.
    trend_df['ci_lower'] = np.nan
    trend_df['ci_upper'] = np.nan
    
    for n in trend_df['sample_size']:
        subset = aggregated_df[aggregated_df['sample_size'] == n]['type_i_error_rate']
        if len(subset) > 1:
            # Use the standard deviation of the error rates across tests/distributions
            # This reflects the variability of the test performance, not just the sampling error of one test.
            # This is a reasonable proxy for stability across test types.
            mean_val = subset.mean()
            std_val = subset.std()
            n_sub = len(subset)
            # 95% CI using t-distribution
            t_crit = stats.t.ppf(0.975, n_sub - 1)
            margin = t_crit * (std_val / np.sqrt(n_sub))
            trend_df.loc[trend_df['sample_size'] == n, 'ci_lower'] = mean_val - margin
            trend_df.loc[trend_df['sample_size'] == n, 'ci_upper'] = mean_val + margin
        elif len(subset) == 1:
            # If only one data point, CI is just the point (or undefined)
            mean_val = subset.iloc[0]
            trend_df.loc[trend_df['sample_size'] == n, 'ci_lower'] = mean_val
            trend_df.loc[trend_df['sample_size'] == n, 'ci_upper'] = mean_val
    
    # Save to CSV
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    trend_df.to_csv(output_csv, index=False)
    logger.info(f"Trend analysis saved to {output_csv}")
    
    # Generate Plot
    if plot_path:
        os.makedirs(os.path.dirname(plot_path), exist_ok=True)
        plt.figure(figsize=(10, 6))
        
        # Plot mean error rate
        plt.errorbar(
            trend_df['sample_size'], 
            trend_df['mean_error_rate'], 
            yerr=trend_df['ci_upper'] - trend_df['mean_error_rate'], # Approximate for plot
            fmt='o', 
            label='Mean Type I Error Rate', 
            capsize=5,
            color='blue'
        )
        
        # Plot nominal alpha
        plt.axhline(y=0.05, color='red', linestyle='--', label='Nominal Alpha (0.05)')
        
        # Plot regression line
        # Create a smooth line for regression
        x_reg = np.linspace(trend_df['log_n'].min(), trend_df['log_n'].max(), 100)
        y_reg = slope * x_reg + intercept
        plt.plot(np.exp(x_reg), y_reg, color='green', linestyle='-', label=f'Trend (Slope={slope:.4f})')
        
        plt.xlabel('Sample Size (n)')
        plt.ylabel('Type I Error Rate')
        plt.title('Stability of Type I Error Rate vs Sample Size')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xscale('log') # Log scale for x-axis often better for sample sizes
        
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Stability plot saved to {plot_path}")
    
    return trend_df

def analyze_log_pvalue_regression(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Placeholder for T027 regression analysis.
    """
    return {}

def export_regression_results(results: Dict[str, Any], filepath: str) -> None:
    """
    Placeholder for T027 export.
    """
    pass

def analyze_and_export(input_file: str = "data/processed/raw_pvalues.csv") -> None:
    """
    Main entry point for the analyzer to run aggregation, stability analysis, and export.
    """
    try:
        df = load_simulation_results(input_file)
        agg_df = aggregate_results(df)
        trend_df = analyze_stability_trend(agg_df)
        logger.info("Analysis and export completed successfully.")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    analyze_and_export()
