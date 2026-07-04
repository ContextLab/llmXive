"""
Statistical analysis module for compiler optimization benchmarks.

Implements block-averaging, Welch's t-test, and null hypothesis testing
for latency distributions across different optimization configurations.
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_latency_data(
    raw_logs_dir: str,
    stability_metrics_path: str,
    exclude_unstable: bool = True
) -> pd.DataFrame:
    """
    Load latency data from raw logs and merge with stability metrics.
    
    Args:
        raw_logs_dir: Directory containing JSONL raw log files
        stability_metrics_path: Path to stability metrics CSV
        exclude_unstable: If True, exclude configurations marked as unstable
        
    Returns:
        DataFrame with latency and stability information
    """
    raw_logs_path = Path(raw_logs_dir)
    if not raw_logs_path.exists():
        raise FileNotFoundError(f"Raw logs directory not found: {raw_logs_dir}")
    
    # Load all raw log files
    latency_data = []
    for log_file in raw_logs_path.glob("*.jsonl"):
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        latency_data.append({
                            'config_id': record.get('config_id'),
                            'median': record.get('median'),
                            'p95': record.get('p95'),
                            'iterations': record.get('iterations'),
                            'downsampled_flag': record.get('downsampled_flag', False)
                        })
        except Exception as e:
            logger.warning(f"Error reading {log_file}: {e}")
    
    df = pd.DataFrame(latency_data)
    if df.empty:
        logger.warning("No latency data found in raw logs")
        return df
    
    # Load stability metrics if provided
    if stability_metrics_path and os.path.exists(stability_metrics_path):
        stability_df = pd.read_csv(stability_metrics_path)
        # Merge on config_id
        df = df.merge(
            stability_df[['config_id', 'status']],
            on='config_id',
            how='left'
        )
        
        if exclude_unstable:
            # Filter out unstable configurations
            unstable_count = len(df[df['status'] == 'unstable'])
            df = df[df['status'] != 'unstable']
            logger.info(f"Excluded {unstable_count} unstable configurations")
    
    return df

def compute_block_averages(
    df: pd.DataFrame,
    config_col: str = 'config_id',
    latency_col: str = 'median',
    block_size: int = 10
) -> pd.DataFrame:
    """
    Compute block averages for latency distributions to ensure statistical power.
    
    Args:
        df: DataFrame with latency measurements
        config_col: Column name for configuration ID
        latency_col: Column name for latency values
        block_size: Number of measurements per block
        
    Returns:
        DataFrame with block-averaged latencies
    """
    if df.empty:
        return df
    
    block_averages = []
    
    for config_id, group in df.groupby(config_col):
        latencies = group[latency_col].values
        
        # Create blocks
        n_blocks = len(latencies) // block_size
        if n_blocks == 0:
            # If fewer than block_size measurements, use all as one block
            block_averages.append({
                config_col: config_id,
                'block_avg_latency': np.mean(latencies),
                'block_std': np.std(latencies),
                'n_measurements': len(latencies)
            })
        else:
            for i in range(n_blocks):
                block_start = i * block_size
                block_end = block_start + block_size
                block_data = latencies[block_start:block_end]
                block_averages.append({
                    config_col: config_id,
                    'block_avg_latency': np.mean(block_data),
                    'block_std': np.std(block_data),
                    'n_measurements': block_size
                })
            
            # Handle remaining measurements
            remaining = len(latencies) - (n_blocks * block_size)
            if remaining > 0:
                block_averages.append({
                    config_col: config_id,
                    'block_avg_latency': np.mean(latencies[n_blocks * block_size:]),
                    'block_std': np.std(latencies[n_blocks * block_size:]),
                    'n_measurements': remaining
                })
    
    return pd.DataFrame(block_averages)

def aggregate_block_averages(
    block_df: pd.DataFrame,
    config_col: str = 'config_id'
) -> pd.DataFrame:
    """
    Aggregate block averages to compute overall statistics per configuration.
    
    Args:
        block_df: DataFrame with block-averaged data
        config_col: Column name for configuration ID
        
    Returns:
        DataFrame with aggregated statistics per configuration
    """
    if block_df.empty:
        return block_df
    
    aggregated = block_df.groupby(config_col).agg({
        'block_avg_latency': ['mean', 'std', 'count', 'min', 'max'],
        'block_std': 'mean'
    }).reset_index()
    
    # Flatten column names
    aggregated.columns = [
        config_col, 'overall_mean', 'overall_std', 'n_blocks', 'min_latency', 'max_latency', 'avg_block_std'
    ]
    
    return aggregated

def welch_ttest(
    sample1: np.ndarray,
    sample2: np.ndarray,
    alternative: str = 'two-sided'
) -> Tuple[float, float]:
    """
    Perform Welch's Independent Samples t-test.
    
    This test is appropriate for comparing independent binaries with
    potentially different variances and sample sizes.
    
    Args:
        sample1: First sample array
        sample2: Second sample array
        alternative: Type of test ('two-sided', 'greater', 'less')
        
    Returns:
        Tuple of (t-statistic, p-value)
    """
    if len(sample1) < 2 or len(sample2) < 2:
        logger.warning("Insufficient samples for t-test (need at least 2 per group)")
        return 0.0, 1.0
    
    try:
        t_stat, p_val = stats.ttest_ind(
            sample1, sample2,
            equal_var=False,  # Welch's t-test
            alternative=alternative
        )
        return float(t_stat), float(p_val)
    except Exception as e:
        logger.error(f"Error in Welch's t-test: {e}")
        return 0.0, 1.0

def compare_configurations(
    df: pd.DataFrame,
    config1: str,
    config2: str,
    latency_col: str = 'block_avg_latency',
    config_col: str = 'config_id',
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Compare two configurations using Welch's t-test.
    
    Args:
        df: DataFrame with block-averaged latencies
        config1: First configuration ID
        config2: Second configuration ID
        latency_col: Column name for latency values
        config_col: Column name for configuration ID
        alpha: Significance level for hypothesis test
        
    Returns:
        Dictionary with test results and hypothesis decision
    """
    sample1 = df[df[config_col] == config1][latency_col].values
    sample2 = df[df[config_col] == config2][latency_col].values
    
    if len(sample1) == 0 or len(sample2) == 0:
        return {
            'config1': config1,
            'config2': config2,
            'sample1_size': len(sample1),
            'sample2_size': len(sample2),
            't_statistic': None,
            'p_value': None,
            'reject_null': False,
            'conclusion': 'Insufficient data for comparison'
        }
    
    t_stat, p_val = welch_ttest(sample1, sample2)
    reject_null = p_val < alpha
    
    # Formulate conclusion
    if reject_null:
        if np.mean(sample1) < np.mean(sample2):
            conclusion = f"Reject H0: {config1} is significantly faster than {config2} (p={p_val:.4f})"
        else:
            conclusion = f"Reject H0: {config2} is significantly faster than {config1} (p={p_val:.4f})"
    else:
        conclusion = f"Fail to reject H0: No significant difference between {config1} and {config2} (p={p_val:.4f})"
    
    return {
        'config1': config1,
        'config2': config2,
        'sample1_size': len(sample1),
        'sample2_size': len(sample2),
        'mean1': float(np.mean(sample1)),
        'mean2': float(np.mean(sample2)),
        'std1': float(np.std(sample1)),
        'std2': float(np.std(sample2)),
        't_statistic': t_stat,
        'p_value': p_val,
        'alpha': alpha,
        'reject_null': reject_null,
        'conclusion': conclusion
    }

