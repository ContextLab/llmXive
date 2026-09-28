import logging
import json
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, Set
import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)

def load_metrics_from_csv(file_path: str) -> pd.DataFrame:
    """
    Load metrics from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        DataFrame containing the metrics
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} rows from {file_path}")
    return df

def filter_time_limited(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out rows where is_time_limited is True.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Filtered DataFrame excluding time-limited runs
    """
    if 'is_time_limited' not in df.columns:
        logger.warning("Column 'is_time_limited' not found in DataFrame. Returning original data.")
        return df
    
    filtered_df = df[~df['is_time_limited']].copy()
    excluded_count = len(df) - len(filtered_df)
    logger.info(f"Filtered out {excluded_count} time-limited runs. Remaining: {len(filtered_df)}")
    return filtered_df

def filter_utility_collapse(df: pd.DataFrame, epsilon_threshold: float = 0.05, 
                             random_guessing_threshold: Optional[float] = None) -> pd.DataFrame:
    """
    Filter out rows exhibiting "utility collapse" as per FR-006.
    
    Utility collapse is detected when:
    1. epsilon < epsilon_threshold (extremely low privacy budget)
    2. accuracy < random_guessing_threshold (performance no better than random)
    
    Args:
        df: Input DataFrame (assumed to be already filtered by time)
        epsilon_threshold: Minimum epsilon threshold (default 0.05)
        random_guessing_threshold: Accuracy threshold for random guessing.
            If None, will be calculated as 1/num_classes based on the data.
            
    Returns:
        Filtered DataFrame excluding utility collapse cases
    """
    if 'epsilon' not in df.columns or 'accuracy' not in df.columns:
        raise ValueError("DataFrame must contain 'epsilon' and 'accuracy' columns")
    
    # Calculate random guessing threshold if not provided
    if random_guessing_threshold is None:
        # Estimate number of classes from the data if possible
        # We look for a column that might indicate num_classes or infer from accuracy distribution
        if 'num_classes' in df.columns:
            # If we have explicit num_classes, use the max
            num_classes = df['num_classes'].max()
            random_guessing_threshold = 1.0 / num_classes
            logger.info(f"Inferred num_classes={num_classes}, random_guessing_threshold={random_guessing_threshold}")
        else:
            # Fallback: assume 10 classes (standard for FEMNIST)
            # This is a conservative estimate for FEMNIST
            random_guessing_threshold = 1.0 / 10
            logger.warning(f"num_classes column not found. Using default random_guessing_threshold={random_guessing_threshold} (assumed 10 classes)")
    
    # Identify rows with utility collapse
    epsilon_condition = df['epsilon'] < epsilon_threshold
    
    # Handle accuracy column - ensure it's numeric
    accuracy_numeric = pd.to_numeric(df['accuracy'], errors='coerce')
    accuracy_condition = accuracy_numeric < random_guessing_threshold
    
    collapse_mask = epsilon_condition | accuracy_condition
    collapsed_count = collapse_mask.sum()
    
    filtered_df = df[~collapse_mask].copy()
    
    logger.info(f"Utility collapse filter: excluded {collapsed_count} rows (epsilon < {epsilon_threshold} OR accuracy < {random_guessing_threshold})")
    logger.info(f"Remaining rows after utility collapse filter: {len(filtered_df)}")
    
    # Log some details about excluded rows if any
    if collapsed_count > 0:
        excluded_rows = df[collapse_mask]
        logger.debug(f"Excluded epsilon values: {excluded_rows['epsilon'].unique()}")
        logger.debug(f"Excluded accuracy range: [{excluded_rows['accuracy'].min()}, {excluded_rows['accuracy'].max()}]")
    
    return filtered_df

def calculate_rounds_to_target(df: pd.DataFrame, target_accuracy: float = 0.8) -> pd.DataFrame:
    """
    Calculate rounds to reach target accuracy for each configuration.
    
    Args:
        df: DataFrame with training metrics
        target_accuracy: Target accuracy threshold
        
    Returns:
        DataFrame with rounds_to_target column
    """
    if 'rounds' not in df.columns or 'accuracy' not in df.columns:
        logger.warning("Required columns 'rounds' or 'accuracy' not found. Returning original DataFrame.")
        return df
    
    # Group by configuration and find first round meeting target
    def find_target_round(group):
        group_sorted = group.sort_values('rounds')
        target_reached = group_sorted[group_sorted['accuracy'] >= target_accuracy]
        if len(target_reached) > 0:
            return target_reached.iloc[0]['rounds']
        return None  # Target not reached
    
    df['rounds_to_target'] = df.groupby(['seed', 'alpha', 'epsilon', 'is_dp'])['rounds', 'accuracy'].transform(
        lambda x: find_target_round(x) if hasattr(x, 'iloc') else x
    )
    
    # Alternative approach if the above doesn't work as expected
    # Reset and calculate properly
    result_df = df.copy()
    result_df['rounds_to_target'] = np.nan
    
    for (seed, alpha, epsilon, is_dp), group in df.groupby(['seed', 'alpha', 'epsilon', 'is_dp']):
        group_sorted = group.sort_values('rounds')
        target_reached = group_sorted[group_sorted['accuracy'] >= target_accuracy]
        if len(target_reached) > 0:
            target_round = target_reached.iloc[0]['rounds']
            result_df.loc[df.index.isin(group.index), 'rounds_to_target'] = target_round
    
    logger.info(f"Calculated rounds_to_target for {result_df['rounds_to_target'].notna().sum()} configurations")
    return result_df

