import logging
import json
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, Set
import numpy as np
import pandas as pd
from scipy import stats

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_metrics_from_csv(csv_path: Path) -> pd.DataFrame:
    """Load metrics from a CSV file."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows from {csv_path}")
    return df

def filter_time_limited(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out rows where is_time_limited is True."""
    if 'is_time_limited' not in df.columns:
        logger.warning("Column 'is_time_limited' not found, returning original dataframe")
        return df
    filtered = df[df['is_time_limited'] != True]
    logger.info(f"Filtered time-limited rows: {len(df)} -> {len(filtered)}")
    return filtered

def filter_utility_collapse(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out rows where utility collapse is detected (accuracy < 0.05 OR epsilon < 0.05)."""
    if 'accuracy' not in df.columns or 'epsilon' not in df.columns:
        logger.warning("Required columns missing, returning original dataframe")
        return df
    
    mask = ~((df['accuracy'] < 0.05) | (df['epsilon'] < 0.05))
    filtered = df[mask]
    dropped = len(df) - len(filtered)
    logger.info(f"Filtered utility collapse rows: {len(df)} -> {len(filtered)} (dropped {dropped})")
    return filtered

def calculate_rounds_to_target(df: pd.DataFrame, target_accuracy: float = 0.8) -> pd.DataFrame:
    """Calculate rounds to reach target accuracy."""
    # This is a placeholder logic assuming df has 'round' and 'accuracy' columns
    # In a real scenario, we would group by seed/config and find the first round meeting target
    if 'round' not in df.columns or 'accuracy' not in df.columns:
        logger.warning("Missing columns for rounds calculation")
        return df
    
    # Simple mock implementation for structure if data isn't granular enough
    # In reality, this would require per-round data or a specific metric column
    if 'rounds_to_target' not in df.columns:
        df = df.copy()
        df['rounds_to_target'] = np.nan 
        logger.warning("Could not calculate rounds_to_target, column added as NaN")
    return df

def run_paired_ttest_dp_vs_nondp(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run paired t-tests on accuracy difference (DP - Non-DP) per seed.
    Returns a dict with p-values per configuration and a flag for power_reduced.
    """
    results = {}
    power_reduced_flags = {}
    
    # Group by configuration (alpha, epsilon)
    # We expect columns: alpha, epsilon, seed, global_accuracy, is_nondp (boolean or similar)
    # Assuming the input df has a way to distinguish DP vs Non-DP runs.
    # If the input is already filtered to only DP runs, we cannot do paired test without Non-DP data.
    # The task description implies we have both.
    
    if 'alpha' not in df.columns or 'epsilon' not in df.columns or 'seed' not in df.columns:
        logger.error("Missing configuration columns for t-test")
        return {"p_values": {}, "power_reduced": True, "reason": "Missing columns"}

    # Group by alpha and epsilon
    grouped = df.groupby(['alpha', 'epsilon'])
    
    for (alpha, epsilon), group in grouped:
        dp_runs = group[group.get('is_nondp', False) == False] # Assuming is_nondp=False means DP
        nondp_runs = group[group.get('is_nondp', False) == True] # Assuming is_nondp=True means Non-DP
        
        if len(dp_runs) == 0 or len(nondp_runs) == 0:
            logger.warning(f"No matching pairs for alpha={alpha}, epsilon={epsilon}. Skipping.")
            results[f"{alpha}_{epsilon}"] = []
            power_reduced_flags[f"{alpha}_{epsilon}"] = True
            continue
        
        # Match by seed
        p_values = []
        valid_pairs = 0
        
        for seed in dp_runs['seed'].unique():
            dp_row = dp_runs[dp_runs['seed'] == seed]
            nondp_row = nondp_runs[nondp_runs['seed'] == seed]
            
            if len(dp_row) == 1 and len(nondp_row) == 1:
                dp_acc = dp_row['global_accuracy'].values[0]
                nondp_acc = nondp_row['global_accuracy'].values[0]
                p_values.append(nondp_acc - dp_acc) # Difference
                valid_pairs += 1
            else:
                logger.warning(f"Missing non-DP run for seed {seed} in config ({alpha}, {epsilon})")
        
        if valid_pairs < 2:
            logger.warning(f"Not enough pairs for t-test in config ({alpha}, {epsilon}). Flagging power_reduced.")
            results[f"{alpha}_{epsilon}"] = []
            power_reduced_flags[f"{alpha}_{epsilon}"] = True
        else:
            # Perform t-test on the differences (one-sample t-test against 0)
            t_stat, p_val = stats.ttest_1samp(p_values, 0.0)
            results[f"{alpha}_{epsilon}"] = [float(p_val)] # List of p-values? Task says "list of individual p-values per seed" but t-test aggregates.
            # Re-reading T024a: "Output: p-values for DP vs Non-DP comparison". T028c says "JSON-encoded string of list of individual p-values per seed".
            # A paired t-test produces ONE p-value for the set of differences.
            # However, if we want "individual p-values per seed", we can't do that with a t-test on differences.
            # We will store the single aggregated p-value in a list to satisfy the JSON list requirement, 
            # or if the requirement implies bootstrapping per seed, that's different.
            # Given "paired t-tests... per seed" is physically impossible (t-test needs a distribution), 
            # we assume the "list" in T028c refers to the result of the test for that config (which might be a list of 1 value) 
            # OR it refers to the raw differences if the user wants to see them.
            # Let's stick to the statistical test result: one p-value per config.
            # To satisfy "list of individual p-values per seed" literally might be impossible with t-test.
            # Interpretation: The "list" in T028c is for the configuration, containing the p-value(s) derived.
            # If the task implies running a test per seed (which is nonsense for t-test), we can't.
            # We will store the calculated p-value in a list.
            results[f"{alpha}_{epsilon}"] = [float(p_val)]
            power_reduced_flags[f"{alpha}_{epsilon}"] = False
    
    return {
        "p_values": results,
        "power_reduced": power_reduced_flags
    }

def run_unpaired_ttest_majority_vs_minority(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run unpaired t-tests (or Mann-Whitney U) comparing majority vs minority client accuracies.
    """
    results = {}
    power_reduced_flags = {}
    
    if 'alpha' not in df.columns or 'epsilon' not in df.columns:
        logger.error("Missing configuration columns")
        return {"p_values": {}, "power_reduced": True}
    
    grouped = df.groupby(['alpha', 'epsilon'])
    
    for (alpha, epsilon), group in grouped:
        if 'majority_accuracy' not in group.columns or 'minority_accuracy' not in group.columns:
            logger.warning(f"Missing accuracy columns for config ({alpha}, {epsilon})")
            results[f"{alpha}_{epsilon}"] = []
            power_reduced_flags[f"{alpha}_{epsilon}"] = True
            continue
        
        majority = group['majority_accuracy'].dropna()
        minority = group['minority_accuracy'].dropna()
        
        if len(majority) < 3 or len(minority) < 3:
            logger.warning(f"Insufficient valid runs (<3) for config ({alpha}, {epsilon}). Switching to Mann-Whitney U and flagging power_reduced.")
            if len(majority) > 0 and len(minority) > 0:
                stat, p_val = stats.mannwhitneyu(majority, minority, alternative='two-sided')
                results[f"{alpha}_{epsilon}"] = [float(p_val)]
                power_reduced_flags[f"{alpha}_{epsilon}"] = True # Flagged due to fallback
            else:
                results[f"{alpha}_{epsilon}"] = []
                power_reduced_flags[f"{alpha}_{epsilon}"] = True
        else:
            # Unpaired t-test
            t_stat, p_val = stats.ttest_ind(majority, minority, equal_var=False)
            results[f"{alpha}_{epsilon}"] = [float(p_val)]
            power_reduced_flags[f"{alpha}_{epsilon}"] = False
    
    return {
        "p_values": results,
        "power_reduced": power_reduced_flags
    }

def calculate_summary_statistics_for_task(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate variance of accuracy metrics across 5 seeds per configuration.
    This function implements T028b logic: calculating p-values (aggregated from stats) 
    and variance per configuration.
    
    Returns a DataFrame with one row per configuration, including variance columns.
    """
    if df.empty:
        logger.warning("Input dataframe is empty")
        return df
    
    # Ensure we have the necessary columns
    required_cols = ['alpha', 'epsilon', 'global_accuracy', 'majority_accuracy', 'minority_accuracy']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        raise ValueError(f"Missing required columns: {missing}")
    
    # Group by configuration
    grouped = df.groupby(['alpha', 'epsilon'])
    
    summary_data = []
    
    for (alpha, epsilon), group in grouped:
        row = {
            'alpha': alpha,
            'epsilon': epsilon,
            'global_accuracy_mean': group['global_accuracy'].mean(),
            'global_accuracy_variance': group['global_accuracy'].var(),
            'majority_accuracy_mean': group['majority_accuracy'].mean(),
            'majority_accuracy_variance': group['majority_accuracy'].var(),
            'minority_accuracy_mean': group['minority_accuracy'].mean(),
            'minority_accuracy_variance': group['minority_accuracy'].var(),
            'rounds_to_target_mean': group['rounds_to_target'].mean() if 'rounds_to_target' in group.columns else None,
            'is_time_limited': group['is_time_limited'].any() if 'is_time_limited' in group.columns else False,
            'seed_count': len(group)
        }
        summary_data.append(row)
    
    summary_df = pd.DataFrame(summary_data)
    logger.info(f"Calculated summary statistics for {len(summary_df)} configurations")
    return summary_df

def generate_validation_report(df: pd.DataFrame, output_path: Path) -> None:
    """Generate a validation report markdown file."""
    report_lines = [
        "# Validation Report",
        "",
        f"Total rows processed: {len(df)}",
        ""
    ]
    
    # Count exclusions if available in the original full dataset (not passed here, so we assume df is filtered)
    # This function is a placeholder as we don't have the full unfiltered history here.
    report_lines.append("## Exclusion Counts")
    report_lines.append("- Time Limited: N/A (requires full log)")
    report_lines.append("- Utility Collapse: N/A (requires full log)")
    report_lines.append("- Power Reduced: Calculated in stats functions")
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))

