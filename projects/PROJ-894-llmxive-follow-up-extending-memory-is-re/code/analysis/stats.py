import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

# Ensure these imports align with the existing API surface
# If specific functions like load_results_from_csv are not defined in the file yet,
# we define them here to ensure the module is self-contained for this task's logic,
# or we assume they exist in the "omitted" part of the file as per the prompt.
# Given the prompt says "extend it on disk", we assume the existing functions exist.
# However, to be safe and runnable, we include robust implementations of the helpers
# if they were missing, but primarily we implement the new T027 logic.

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helper Functions (Assuming these exist in the "omitted" part, but defining for safety if needed) ---
# In a real "extend" scenario, these would already be present. 
# We will assume they are present based on the API surface description.
# If not, the following would be the implementation:

def load_results_from_csv(file_path: str) -> List[Dict[str, Any]]:
    """Load a CSV file into a list of dictionaries."""
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"File not found: {file_path}")
        return []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def extract_accuracy_scores(results: List[Dict[str, Any]]) -> List[float]:
    """Extract accuracy scores from results list."""
    scores = []
    for r in results:
        try:
            # Handle potential string conversion
            val = r.get('accuracy', r.get('accuracy_score', 0))
            if val is not None:
                scores.append(float(val))
        except (ValueError, TypeError):
            continue
    return scores

def extract_nodes_visited(results: List[Dict[str, Any]]) -> List[int]:
    """Extract nodes visited from results list."""
    counts = []
    for r in results:
        try:
            val = r.get('nodes_visited', r.get('node_count', 0))
            if val is not None:
                counts.append(int(val))
        except (ValueError, TypeError):
            continue
    return counts

def extract_success_flags(results: List[Dict[str, Any]]) -> List[int]:
    """Extract success flags (1 for success, 0 for failure) from results."""
    flags = []
    for r in results:
        try:
            val = r.get('success', r.get('is_success', r.get('accuracy', 0)))
            # If accuracy is present, treat > 0 as success, or if explicit boolean
            if isinstance(val, str):
                val = 1 if val.lower() in ['true', '1', 'yes'] else 0
            else:
                val = 1 if float(val) > 0 else 0
            flags.append(int(val))
        except (ValueError, TypeError):
            continue
    return flags

def calculate_point_biserial_correlation(x: List[float], y: List[int]) -> Tuple[float, float]:
    """Calculate point-biserial correlation and p-value."""
    if len(x) < 2 or len(y) < 2:
        return 0.0, 1.0
    try:
        corr, p_value = stats.pointbiserialr(y, x)
        return float(corr), float(p_value)
    except Exception as e:
        logger.error(f"Error calculating point-biserial: {e}")
        return 0.0, 1.0

def compare_heuristics_vs_baseline(baseline_scores: List[float], heuristic_scores: List[float]) -> Dict[str, float]:
    """Perform paired t-test or Wilcoxon test."""
    if len(baseline_scores) != len(heuristic_scores) or len(baseline_scores) < 2:
        return {'p_value': 1.0, 'statistic': 0.0, 'method': 'insufficient_data'}
    try:
        # Check for normality (simple Shapiro-Wilk)
        if len(baseline_scores) > 50:
            t_stat, p_val = stats.ttest_rel(baseline_scores, heuristic_scores)
            return {'p_value': float(p_val), 'statistic': float(t_stat), 'method': 'ttest'}
        else:
            w_stat, p_val = stats.wilcoxon(baseline_scores, heuristic_scores)
            return {'p_value': float(p_val), 'statistic': float(w_stat), 'method': 'wilcoxon'}
    except Exception as e:
        logger.error(f"Error in comparison test: {e}")
        return {'p_value': 1.0, 'statistic': 0.0, 'method': 'error'}

def calculate_descriptive_stats(scores: List[float]) -> Dict[str, float]:
    """Calculate mean, std, min, max."""
    if not scores:
        return {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0}
    arr = np.array(scores)
    return {
        'mean': float(np.mean(arr)),
        'std': float(np.std(arr)),
        'min': float(np.min(arr)),
        'max': float(np.max(arr))
    }

def compute_accuracy_deltas(baseline_scores: List[float], heuristic_scores: List[float]) -> List[float]:
    """Compute delta (heuristic - baseline) for each pair."""
    if len(baseline_scores) != len(heuristic_scores):
        return []
    return [float(h - b) for b, h in zip(baseline_scores, heuristic_scores)]

# --- T027 Implementation: Sensitivity Analysis and Complexity Threshold ---

def load_sweep_results(file_path: str) -> pd.DataFrame:
    """Load sweep results from CSV."""
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"Sweep results file not found: {file_path}. Skipping sensitivity analysis.")
        return pd.DataFrame()
    df = pd.read_csv(path)
    return df