def run_paired_ttest_dp_vs_nondp(df: pd.DataFrame) -> Tuple[float, float, Dict[str, Any]]:
    """
    Run paired t-tests comparing DP vs Non-DP accuracy for each configuration.
    
    Args:
        df: DataFrame containing both DP and Non-DP results
        
    Returns:
        Tuple of (mean_p_value, min_p_value, metadata_dict)
    """
    if 'is_dp' not in df.columns or 'accuracy' not in df.columns:
        raise ValueError("DataFrame must contain 'is_dp' and 'accuracy' columns")
    
    p_values = []
    configurations = df.groupby(['alpha', 'epsilon']).groups.keys()
    
    results_by_config = {}
    
    for alpha, epsilon in configurations:
        config_df = df[(df['alpha'] == alpha) & (df['epsilon'] == epsilon)]
        
        dp_results = config_df[config_df['is_dp'] == True]['accuracy'].values
        nondp_results = config_df[config_df['is_dp'] == False]['accuracy'].values
        
        # Check if we have paired data (same seeds)
        dp_seeds = set(config_df[config_df['is_dp'] == True]['seed'].values)
        nondp_seeds = set(config_df[config_df['is_dp'] == False]['seed'].values)
        common_seeds = dp_seeds.intersection(nondp_seeds)
        
        if len(common_seeds) < 2:
            logger.warning(f"Insufficient paired data for alpha={alpha}, epsilon={epsilon}. Seeds: {common_seeds}")
            results_by_config[(alpha, epsilon)] = {'p_value': np.nan, 'power_reduced': True, 'reason': 'insufficient_pairs'}
            continue
        
        # Extract paired values
        paired_dp = []
        paired_nondp = []
        
        for seed in sorted(common_seeds):
            dp_val = config_df[(config_df['seed'] == seed) & (config_df['is_dp'] == True)]['accuracy'].values
            nondp_val = config_df[(config_df['seed'] == seed) & (config_df['is_dp'] == False)]['accuracy'].values
            
            if len(dp_val) > 0 and len(nondp_val) > 0:
                paired_dp.append(dp_val[0])
                paired_nondp.append(nondp_val[0])
        
        if len(paired_dp) < 2:
            logger.warning(f"Insufficient paired samples for alpha={alpha}, epsilon={epsilon}")
            results_by_config[(alpha, epsilon)] = {'p_value': np.nan, 'power_reduced': True, 'reason': 'insufficient_pairs'}
            continue
        
        # Perform paired t-test
        try:
            t_stat, p_val = stats.ttest_rel(paired_dp, paired_nondp)
            results_by_config[(alpha, epsilon)] = {
                'p_value': float(p_val),
                'power_reduced': False,
                'n_pairs': len(paired_dp)
            }
            p_values.append(p_val)
        except Exception as e:
            logger.error(f"Error running t-test for alpha={alpha}, epsilon={epsilon}: {e}")
            results_by_config[(alpha, epsilon)] = {'p_value': np.nan, 'power_reduced': True, 'reason': 'test_error'}
    
    mean_p = np.nanmean(p_values) if p_values else np.nan
    min_p = np.nanmin(p_values) if p_values else np.nan
    
    metadata = {
        'mean_p_value': float(mean_p),
        'min_p_value': float(min_p),
        'n_configurations': len(results_by_config),
        'configurations': results_by_config
    }
    
    return mean_p, min_p, metadata

