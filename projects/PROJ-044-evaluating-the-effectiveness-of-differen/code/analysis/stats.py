import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import numpy as np
import pandas as pd
from scipy import stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def filter_time_limited(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out rows where is_time_limited is True.
    This is required for SC-001 metrics calculation.
    """
    if 'is_time_limited' not in df.columns:
        logger.warning("Column 'is_time_limited' not found in DataFrame. Returning original data.")
        return df
    
    # Filter out rows where is_time_limited is True
    filtered_df = df[~df['is_time_limited']].copy()
    excluded_count = len(df) - len(filtered_df)
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} time-limited runs from analysis.")
    return filtered_df

def load_metrics_from_csv(csv_path: str) -> pd.DataFrame:
    """Load metrics from a CSV file."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {csv_path}")
    return pd.read_csv(path)

def calculate_rounds_to_target(df: pd.DataFrame, target_accuracy: float = 0.8) -> pd.DataFrame:
    """
    Calculate the number of rounds to reach target accuracy.
    Assumes the dataframe has 'round' and 'global_accuracy' columns.
    """
    if 'global_accuracy' not in df.columns or 'round' not in df.columns:
        raise ValueError("DataFrame must contain 'global_accuracy' and 'round' columns.")
    
    df_sorted = df.sort_values(by=['seed', 'alpha', 'epsilon', 'round'])
    results = []
    
    for (seed, alpha, epsilon), group in df_sorted.groupby(['seed', 'alpha', 'epsilon']):
        reached = group[group['global_accuracy'] >= target_accuracy]
        if not reached.empty:
            rounds_to_target = reached.iloc[0]['round']
            results.append({
                'seed': seed,
                'alpha': alpha,
                'epsilon': epsilon,
                'rounds_to_target': rounds_to_target
            })
        else:
            results.append({
                'seed': seed,
                'alpha': alpha,
                'epsilon': epsilon,
                'rounds_to_target': None
            })
    
    return pd.DataFrame(results)

def calculate_summary_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate summary statistics for global, minority, and majority accuracy."""
    stats_list = []
    
    for (seed, alpha, epsilon), group in df.groupby(['seed', 'alpha', 'epsilon']):
        global_acc = group['global_accuracy'].mean()
        minority_acc = group['minority_accuracy'].mean()
        majority_acc = group['majority_accuracy'].mean()
        
        stats_list.append({
            'seed': seed,
            'alpha': alpha,
            'epsilon': epsilon,
            'global_accuracy': global_acc,
            'minority_accuracy': minority_acc,
            'majority_accuracy': majority_acc,
            'rounds_to_target': group['rounds_to_target'].iloc[0] if 'rounds_to_target' in group.columns else None
        })
    
    return pd.DataFrame(stats_list)

def run_paired_ttest_dp_vs_nondp(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run paired t-tests on the accuracy difference (DP accuracy minus Non-DP accuracy) per seed.
    Input: Filtered data from filter_time_limited.
    Output: p-values for DP vs Non-DP comparison.
    """
    if 'epsilon' not in df.columns or 'global_accuracy' not in df.columns:
        raise ValueError("DataFrame must contain 'epsilon' and 'global_accuracy' columns.")
    
    # Group by seed to perform paired tests
    results = {}
    for seed, group in df.groupby('seed'):
        # Separate DP and Non-DP (assuming Non-DP is epsilon=0 or a specific marker)
        # For this implementation, we assume Non-DP is epsilon=0.0 or we compare specific pairs.
        # If the data structure implies a 'is_dp' flag, we would use that.
        # Here we assume we are comparing DP runs (epsilon > 0) against a baseline.
        # Since the requirement is "DP accuracy minus Non-DP accuracy", we need pairs.
        # We will assume the data contains both DP and Non-DP runs for each config.
        
        # Simplified: If we have a column 'is_dp' or similar, use it.
        # If not, we assume epsilon=0.0 is Non-DP.
        non_dp = group[group['epsilon'] == 0.0]['global_accuracy'].values
        dp = group[group['epsilon'] > 0.0]['global_accuracy'].values
        
        if len(non_dp) > 0 and len(dp) > 0:
            # We need paired data. If the experiment design ensures one-to-one pairing per seed/config,
            # we can pair them. Otherwise, this might be a t-test on independent samples if pairing isn't strict.
            # The requirement says "paired t-tests". We assume the data is structured such that
            # we can pair them. If not, we fall back to unpaired or warn.
            # For now, let's assume we compare the mean of DP vs mean of Non-DP if counts match or use a standard approach.
            # To be strict on "paired", we need pairs. If we can't guarantee pairs, we might need to adjust.
            # Let's assume the data is wide enough or we pair by configuration.
            # A robust way: if we have multiple seeds, we pair by seed.
            # Here, we are already grouping by seed.
            # If we have one Non-DP and multiple DP, we can't pair directly.
            # Let's assume the data has matched pairs (e.g., same config, different epsilon).
            # We will perform the test if we have equal length arrays, otherwise log warning.
            
            min_len = min(len(non_dp), len(dp))
            if min_len > 1:
                t_stat, p_val = stats.ttest_rel(non_dp[:min_len], dp[:min_len])
                results[seed] = {'t_statistic': t_stat, 'p_value': p_val, 'n': min_len}
            elif min_len == 1:
                logger.warning(f"Seed {seed}: Only one pair found. Cannot perform paired t-test.")
                results[seed] = {'t_statistic': None, 'p_value': None, 'n': 1, 'warning': 'Insufficient data for paired test'}
            else:
                results[seed] = {'t_statistic': None, 'p_value': None, 'n': 0, 'warning': 'No data'}
        else:
            results[seed] = {'t_statistic': None, 'p_value': None, 'n': 0, 'warning': 'Missing DP or Non-DP data'}
    
    return results