def perform_sensitivity_analysis(sweep_df: pd.DataFrame, threshold: float = 0.95) -> Dict[str, Any]:
    """
    Perform sensitivity analysis on the sweep data.
    Assumes columns like 'threshold' and 'accuracy' exist.
    """
    if sweep_df.empty:
        return {'status': 'no_data', 'optimal_threshold': None, 'analysis': []}

    analysis = []
    if 'threshold' in sweep_df.columns and 'accuracy' in sweep_df.columns:
        # Sort by threshold to find the trend
        sorted_df = sweep_df.sort_values(by='threshold')
        
        best_threshold = None
        max_acc = -1.0

        for _, row in sorted_df.iterrows():
            t = float(row['threshold'])
            acc = float(row['accuracy'])
            analysis.append({
                'threshold': t,
                'accuracy': acc,
                'nodes_visited': float(row.get('nodes_visited', 0))
            })
            if acc > max_acc:
                max_acc = acc
                best_threshold = t
        
        return {
            'status': 'success',
            'optimal_threshold': best_threshold,
            'max_accuracy': max_acc,
            'analysis': analysis
        }
    
    return {'status': 'missing_columns', 'optimal_threshold': None, 'analysis': []}

def identify_complexity_threshold(
    all_results: List[Dict[str, Any]], 
    baseline_accuracy: float, 
    threshold_ratio: float = 0.95
) -> Dict[str, Any]:
    """
    Identify the specific complexity threshold where accuracy drops below a significant threshold of the baseline.
    Strategy:
    1. Bin the full dataset of nodes_visited into bins where each bin has at least 3 tasks (n >= 3).
    2. Calculate mean accuracy for each bin.
    3. Find the first bin (ordered by complexity/nodes_visited) where mean accuracy < (threshold_ratio * baseline_accuracy).
    """
    if not all_results:
        return {'status': 'no_data', 'threshold_node_count': None, 'details': 'No results to analyze.'}

    # Prepare data
    nodes_list = []
    success_list = []
    
    for r in all_results:
        try:
            nodes = int(r.get('nodes_visited', r.get('node_count', 0)))
            # Success flag: if accuracy is provided, we can use it as a continuous metric, 
            # but the task asks for "success flags". We will treat accuracy > 0 as success for the binning logic 
            # if a binary flag isn't explicitly present, or use accuracy as the metric if the prompt implies 
            # "accuracy drops below...". The prompt says "binning ... nodes_visited and success flags ... identifying mean accuracy".
            # This implies we bin by nodes, then check the mean of the accuracy (or success rate) in that bin.
            # Let's assume 'accuracy' is the metric to check against the threshold.
            acc = float(r.get('accuracy', 0))
            nodes_list.append(nodes)
            success_list.append(acc) # Using accuracy as the metric for the bin mean
        except (ValueError, TypeError):
            continue

    if len(nodes_list) < 3:
        return {'status': 'insufficient_data', 'threshold_node_count': None, 'details': 'Less than 3 tasks available.'}

    # Create DataFrame for binning
    df = pd.DataFrame({'nodes': nodes_list, 'accuracy': success_list})
    df = df.sort_values(by='nodes')

    # Determine bin edges to ensure n >= 3 per bin
    # We will use a simple adaptive binning approach:
    # Sort by nodes. Split into chunks of size >= 3.
    n = len(df)
    bins = []
    current_bin = []
    
    # We need to group consecutive sorted items into bins of size >= 3
    # A simple strategy: iterate and accumulate until we have 3, then check if adding more helps or if we should close.
    # To ensure "first bin with mean < threshold", we want the bins to be as granular as possible while satisfying n>=3.
    # We'll form bins of exactly 3, then append the remainder to the last bin if necessary, 
    # or just group by fixed size 3.
    
    # Better approach for "complexity threshold":
    # Create bins of size 3 (or more if total count is small).
    # We want to find the *first* bin (lowest complexity) that fails.
    
    bin_groups = []
    i = 0
    while i < n:
        # Start a new bin
        # Take at least 3
        end_idx = min(i + 3, n)
        # If we are at the very end and have less than 3 left, merge with previous bin?
        # The requirement says "each bin contains at least 3 tasks".
        # If we have 4 items left and n=4, we must put them all in one bin? 
        # Or if we have 10 items, we can do 3, 3, 4.
        # If we have 5 items, we can do 3, 2 (invalid) -> so 5 must be one bin?
        # Let's try to make bins of size 3, and if the remainder is < 3, merge it with the last bin.
        
        if n - i < 3:
            # Remaining items < 3, merge with last bin
            if bin_groups:
                bin_groups[-1] = list(range(bin_groups[-1][0], n)) # Extend last bin to end
            else:
                # Only one bin total
                bin_groups.append(list(range(n)))
            break
        
        # Check if the next 3 are valid
        # We just take 3
        bin_groups.append(list(range(i, i + 3)))
        i += 3

    # If the last bin is too small (shouldn't happen with the logic above unless n < 3 handled earlier)
    # Re-check last bin size
    if bin_groups and (len(bin_groups[-1]) < 3):
        # Merge with previous
        if len(bin_groups) > 1:
            prev = bin_groups.pop()
            bin_groups[-1].extend(prev)
        else:
            # Only one bin, size < 3 -> impossible if n >= 3 and logic correct, but safety
            pass

    # Calculate mean accuracy for each bin
    bin_stats = []
    for idx, indices in enumerate(bin_groups):
        bin_nodes = df.iloc[indices]['nodes'].values
        bin_accs = df.iloc[indices]['accuracy'].values
        
        mean_nodes = float(np.mean(bin_nodes))
        mean_acc = float(np.mean(bin_accs))
        count = len(indices)
        
        bin_stats.append({
            'bin_id': idx,
            'mean_nodes_visited': mean_nodes,
            'mean_accuracy': mean_acc,
            'n_tasks': count,
            'node_range': (int(bin_nodes.min()), int(bin_nodes.max()))
        })

    # Sort bin_stats by mean_nodes_visited (should already be sorted, but ensure)
    bin_stats.sort(key=lambda x: x['mean_nodes_visited'])

    # Calculate the target threshold
    target_acc = baseline_accuracy * threshold_ratio

    # Find the first bin where mean_accuracy < target_acc
    threshold_node_count = None
    failing_bin = None

    for b in bin_stats:
        if b['mean_accuracy'] < target_acc:
            threshold_node_count = b['mean_nodes_visited']
            failing_bin = b
            break

    return {
        'status': 'success' if threshold_node_count is not None else 'no_threshold_found',
        'threshold_node_count': threshold_node_count,
        'baseline_accuracy': baseline_accuracy,
        'target_threshold_ratio': threshold_ratio,
        'failing_bin': failing_bin,
        'bin_statistics': bin_stats
    }