def run_unpaired_ttest_majority_vs_minority(df: pd.DataFrame) -> Tuple[float, float, Dict[str, Any]]:
    """
    Run unpaired t-tests (or Mann-Whitney U fallback) comparing majority vs minority client accuracies.
    
    Args:
        df: DataFrame with majority/minority accuracy columns
        
    Returns:
        Tuple of (mean_p_value, min_p_value, metadata_dict)
    """
    if 'majority_accuracy' not in df.columns or 'minority_accuracy' not in df.columns:
        raise ValueError("DataFrame must contain 'majority_accuracy' and 'minority_accuracy' columns")
    
    p_values = []
    configurations = df.groupby(['alpha', 'epsilon']).groups.keys()
    
    results_by_config = {}
    power_reduced_flag = False
    
    for alpha, epsilon in configurations:
        config_df = df[(df['alpha'] == alpha) & (df['epsilon'] == epsilon)].dropna(subset=['majority_accuracy', 'minority_accuracy'])
        
        majority_vals = config_df['majority_accuracy'].values
        minority_vals = config_df['minority_accuracy'].values
        
        valid_runs = len(majority_vals)
        
        if valid_runs < 3:
            # Fallback to Mann-Whitney U if valid runs < 3
            logger.info(f"Using Mann-Whitney U fallback for alpha={alpha}, epsilon={epsilon} (valid_runs={valid_runs})")
            power_reduced_flag = True
            
            if valid_runs < 2:
                logger.warning(f"Insufficient data for statistical test: alpha={alpha}, epsilon={epsilon}")
                results_by_config[(alpha, epsilon)] = {'p_value': np.nan, 'power_reduced': True, 'reason': 'insufficient_data'}
                continue
            
            try:
                stat, p_val = stats.mannwhitneyu(majority_vals, minority_vals, alternative='two-sided')
                results_by_config[(alpha, epsilon)] = {
                    'p_value': float(p_val),
                    'power_reduced': True,
                    'test_type': 'mannwhitney',
                    'n_runs': valid_runs
                }
                p_values.append(p_val)
            except Exception as e:
                logger.error(f"Error running Mann-Whitney U for alpha={alpha}, epsilon={epsilon}: {e}")
                results_by_config[(alpha, epsilon)] = {'p_value': np.nan, 'power_reduced': True, 'reason': 'test_error'}
        else:
            # Standard unpaired t-test
            try:
                t_stat, p_val = stats.ttest_ind(majority_vals, minority_vals)
                results_by_config[(alpha, epsilon)] = {
                    'p_value': float(p_val),
                    'power_reduced': False,
                    'test_type': 'ttest',
                    'n_runs': valid_runs
                }
                p_values.append(p_val)
            except Exception as e:
                logger.error(f"Error running t-test for alpha={alpha}, epsilon={epsilon}: {e}")
                results_by_config[(alpha, epsilon)] = {'p_value': np.nan, 'power_reduced': True, 'reason': 'test_error'}
    
    mean_p = np.nanmean(p_values) if p_values else np.nan
    min_p = np.nanmin(p_values) if p_values else np.nan
    
    metadata = {
        'mean_p_value': float(mean_p),
        'min_p_value': float(min_p),
        'power_reduced': power_reduced_flag,
        'n_configurations': len(results_by_config),
        'configurations': results_by_config
    }
    
    return mean_p, min_p, metadata

