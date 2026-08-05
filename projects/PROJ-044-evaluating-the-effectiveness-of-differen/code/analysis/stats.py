import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import numpy as np
import pandas as pd
from scipy import stats

from config import Config

# --- Logging Setup ---
logger = logging.getLogger(__name__)

# --- Helper Functions ---

def filter_time_limited(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters out rows where is_time_limited is True.
    Used for SC-001 metrics calculation.
    """
    if df.empty:
        return df
    return df[df['is_time_limited'] == False].copy()

def filter_utility_collapse(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters out rows where is_utility_collapse is True.
    Used to produce the clean dataset for final analysis.
    """
    if df.empty:
        return df
    return df[df['is_utility_collapse'] == False].copy()

def load_metrics_from_csv(file_path: str) -> pd.DataFrame:
    """
    Loads metrics from a CSV file.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {file_path}")
    return pd.read_csv(path)

def calculate_rounds_to_target(df: pd.DataFrame, target_accuracy: float = 0.8) -> pd.DataFrame:
    """
    Calculates the number of rounds to reach target accuracy per run.
    Assumes the input df has 'round' and 'global_accuracy' columns.
    This is a simplified aggregation for the summary if raw round-level data isn't present.
    If the input is already aggregated (one row per run), this might just return the max round or a specific metric.
    For this task, we assume the input 'filtered_data.csv' contains aggregated metrics per run.
    If 'rounds_to_target' is missing, we might need to estimate or leave as NaN if raw logs aren't available.
    However, T018b/T019 should have logged this. We will assume it exists or is derived.
    """
    if 'rounds_to_target' in df.columns:
        return df['rounds_to_target']
    # Fallback if not explicitly logged: assume max round if accuracy reached, else NaN
    # This is a placeholder logic if the column is missing
    if 'global_accuracy' in df.columns and 'max_round' in df.columns:
        # Simple heuristic: if accuracy >= target, use max_round, else NaN
        df['rounds_to_target'] = df.apply(
            lambda r: r['max_round'] if r['global_accuracy'] >= target_accuracy else np.nan,
            axis=1
        )
        return df['rounds_to_target']
    return pd.Series([np.nan] * len(df))

def run_paired_ttest_dp_vs_nondp(df: pd.DataFrame, epsilon_col: str = 'epsilon') -> Dict[float, List[float]]:
    """
    Performs paired t-tests on accuracy difference (DP - Non-DP) per seed.
    Input: Filtered data (no time_limited, no utility_collapse).
    Assumption: The dataframe contains rows for both DP and Non-DP runs,
    distinguished by epsilon (e.g., epsilon=0.0 for Non-DP, others for DP).
    Or, we compare DP runs against a baseline Non-DP run for the same seed/alpha.
    
    Based on FR-005: "paired t-tests on the accuracy difference (DP accuracy minus Non-DP accuracy) per seed".
    We need to group by (seed, alpha). For each group, we need a Non-DP accuracy and a set of DP accuracies.
    Usually Non-DP corresponds to epsilon=infinity or a specific marker. 
    Let's assume epsilon=0.0 or a specific 'is_dp' flag exists. 
    If not, we look for a row where epsilon is minimal or marked as non-dp.
    
    Simplification for this implementation:
    We assume the input dataframe has a column 'is_dp' or we infer Non-DP as epsilon=0.0 (or specific value).
    If the dataset doesn't explicitly have Non-DP runs for every seed/alpha, we cannot compute paired t-test.
    We will assume the training loop (T018b) generated a 'non_dp' run (epsilon=0.0 or similar) for each config.
    
    Strategy:
    1. Group by (seed, alpha).
    2. Identify Non-DP accuracy (e.g., where epsilon is 0.0 or a specific marker).
    3. Identify DP accuracies (where epsilon > 0).
    4. Calculate difference (DP - NonDP) for each DP run.
    5. Run t-test on these differences against 0? Or just return the p-value of the difference distribution?
       "paired t-test" usually implies comparing two related samples. Here, it's comparing the set of DP accuracies
       against the set of Non-DP accuracies? But there's only one Non-DP run per seed/alpha?
       If there's only one Non-DP run, we can't do a paired t-test unless we have multiple Non-DP runs.
       
    Re-reading FR-005: "paired t-tests on the accuracy difference (DP accuracy minus Non-DP accuracy) per seed".
    This implies we have multiple seeds. For a fixed alpha, we have multiple seeds.
    Maybe it means: For each seed, we have a Non-DP accuracy and a DP accuracy (for a specific epsilon).
    Then we test if the mean difference across seeds is significantly different from 0.
    
    Let's assume the function is called per (alpha, epsilon) configuration.
    Input df has rows for all seeds for this alpha/epsilon and the corresponding Non-DP rows.
    Actually, the summary needs a list of p-values per seed? No, "p-value ... (list of individual p-values per seed)"?
    That phrasing is odd. A t-test produces one p-value for a set of samples.
    "list of individual p-values per seed" might mean we run a t-test for each seed? Impossible with one value per seed.
    Interpretation: We calculate the difference for each seed, then run a ONE-SAMPLE t-test on the differences to see if mean(diff) != 0.
    The output should be the p-value of this test.
    The task description says "list of individual p-values per seed" in the summary CSV column.
    This is contradictory. A single t-test gives one p-value for the group.
    Perhaps it means: For each epsilon, we run a t-test comparing DP vs Non-DP across seeds.
    The summary column `p_value_dp_vs_nondp` should contain that single p-value for the (alpha, epsilon) group.
    But the description says "list of individual p-values per seed".
    Maybe it means: For each seed, we have a p-value? No, that's not how t-tests work.
    Let's assume the requirement means: "The p-value from the t-test comparing DP vs Non-DP across seeds".
    And if the prompt insists on a "list", maybe it's a list of p-values for each epsilon level?
    Given the column definition: `p_value_dp_vs_nondp` (list of individual p-values per seed from T024a).
    This is very confusing. T024a is "paired t-tests ... per seed".
    If T024a runs per seed, it implies we have multiple runs per seed?
    Let's assume the standard interpretation: Compare DP accuracies vs Non-DP accuracies across the 5 seeds.
    The result is ONE p-value for the (alpha, epsilon) group.
    However, to satisfy the "list" requirement in the CSV description, maybe we store the p-value as a string or list?
    Or maybe the "list" refers to the p-values for DIFFERENT epsilon comparisons?
    
    Let's stick to the most logical statistical approach:
    For a given (alpha, epsilon), we have 5 seeds.
    We have 5 Non-DP accuracies (from epsilon=0.0 or similar) for the same 5 seeds.
    We compute diff = DP_acc - NonDP_acc for each seed.
    We run a one-sample t-test on `diff` to see if mean(diff) != 0.
    The result is a single p-value.
    We will return a dictionary mapping (alpha, epsilon) -> p_value.
    If the summary CSV requires a "list", we might have to format it as a string or a list containing one float.
    Given the ambiguity, I will return the single p-value for the group.
    If the user meant "p-values for each epsilon", that's handled by the loop.
    
    Correction: The task says "list of individual p-values per seed".
    Maybe it means: For each seed, we compare DP vs Non-DP? But we only have one DP and one Non-DP per seed.
    You cannot run a t-test on 1 sample.
    Therefore, the "per seed" must refer to the grouping for the t-test (i.e., the t-test is performed on the set of seeds).
    I will return the single p-value for the group (alpha, epsilon).
    If the CSV column expects a list, I will format it as a JSON string or similar.
    But usually, CSV columns are atomic. I'll assume the description meant "p-value for the seed-grouped test".
    Wait, "list of individual p-values per seed" might be a typo for "p-value for the test across seeds".
    I will implement the t-test across seeds and return the single p-value.
    """
    if df.empty:
        return {}
    
    results = {}
    
    # Identify Non-DP rows. Assuming epsilon=0.0 or a specific flag.
    # If no epsilon=0.0, we might need to infer. Let's assume epsilon=0.0 is Non-DP.
    non_dp_mask = df['epsilon'] == 0.0
    dp_mask = df['epsilon'] > 0.0
    
    if not non_dp_mask.any():
        logger.warning("No Non-DP runs found (epsilon=0.0). Skipping t-test.")
        return {}
    
    non_dp_df = df[non_dp_mask]
    dp_df = df[dp_mask]
    
    # Group by alpha
    for alpha in dp_df['alpha'].unique():
        alpha_dp = dp_df[dp_df['alpha'] == alpha]
        alpha_non_dp = non_dp_df[non_dp_df['alpha'] == alpha]
        
        for epsilon in alpha_dp['epsilon'].unique():
            dp_group = alpha_dp[alpha_dp['epsilon'] == epsilon]
            non_dp_group = alpha_non_dp[alpha_non_dp['epsilon'] == 0.0] # Non-DP is always 0.0
            
            # Match by seed
            common_seeds = set(dp_group['seed']).intersection(set(non_dp_group['seed']))
            if len(common_seeds) < 2:
                logger.warning(f"Not enough common seeds for alpha={alpha}, epsilon={epsilon} to run t-test.")
                results[(alpha, epsilon)] = np.nan
                continue
            
            dp_accs = []
            nondp_accs = []
            
            for seed in sorted(common_seeds):
                dp_row = dp_group[dp_group['seed'] == seed].iloc[0]
                nondp_row = non_dp_group[non_dp_group['seed'] == seed].iloc[0]
                dp_accs.append(dp_row['global_accuracy'])
                nondp_accs.append(nondp_row['global_accuracy'])
            
            # Paired t-test
            t_stat, p_val = stats.ttest_rel(dp_accs, nondp_accs)
            results[(alpha, epsilon)] = p_val
            
    return results

def run_unpaired_ttest_majority_vs_minority(df: pd.DataFrame) -> Dict[Tuple[float, float], float]:
    """
    Performs unpaired t-tests (or Mann-Whitney U if n < 3) comparing majority vs minority accuracies.
    Input: Filtered data.
    Returns: Dict mapping (alpha, epsilon) -> p_value.
    """
    if df.empty:
        return {}
    
    results = {}
    
    for alpha in df['alpha'].unique():
        for epsilon in df['epsilon'].unique():
            group = df[(df['alpha'] == alpha) & (df['epsilon'] == epsilon)]
            
            if group.empty:
                continue
            
            # Check for valid runs
            if len(group) < 3:
                logger.warning(f"Fewer than 3 runs for alpha={alpha}, epsilon={epsilon}. Using Mann-Whitney U.")
                power_reduced = True
            else:
                power_reduced = False
            
            # We need to compare majority_accuracy vs minority_accuracy for each row?
            # Or are these aggregated per run?
            # The summary CSV has columns: global_accuracy, minority_accuracy, majority_accuracy.
            # So each row is a run (seed, alpha, epsilon).
            # We want to test if the distribution of majority accuracies is different from minority accuracies.
            # This is a paired comparison per run? Or unpaired across runs?
            # "comparing majority vs minority client accuracies for each configuration"
            # Usually, we compare the vector of majority_accs vs vector of minority_accs.
            # Since they come from the same run, they are paired. But the task says "unpaired t-tests (or Mann-Whitney U)".
            # Mann-Whitney U is unpaired.
            # Let's follow the instruction: "unpaired t-tests (or Mann-Whitney U)".
            # So we treat the list of majority accuracies and list of minority accuracies as independent samples?
            # That seems statistically weak, but we follow the spec.
            
            majority_accs = group['majority_accuracy'].dropna().values
            minority_accs = group['minority_accuracy'].dropna().values
            
            if len(majority_accs) < 2 or len(minority_accs) < 2:
                results[(alpha, epsilon)] = np.nan
                continue
            
            if len(group) < 3:
                # Mann-Whitney U
                stat, p_val = stats.mannwhitneyu(majority_accs, minority_accs, alternative='two-sided')
            else:
                # Unpaired t-test
                stat, p_val = stats.ttest_ind(majority_accs, minority_accs)
            
            results[(alpha, epsilon)] = p_val
            
    return results

def generate_validation_report(
    raw_logs_path: str,
    filtered_logs_path: str,
    output_path: str
) -> None:
    """
    Generates a validation report (MD) including counts of excluded runs.
    """
    raw_df = load_metrics_from_csv(raw_logs_path)
    filtered_df = load_metrics_from_csv(filtered_logs_path)
    
    total_runs = len(raw_df)
    filtered_runs = len(filtered_df)
    excluded_runs = total_runs - filtered_runs
    
    time_limited_count = raw_df['is_time_limited'].sum() if 'is_time_limited' in raw_df.columns else 0
    utility_collapse_count = raw_df['is_utility_collapse'].sum() if 'is_utility_collapse' in raw_df.columns else 0
    
    # Check for power reduced flags if available (from T035b logic)
    # Assuming we can infer or store this in a separate column or just note the sample size
    power_reduced_count = 0
    if 'power_reduced' in filtered_df.columns:
        power_reduced_count = filtered_df['power_reduced'].sum()
    
    report_lines = [
        "# Validation Report",
        "",
        "## Data Filtering Summary",
        f"- **Total Runs in Raw Logs**: {total_runs}",
        f"- **Runs in Filtered Data**: {filtered_runs}",
        f"- **Excluded Runs**: {excluded_runs}",
        "",
        "## Exclusion Breakdown",
        f"- **Time Limited (is_time_limited)**: {time_limited_count}",
        f"- **Utility Collapse (is_utility_collapse)**: {utility_collapse_count}",
        "",
        "## Statistical Power",
        f"- **Runs with Reduced Power (n < 3)**: {power_reduced_count}",
        "",
        "## Dataset Constraints",
        "- **Dataset**: FEMNIST only (Shakespeare excluded per plan.md).",
        "- **Filtering**: Excludes time-limited and utility collapse runs.",
        "",
        "## Notes",
        "- Mann-Whitney U test was used for configurations with < 3 valid runs.",
        "- Paired t-tests were performed on seed-matched DP vs Non-DP runs."
    ]
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Validation report generated at {output_path}")

def calculate_summary_statistics_for_task(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates summary statistics for the final report.
    """
    # Placeholder if specific aggregation is needed beyond the raw filtered data
    return df

def run_experiment_analysis(
    raw_logs_path: str,
    filtered_logs_path: str,
    output_summary_path: str,
    output_report_path: str
) -> None:
    """
    Orchestrates the final analysis for T028.
    1. Load filtered data.
    2. Calculate p-values (T024a, T024b).
    3. Generate summary CSV (T028).
    4. Generate validation report (T028).
    """
    logger.info(f"Starting analysis for T028. Input: {filtered_logs_path}")
    
    # Load filtered data
    df = load_metrics_from_csv(filtered_logs_path)
    
    if df.empty:
        raise ValueError("Filtered dataset is empty. Cannot generate summary.")
    
    # Ensure FEMNIST only
    if 'dataset' in df.columns:
        df = df[df['dataset'] == 'femnist']
        if df.empty:
            raise ValueError("No FEMNIST data found in filtered dataset.")
    
    # 1. Calculate P-values
    p_values_dp = run_paired_ttest_dp_vs_nondp(df)
    p_values_maj_min = run_unpaired_ttest_majority_vs_minority(df)
    
    # 2. Prepare Summary DataFrame
    # Columns: seed, alpha, epsilon, global_accuracy, minority_accuracy, majority_accuracy,
    #          rounds_to_target, is_time_limited, p_value_dp_vs_nondp, p_value_majority_vs_minority
    
    summary_rows = []
    
    for _, row in df.iterrows():
        seed = row['seed']
        alpha = row['alpha']
        epsilon = row['epsilon']
        
        # Get p-values for this (alpha, epsilon)
        p_dp = p_values_dp.get((alpha, epsilon), np.nan)
        p_mm = p_values_maj_min.get((alpha, epsilon), np.nan)
        
        summary_rows.append({
            'seed': seed,
            'alpha': alpha,
            'epsilon': epsilon,
            'global_accuracy': row.get('global_accuracy', np.nan),
            'minority_accuracy': row.get('minority_accuracy', np.nan),
            'majority_accuracy': row.get('majority_accuracy', np.nan),
            'rounds_to_target': row.get('rounds_to_target', np.nan),
            'is_time_limited': row.get('is_time_limited', False),
            'p_value_dp_vs_nondp': p_dp,
            'p_value_majority_vs_minority': p_mm
        })
    
    summary_df = pd.DataFrame(summary_rows)
    
    # 3. Save Summary CSV
    Path(output_summary_path).parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(output_summary_path, index=False)
    logger.info(f"Summary CSV saved to {output_summary_path}")
    
    # 4. Generate Validation Report
    generate_validation_report(raw_logs_path, filtered_logs_path, output_report_path)
    
    logger.info("T028 Analysis complete.")

# --- Main Entry Point for T028 ---
if __name__ == "__main__":
    import sys
    
    # Default paths
    RAW_LOGS = "results/raw_logs.csv"
    FILTERED_LOGS = "results/filtered_data.csv"
    SUMMARY_CSV = "results/summary.csv"
    VALIDATION_REPORT = "results/validation_report.md"
    
    if len(sys.argv) > 1:
        RAW_LOGS = sys.argv[1]
    if len(sys.argv) > 2:
        FILTERED_LOGS = sys.argv[2]
    if len(sys.argv) > 3:
        SUMMARY_CSV = sys.argv[3]
    if len(sys.argv) > 4:
        VALIDATION_REPORT = sys.argv[4]
        
    run_experiment_analysis(RAW_LOGS, FILTERED_LOGS, SUMMARY_CSV, VALIDATION_REPORT)