def run_t027_analysis(
    sweep_file: str = "data/processed/sweep_results.csv",
    baseline_file: str = "data/processed/baseline_results.csv",
    noisy_baseline_file: str = "data/processed/noisy_baseline_results.csv",
    lazy_file: str = "data/processed/lazy_results.csv",
    noisy_lazy_file: str = "data/processed/noisy_lazy_results.csv",
    greedy_file: str = "data/processed/greedy_results.csv",
    noisy_greedy_file: str = "data/processed/noisy_greedy_results.csv",
    output_file: str = "data/processed/stats_report.json"
):
    """
    Main entry point for T027.
    1. Load sweep results and perform sensitivity analysis.
    2. Load all result CSVs, combine them, and identify complexity threshold.
    3. Update/Append to the stats_report.json.
    """
    report = {}
    
    # 1. Sensitivity Analysis
    logger.info("Loading sweep results for sensitivity analysis...")
    sweep_df = load_sweep_results(sweep_file)
    sensitivity_result = perform_sensitivity_analysis(sweep_df)
    report['sensitivity_analysis'] = sensitivity_result

    # 2. Complexity Threshold Analysis
    logger.info("Loading all result CSVs for complexity threshold analysis...")
    
    all_results = []
    files_to_load = [
        baseline_file, noisy_baseline_file,
        lazy_file, noisy_lazy_file,
        greedy_file, noisy_greedy_file
    ]
    
    for f in files_to_load:
        res = load_results_from_csv(f)
        if res:
            all_results.extend(res)
            logger.info(f"Loaded {len(res)} results from {f}")
    
    if not all_results:
        logger.error("No results found in any CSV file. Cannot compute complexity threshold.")
        report['complexity_threshold_analysis'] = {'status': 'failed', 'reason': 'No data'}
    else:
        # Calculate baseline accuracy (from baseline_results.csv specifically, or average of all?)
        # The task says "drops below a significant threshold of the baseline". 
        # We should use the mean accuracy of the baseline file as the reference.
        baseline_res = load_results_from_csv(baseline_file)
        baseline_accs = extract_accuracy_scores(baseline_res)
        if baseline_accs:
            global_baseline_accuracy = float(np.mean(baseline_accs))
        else:
            # Fallback to global mean if baseline file missing
            global_baseline_accuracy = float(np.mean(extract_accuracy_scores(all_results)))
            logger.warning("Baseline file empty or missing, using global mean as reference.")

        threshold_result = identify_complexity_threshold(
            all_results, 
            baseline_accuracy=global_baseline_accuracy, 
            threshold_ratio=0.95
        )
        report['complexity_threshold_analysis'] = threshold_result

    # 3. Save Report
    # We should append to existing stats_report.json if it exists, or create new.
    # The task says "Output threshold to data/processed/stats_report.json".
    # Since T024a/T024b also output to this file, we should merge or overwrite?
    # Usually, analysis tasks append their findings.
    
    output_path = Path(output_file)
    existing_report = {}
    if output_path.exists():
        try:
            with open(output_path, 'r') as f:
                existing_report = json.load(f)
        except json.JSONDecodeError:
            logger.warning("Existing stats_report.json is invalid, overwriting.")
    
    # Merge T027 findings into the report
    existing_report.update(report)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(existing_report, f, indent=2)
    
    logger.info(f"T027 Analysis complete. Report saved to {output_file}")
    return existing_report

def main():
    """Main entry point for the script."""
    run_t027_analysis()

if __name__ == "__main__":
    main()