def generate_comparison_report(
    df: pd.DataFrame,
    alpha: float = 0.05,
    output_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Generate a comprehensive comparison report for all configuration pairs.
    
    Args:
        df: DataFrame with block-averaged latencies
        alpha: Significance level
        output_path: Optional path to save report as JSON
        
    Returns:
        List of comparison results for each pair
    """
    if df.empty:
        logger.warning("Empty DataFrame provided for comparison")
        return []
    
    configs = df['config_id'].unique()
    comparisons = []
    
    logger.info(f"Generating comparisons for {len(configs)} configurations")
    
    for i in range(len(configs)):
        for j in range(i + 1, len(configs)):
            result = compare_configurations(
                df, 
                configs[i], 
                configs[j], 
                alpha=alpha
            )
            comparisons.append(result)
            
            # Log each comparison
            logger.info(f"Comparison: {configs[i]} vs {configs[j]}")
            logger.info(f"  P-value: {result['p_value']:.4f}")
            logger.info(f"  Reject H0: {result['reject_null']}")
            logger.info(f"  Conclusion: {result['conclusion']}")
    
    # Save report if path provided
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(comparisons, f, indent=2)
        logger.info(f"Comparison report saved to {output_path}")
    
    return comparisons

def main():
    """
    Main entry point for statistical analysis.
    
    Demonstrates loading data, computing block averages, and performing
    Welch's t-test comparisons between configurations.
    """
    # Example usage with default paths
    raw_logs_dir = "data/intermediates/raw_logs"
    stability_metrics_path = "data/results/stability_metrics.csv"
    output_report_path = "data/results/statistical_comparison.json"
    
    logger.info("Starting statistical analysis")
    
    try:
        # Load data
        df = load_latency_data(raw_logs_dir, stability_metrics_path)
        if df.empty:
            logger.warning("No data loaded, exiting")
            return
        
        logger.info(f"Loaded {len(df)} latency records")
        
        # Compute block averages
        block_df = compute_block_averages(df)
        logger.info(f"Computed {len(block_df)} block averages")
        
        # Aggregate results
        aggregated_df = aggregate_block_averages(block_df)
        logger.info(f"Aggregated to {len(aggregated_df)} configurations")
        
        # Generate comparison report
        comparisons = generate_comparison_report(
            block_df,
            alpha=0.05,
            output_path=output_report_path
        )
        
        logger.info(f"Generated {len(comparisons)} pairwise comparisons")
        
        # Print summary
        significant_count = sum(1 for c in comparisons if c['reject_null'])
        logger.info(f"Significant differences found: {significant_count}/{len(comparisons)}")
        
    except Exception as e:
        logger.error(f"Error in statistical analysis: {e}")
        raise

if __name__ == "__main__":
    main()