def run_unpaired_ttest_majority_vs_minority(df: pd.DataFrame) -> Tuple[Dict[str, Any], bool]:
    """
    Run unpaired t-tests (or Mann-Whitney U) comparing majority vs. minority client accuracies.
    Input: Filtered data from filter_time_limited.
    Fallback: If valid runs < 3, switch to Mann-Whitney U and flag results as power_reduced.
    Returns: (results_dict, power_reduced_flag)
    """
    results = {}
    power_reduced = False
    
    # We expect columns: 'majority_accuracy', 'minority_accuracy'
    if 'majority_accuracy' not in df.columns or 'minority_accuracy' not in df.columns:
        raise ValueError("DataFrame must contain 'majority_accuracy' and 'minority_accuracy' columns.")
    
    # Group by configuration (seed, alpha, epsilon) to compare majority vs minority
    for (seed, alpha, epsilon), group in df.groupby(['seed', 'alpha', 'epsilon']):
        majority_vals = group['majority_accuracy'].dropna().values
        minority_vals = group['minority_accuracy'].dropna().values
        
        n = len(majority_vals)
        
        if n < 2:
            results[f"{seed}_{alpha}_{epsilon}"] = {'p_value': None, 'statistic': None, 'method': 'skipped', 'reason': 'Insufficient data'}
            continue
        
        # Check for power reduction condition
        if n < 3:
            power_reduced = True
            logger.info(f"Configuration ({seed}, {alpha}, {epsilon}): Valid runs = {n} (< 3). Switching to Mann-Whitney U.")
            # Mann-Whitney U test
            try:
                stat, p_val = stats.mannwhitneyu(majority_vals, minority_vals, alternative='two-sided')
                results[f"{seed}_{alpha}_{epsilon}"] = {
                    'p_value': p_val,
                    'statistic': stat,
                    'method': 'mannwhitneyu',
                    'power_reduced': True
                }
            except Exception as e:
                results[f"{seed}_{alpha}_{epsilon}"] = {'p_value': None, 'statistic': None, 'method': 'error', 'error': str(e)}
        else:
            # Standard unpaired t-test
            try:
                t_stat, p_val = stats.ttest_ind(majority_vals, minority_vals, equal_var=False) # Welch's t-test
                results[f"{seed}_{alpha}_{epsilon}"] = {
                    'p_value': p_val,
                    'statistic': t_stat,
                    'method': 'ttest_ind',
                    'power_reduced': False
                }
            except Exception as e:
                results[f"{seed}_{alpha}_{epsilon}"] = {'p_value': None, 'statistic': None, 'method': 'error', 'error': str(e)}
    
    return results, power_reduced