def calculate_summary_statistics_for_task(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate summary statistics for the filtered dataset.
    
    Args:
        df: Filtered DataFrame
        
    Returns:
        Dictionary of summary statistics
    """
    summary = {
        'total_rows': len(df),
        'unique_seeds': df['seed'].nunique() if 'seed' in df.columns else 0,
        'unique_alphas': df['alpha'].nunique() if 'alpha' in df.columns else 0,
        'unique_epsilons': df['epsilon'].nunique() if 'epsilon' in df.columns else 0,
        'mean_accuracy': float(df['accuracy'].mean()) if 'accuracy' in df.columns else None,
        'std_accuracy': float(df['accuracy'].std()) if 'accuracy' in df.columns else None,
        'mean_epsilon': float(df['epsilon'].mean()) if 'epsilon' in df.columns else None,
        'dp_runs': len(df[df['is_dp'] == True]) if 'is_dp' in df.columns else 0,
        'nondp_runs': len(df[df['is_dp'] == False]) if 'is_dp' in df.columns else 0
    }
    
    return summary

def load_filtered_data(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Main pipeline function to filter utility collapse from the dataset.
    
    This implements T035: Filter utility collapse results from the dataset.
    
    Args:
        input_path: Path to the time-filtered CSV (results/filtered_time.csv)
        output_path: Path to save the utility-collapse-filtered CSV (results/filtered_data.csv)
        
    Returns:
        The filtered DataFrame
    """
    logger.info(f"Starting utility collapse filter pipeline")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    # Load the time-filtered data
    df = load_metrics_from_csv(input_path)
    
    # Apply utility collapse filter
    filtered_df = filter_utility_collapse(df)
    
    # Calculate and log summary statistics
    summary = calculate_summary_statistics_for_task(filtered_df)
    logger.info(f"Summary statistics: {summary}")
    
    # Save the filtered data
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered data to {output_path}")
    
    return filtered_df

def run_experiment_analysis(input_time_filtered: str, output_filtered: str, 
                             output_p_values: str) -> Dict[str, Any]:
    """
    Run the full analysis pipeline including utility collapse filtering and statistical tests.
    
    Args:
        input_time_filtered: Path to time-filtered CSV
        output_filtered: Path to save utility-collapse-filtered CSV
        output_p_values: Path to save p-values JSON
        
    Returns:
        Dictionary containing analysis results and metadata
    """
    # Step 1: Filter utility collapse
    filtered_df = load_filtered_data(input_time_filtered, output_filtered)
    
    # Step 2: Run statistical tests
    results = {
        'utility_filter_summary': calculate_summary_statistics_for_task(filtered_df),
        'paired_ttest_results': None,
        'unpaired_ttest_results': None
    }
    
    try:
        mean_p_dp, min_p_dp, dp_metadata = run_paired_ttest_dp_vs_nondp(filtered_df)
        results['paired_ttest_results'] = {
            'mean_p_value': mean_p_dp,
            'min_p_value': min_p_dp,
            'metadata': dp_metadata
        }
    except Exception as e:
        logger.error(f"Error in paired t-test: {e}")
        results['paired_ttest_results'] = {'error': str(e)}
    
    try:
        mean_p_maj, min_p_maj, maj_metadata = run_unpaired_ttest_majority_vs_minority(filtered_df)
        results['unpaired_ttest_results'] = {
            'mean_p_value': mean_p_maj,
            'min_p_value': min_p_maj,
            'metadata': maj_metadata
        }
    except Exception as e:
        logger.error(f"Error in unpaired t-test: {e}")
        results['unpaired_ttest_results'] = {'error': str(e)}
    
    # Save p-values to JSON
    with open(output_p_values, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Saved p-values to {output_p_values}")
    
    return results

def generate_validation_report(results: Dict[str, Any], output_path: str):
    """
    Generate a validation report for the analysis.
    
    Args:
        results: Analysis results dictionary
        output_path: Path to save the report
    """
    report_lines = [
        "# Utility Collapse Filter Validation Report",
        "",
        "## Summary",
        f"- Total rows after time filter: {results['utility_filter_summary']['total_rows']}",
        f"- Unique seeds: {results['utility_filter_summary']['unique_seeds']}",
        f"- Unique alphas: {results['utility_filter_summary']['unique_alphas']}",
        f"- Unique epsilons: {results['utility_filter_summary']['unique_epsilons']}",
        "",
        "## Statistical Tests"
    ]
    
    if results['paired_ttest_results'] and 'metadata' in results['paired_ttest_results']:
        dp_meta = results['paired_ttest_results']['metadata']
        report_lines.append(f"- Paired t-test (DP vs Non-DP): mean p-value = {dp_meta['mean_p_value']:.4f}")
        if dp_meta.get('power_reduced'):
            report_lines.append("  - WARNING: Power reduced due to insufficient pairs")
    
    if results['unpaired_ttest_results'] and 'metadata' in results['unpaired_ttest_results']:
        maj_meta = results['unpaired_ttest_results']['metadata']
        report_lines.append(f"- Unpaired test (Majority vs Minority): mean p-value = {maj_meta['mean_p_value']:.4f}")
        if maj_meta.get('power_reduced'):
            report_lines.append("  - WARNING: Power reduced (Mann-Whitney U fallback triggered)")
    
    report_text = "\n".join(report_lines)
    
    with open(output_path, 'w') as f:
        f.write(report_text)
    
    logger.info(f"Generated validation report at {output_path}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Filter utility collapse from dataset")
    parser.add_argument("--input", type=str, default="results/filtered_time.csv",
                       help="Input CSV file (time-filtered)")
    parser.add_argument("--output", type=str, default="results/filtered_data.csv",
                       help="Output CSV file")
    parser.add_argument("--p-values", type=str, default="results/p_values_by_seed.json",
                       help="Output JSON file for p-values")
    parser.add_argument("--report", type=str, default="results/analysis_report.md",
                       help="Output validation report")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    results = run_experiment_analysis(args.input, args.output, args.p_values)
    generate_validation_report(results, args.report)
    
    print(f"Analysis complete. Filtered data saved to {args.output}")
    print(f"P-values saved to {args.p_values}")
    print(f"Report saved to {args.report}")