def load_filtered_data() -> pd.DataFrame:
    """Load the filtered data from the results directory."""
    path = Path("results/filtered_data.csv")
    return load_metrics_from_csv(path)

def run_experiment_analysis() -> Dict[str, Any]:
    """
    Main analysis pipeline for T028b.
    1. Load filtered data.
    2. Calculate summary statistics (variance).
    3. Run t-tests (p-values).
    4. Return aggregated results.
    """
    logger.info("Starting experiment analysis for T028b")
    
    # Load data
    df = load_filtered_data()
    if df.empty:
        logger.error("No data found for analysis")
        return {}
    
    # Calculate summary statistics (Variance)
    summary_stats = calculate_summary_statistics_for_task(df)
    
    # Run T-tests
    ttest_results_dp = run_paired_ttest_dp_vs_nondp(df)
    ttest_results_majority_minority = run_unpaired_ttest_majority_vs_minority(df)
    
    # Consolidate results
    final_results = {
        "summary_statistics": summary_stats.to_dict(orient='records'),
        "p_values_dp_vs_nondp": ttest_results_dp['p_values'],
        "p_values_majority_vs_minority": ttest_results_majority_minority['p_values'],
        "power_reduced_flags": {
            "dp_vs_nondp": ttest_results_dp['power_reduced'],
            "majority_vs_minority": ttest_results_majority_minority['power_reduced']
        }
    }
    
    logger.info("Analysis complete")
    return final_results

if __name__ == "__main__":
    results = run_experiment_analysis()
    print(json.dumps(results, indent=2, default=str))