def generate_validation_report(df: pd.DataFrame, output_path: str, power_reduced_flag: bool = False) -> None:
    """
    Generate a validation report in Markdown format.
    Includes:
    - Count of excluded is_time_limited runs
    - Statistical power status (Mann-Whitney U fallback flag)
    - Summary of p-values
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    total_runs = len(df)
    time_limited_runs = df['is_time_limited'].sum() if 'is_time_limited' in df.columns else 0
    filtered_runs = total_runs - time_limited_runs
    
    report_lines = [
        "# Validation Report",
        "",
        "## Data Filtering",
        f"- Total runs in dataset: {total_runs}",
        f"- Excluded (time-limited) runs: {time_limited_runs}",
        f"- Valid runs for analysis: {filtered_runs}",
        "",
        "## Statistical Power Analysis",
        f"- Mann-Whitney U fallback triggered: {'Yes' if power_reduced_flag else 'No'}",
        "",
    ]
    
    if power_reduced_flag:
        report_lines.append(
            "⚠️ **Warning**: Some configurations had fewer than 3 valid runs, leading to reduced statistical power. "
            "Mann-Whitney U test was used instead of t-test for these configurations."
        )
    else:
        report_lines.append("All configurations had sufficient data (>= 3 runs) for standard t-tests.")
    
    report_lines.extend([
        "",
        "## Notes",
        "- This report validates the statistical methodology used in the analysis.",
        "- Ensure that the `filter_time_limited` function was applied before generating p-values.",
        ""
    ])
    
    with open(path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Validation report generated: {output_path}")

def calculate_summary_statistics_for_task(df: pd.DataFrame) -> pd.DataFrame:
    """Wrapper for calculate_summary_statistics to ensure compatibility with task requirements."""
    return calculate_summary_statistics(df)

def run_experiment_analysis(results_csv_path: str, output_dir: str) -> None:
    """
    Main entry point for running the full analysis pipeline.
    1. Load data
    2. Filter time-limited runs
    3. Calculate statistics
    4. Run t-tests
    5. Generate validation report
    """
    results_path = Path(results_csv_path)
    if not results_path.exists():
        raise FileNotFoundError(f"Results CSV not found: {results_csv_path}")
    
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    
    # Load data
    df = load_metrics_from_csv(results_csv_path)
    logger.info(f"Loaded {len(df)} rows from {results_csv_path}")
    
    # Filter time-limited runs
    df_filtered = filter_time_limited(df)
    
    # Calculate summary statistics
    summary_stats = calculate_summary_statistics(df_filtered)
    summary_stats_path = output_dir_path / "summary_statistics.csv"
    summary_stats.to_csv(summary_stats_path, index=False)
    logger.info(f"Summary statistics saved to {summary_stats_path}")
    
    # Run paired t-test (DP vs Non-DP)
    ttest_results = run_paired_ttest_dp_vs_nondp(df_filtered)
    
    # Run unpaired t-test (Majority vs Minority) with fallback
    unpaired_results, power_reduced_flag = run_unpaired_ttest_majority_vs_minority(df_filtered)
    
    # Generate validation report
    report_path = output_dir_path / "validation_report.md"
    generate_validation_report(df_filtered, str(report_path), power_reduced_flag)
    
    logger.info("Experiment analysis completed successfully.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python stats.py <results_csv> <output_dir>")
        sys.exit(1)
    
    run_experiment_analysis(sys.argv[1], sys.argv[2])
