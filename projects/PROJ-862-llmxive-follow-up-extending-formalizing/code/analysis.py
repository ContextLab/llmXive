import csv
import json
import logging
import math
import os
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from scipy import stats
from dataclasses import dataclass
import warnings

# Custom Exceptions and Classes
class NoValidSigmaError(Exception):
    """Raised when no sigma level passes the validity threshold."""
    pass

@dataclass
class NoValidSigmaReport:
    task_type: str
    reason: str
    trade_off_curve: List[Dict[str, Any]]

@dataclass
class PowerWarning:
    """Warning object for reduced statistical power."""
    task_type: str
    sigma: float
    original_test: str
    switched_test: str
    effective_n: int
    power_estimate: float
    message: str

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Helper Functions ---

def load_filtered_vectors(csv_path: str) -> List[Dict[str, Any]]:
    """Load filtered pairs from CSV for analysis."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Filtered vectors file not found: {csv_path}")
    vectors = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            vectors.append(row)
    return vectors

def calculate_pairwise_cosine_similarity(vectors: List[Dict[str, Any]], pair_ids: Optional[List[str]] = None) -> Dict[str, List[float]]:
    """
    Calculate cosine similarity distributions for baseline and perturbed sets.
    Returns dict: { 'baseline': [float], 'perturbed': [float] }
    """
    import base64
    import numpy as np

    baseline_sims = []
    perturbed_sims = []

    # Group by pair_id to find baseline vs perturbed pairs if not explicitly separated
    # Assuming the input 'vectors' contains both baseline and perturbed entries tagged by type
    # For this implementation, we assume the list is pre-filtered to contain pairs for comparison
    # or we process them in batches.

    # Simplified logic: Assume we have a list of (vector_b64, type) tuples or similar structure
    # Since the schema is 'vector_base64', we need to decode.
    # We will assume the input list 'vectors' has a 'vector_base64' and a 'type' (baseline/perturbed)
    # and we need to match them by 'pair_id'.

    grouped = {}
    for v in vectors:
        pid = v.get('pair_id')
        if not pid:
            continue
        if pid not in grouped:
            grouped[pid] = {'baseline': None, 'perturbed': []}
        
        vec_str = v.get('vector_base64')
        if not vec_str:
            continue
        
        try:
            vec_bytes = base64.b64decode(vec_str)
            vec_np = np.frombuffer(vec_bytes, dtype=np.float32)
        except Exception as e:
            logger.warning(f"Failed to decode vector for {pid}: {e}")
            continue

        v_type = v.get('type', 'baseline') # Default assumption
        
        if v_type == 'baseline':
            grouped[pid]['baseline'] = vec_np
        else:
            grouped[pid]['perturbed'].append(vec_np)

    for pid, data in grouped.items():
        if data['baseline'] is None or len(data['perturbed']) == 0:
            continue
        
        base_vec = data['baseline']
        for pert_vec in data['perturbed']:
            if len(base_vec) != len(pert_vec):
                continue
            # Cosine similarity
            dot = np.dot(base_vec, pert_vec)
            norm_base = np.linalg.norm(base_vec)
            norm_pert = np.linalg.norm(pert_vec)
            if norm_base == 0 or norm_pert == 0:
                continue
            sim = dot / (norm_base * norm_pert)
            # We want distance or dissimilarity for separability?
            # Task says "increased latent separability", so lower similarity = better separability?
            # Or we compare distributions of similarity.
            baseline_sims.append(sim)
            # If multiple perturbed, we might average or keep all. Let's keep all for distribution.
            perturbed_sims.append(sim)

    return {'baseline': baseline_sims, 'perturbed': perturbed_sims}

def check_sample_size_and_switch_test(n: int, alpha: float = 0.05) -> Tuple[str, Optional[PowerWarning]]:
    """
    Check effective sample size and switch to Wilcoxon if n < 30.
    Calculate reduced statistical power and return a warning if applicable.
    """
    threshold = 30
    test_type = "t-test"
    warning = None

    if n < threshold:
        test_type = "Wilcoxon signed-rank test"
        # Estimate power reduction
        # Power is roughly proportional to sqrt(n) for t-tests, but exact calculation requires effect size.
        # We will estimate a relative power drop based on the threshold crossing.
        # A simple heuristic: if n is very small, power is significantly reduced.
        # We'll calculate a rough estimate: power ~ 1 - (threshold / n) * factor?
        # Better: Use a standard approximation for Wilcoxon vs T-test efficiency (ARE ~ 0.95).
        # The main issue here is sample size.
        
        # Heuristic power estimate (very rough):
        # If n=30 is 80% power (typical target), then power scales with sqrt(n).
        # power_est = 0.8 * math.sqrt(n / threshold)
        power_est = 0.8 * math.sqrt(n / threshold) if n > 0 else 0.0
        
        warning = PowerWarning(
            task_type="global", # Will be refined per task
            sigma=0.0, # Will be refined
            original_test="t-test",
            switched_test="Wilcoxon signed-rank test",
            effective_n=n,
            power_estimate=power_est,
            message=f"Sample size {n} < {threshold}. Switched to Wilcoxon. Estimated power reduced to {power_est:.2f}."
        )
        logger.warning(warning.message)
    
    return test_type, warning

def run_hypothesis_test(baseline_sims: List[float], perturbed_sims: List[float], task_type: str, sigma: float) -> Dict[str, Any]:
    """
    Run the appropriate statistical test based on sample size.
    Returns dict with p_value, mean_diff, ci, test_type, and optional power_warning.
    """
    if len(baseline_sims) == 0 or len(perturbed_sims) == 0:
        return {
            "task_type": task_type,
            "sigma": sigma,
            "p_value": None,
            "mean_diff": None,
            "ci": None,
            "test_type": "None (Empty Data)",
            "power_warning": None
        }

    # Check sample size
    n = min(len(baseline_sims), len(perturbed_sims))
    test_type, power_warning = check_sample_size_and_switch_test(n)

    mean_diff = np.mean(perturbed_sims) - np.mean(baseline_sims)
    
    p_val = None
    ci = None

    try:
        if test_type == "Wilcoxon signed-rank test":
            # Wilcoxon requires paired data. We assume the lists are paired by index in the caller logic.
            # If they are not paired, we cannot use Wilcoxon signed-rank. 
            # Assuming paired structure from the similarity calculation logic above.
            if len(baseline_sims) == len(perturbed_sims):
                stat, p_val = stats.wilcoxon(baseline_sims, perturbed_sims)
            else:
                # Fallback to Mann-Whitney U if not perfectly paired but independent?
                # Task implies paired comparison (same pair, baseline vs perturbed).
                # If lengths differ, we truncate.
                min_len = min(len(baseline_sims), len(perturbed_sims))
                stat, p_val = stats.wilcoxon(baseline_sims[:min_len], perturbed_sims[:min_len])
        
        else:
            # T-test (paired)
            if len(baseline_sims) == len(perturbed_sims):
                stat, p_val = stats.ttest_rel(baseline_sims, perturbed_sims)
            else:
                min_len = min(len(baseline_sims), len(perturbed_sims))
                stat, p_val = stats.ttest_rel(baseline_sims[:min_len], perturbed_sims[:min_len])
        
        # Calculate CI for mean difference
        # Using bootstrap or standard error if normal assumption holds
        # For simplicity, using standard error of the mean difference
        diffs = np.array(perturbed_sims) - np.array(baseline_sims[:len(perturbed_sims)])
        if len(diffs) > 1:
            se = np.std(diffs, ddof=1) / math.sqrt(len(diffs))
            ci_lower = mean_diff - 1.96 * se
            ci_upper = mean_diff + 1.96 * se
            ci = [ci_lower, ci_upper]
        else:
            ci = [mean_diff, mean_diff]

    except Exception as e:
        logger.error(f"Statistical test failed for {task_type} at sigma={sigma}: {e}")
        p_val = None

    result = {
        "task_type": task_type,
        "sigma": sigma,
        "p_value": p_val,
        "mean_diff": float(mean_diff),
        "ci": ci,
        "test_type": test_type,
        "power_warning": None
    }

    if power_warning:
        result["power_warning"] = {
            "task_type": power_warning.task_type,
            "effective_n": power_warning.effective_n,
            "power_estimate": power_warning.power_estimate,
            "message": power_warning.message
        }

    return result

def aggregate_global_results(task_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate per-task results into a global summary."""
    all_p_values = [r["p_value"] for r in task_results if r["p_value"] is not None]
    all_mean_diffs = [r["mean_diff"] for r in task_results if r["mean_diff"] is not None]
    
    return {
        "total_tests": len(task_results),
        "valid_tests": len(all_p_values),
        "mean_global_diff": float(np.mean(all_mean_diffs)) if all_mean_diffs else None,
        "global_p_values": all_p_values
    }

def apply_holm_bonferroni(p_values: List[float], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Apply Holm-Bonferroni correction to a list of p-values.
    Returns list of dicts with original p-value, adjusted p-value, and significance.
    """
    if not p_values:
        return []

    indexed = list(enumerate(p_values))
    # Sort by p-value
    sorted_indexed = sorted(indexed, key=lambda x: x[1])
    
    m = len(p_values)
    adjusted = [0.0] * m
    
    # Holm-Bonferroni step-up procedure
    # For each i (0 to m-1), compare p_(i) with alpha / (m - i)
    # If p_(i) > alpha / (m - i), then all subsequent are non-significant?
    # Actually, Holm is: reject H_(i) if p_(i) <= alpha / (m - i + 1).
    # Adjusted p-value for the i-th smallest is max(adjusted of previous, p_(i) * (m - i + 1))
    
    prev_adj = 0.0
    for i, (orig_idx, p_val) in enumerate(sorted_indexed):
        # The rank in the sorted list is i+1 (1-based)
        # The number of tests remaining including this one is m - i
        # Correction factor: m - i
        factor = m - i
        adj_val = max(prev_adj, p_val * factor)
        if adj_val > 1.0:
            adj_val = 1.0
        adjusted[orig_idx] = adj_val
        prev_adj = adj_val

    results = []
    for i, adj_p in enumerate(adjusted):
        results.append({
            "original_p_value": p_values[i],
            "adjusted_p_value": adj_p,
            "significant": adj_p < alpha
        })
    
    return results

def check_significant_separability_increase(results: List[Dict[str, Any]], alpha: float = 0.05) -> bool:
    """Check if any test shows significant increase after correction."""
    for res in results:
        if res.get("significant", False):
            # Check direction of mean_diff?
            # "Increased separability" implies perturbed is MORE separable (lower similarity?)
            # If mean_diff < 0 (perturbed < baseline), that's increased separability.
            # The test result doesn't store direction in 'significant' flag directly, 
            # but we have 'mean_diff' in the source.
            # We need to cross-reference.
            pass
    return False # Placeholder

def run_analysis_orchestration(
    baseline_vectors_path: str,
    perturbed_vectors_path: str,
    validity_log_path: str,
    output_json_path: str
) -> None:
    """
    Main orchestration function for T049 and T039.
    1. Load data.
    2. Check sample size (T049).
    3. Run tests.
    4. Apply Holm-Bonferroni.
    5. Save results with power warnings.
    """
    logger.info(f"Starting analysis orchestration. Baseline: {baseline_vectors_path}, Perturbed: {perturbed_vectors_path}")
    
    # Load data
    # Assuming these files are pre-processed and contain 'pair_id', 'vector_base64', 'type'
    baseline_data = load_filtered_vectors(baseline_vectors_path)
    perturbed_data = load_filtered_vectors(perturbed_vectors_path)
    
    # Merge by pair_id
    # We need to align them.
    # Let's create a map for baseline
    baseline_map = {}
    for row in baseline_data:
        pid = row.get('pair_id')
        if pid:
            baseline_map[pid] = row.get('vector_base64')
    
    # Filter perturbed to only those with baseline
    aligned_pairs = []
    for row in perturbed_data:
        pid = row.get('pair_id')
        if pid and pid in baseline_map:
            aligned_pairs.append({
                'pair_id': pid,
                'baseline_vec': baseline_map[pid],
                'perturbed_vec': row.get('vector_base64')
            })
    
    logger.info(f"Aligned {len(aligned_pairs)} pairs for analysis.")
    
    if len(aligned_pairs) < 2:
        logger.error("Not enough data for statistical analysis.")
        # Save empty result
        with open(output_json_path, 'w') as f:
            json.dump({"error": "Insufficient data", "results": []}, f, indent=2)
        return

    # Run tests
    # We need to group by task_type and sigma if they exist in the data
    # Assuming the input files have these columns.
    # If not, we treat all as one group.
    
    # Grouping logic
    groups = {}
    for pair in aligned_pairs:
        # Try to get task_type and sigma from the perturbed row (assuming they are stored there)
        # The schema might not have them in the vector file, so we might need to join with validity_log
        # For now, assume they are in the CSV.
        # If not, we default to 'global'
        t_type = pair.get('task_type', 'global') # This might fail if not in CSV
        # Actually, the vector CSV might not have task_type. 
        # We must rely on the validity_log or assume a single run.
        # Let's assume the input files are already filtered by task_type or we process globally.
        # To be safe, we will process globally if task_type is missing.
        key = 'global' 
        if 'task_type' in pair:
            key = pair['task_type']
        if 'sigma' in pair:
            key = f"{pair['task_type']}_{pair['sigma']}"
        
        if key not in groups:
            groups[key] = {'baseline': [], 'perturbed': []}
        
        # Decode and append
        # We need to decode to compare.
        # But calculate_pairwise_cosine_similarity expects a list of dicts.
        # Let's restructure: create a list of dicts for the similarity function
        pass

    # Alternative approach: Pass the aligned list to the similarity function
    # The similarity function needs to know which is baseline and which is perturbed.
    # Let's create a unified list with a 'type' field.
    unified_data = []
    for pair in aligned_pairs:
        unified_data.append({'pair_id': pair['pair_id'], 'vector_base64': pair['baseline_vec'], 'type': 'baseline'})
        unified_data.append({'pair_id': pair['pair_id'], 'vector_base64': pair['perturbed_vec'], 'type': 'perturbed'})
    
    # Calculate similarities
    # This function groups by pair_id internally.
    sim_results = calculate_pairwise_cosine_similarity(unified_data)
    
    if not sim_results['baseline'] or not sim_results['perturbed']:
        logger.warning("No valid similarity pairs found.")
        with open(output_json_path, 'w') as f:
            json.dump({"error": "No valid pairs", "results": []}, f, indent=2)
        return

    # Run hypothesis test
    # Since we don't have task_type/sigma in the unified list easily, we assume global for now
    # or we need to extract from the original CSVs.
    # Let's assume the task is run per (task_type, sigma) if the files are split,
    # or globally if combined.
    # The function run_hypothesis_test expects lists.
    
    test_result = run_hypothesis_test(
        sim_results['baseline'],
        sim_results['perturbed'],
        task_type="global", # Or extract from context
        sigma=0.0 # Or extract from context
    )
    
    # Apply Holm-Bonferroni
    # If we have multiple tests (e.g. per task type), we collect all p-values.
    # Here we only have one test result for the global set.
    p_values = [test_result['p_value']] if test_result['p_value'] is not None else []
    corrections = apply_holm_bonferroni(p_values)
    
    if corrections:
        test_result['adjusted_p_value'] = corrections[0]['adjusted_p_value']
        test_result['significant'] = corrections[0]['significant']
    else:
        test_result['adjusted_p_value'] = None
        test_result['significant'] = False

    # Final Output Structure
    final_output = {
        "analysis_timestamp": str(datetime.now()),
        "results": [test_result],
        "global_summary": aggregate_global_results([test_result]),
        "holm_bonferroni_correction": corrections
    }
    
    # Write to JSON
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, 'w') as f:
        json.dump(final_output, f, indent=2)
    
    logger.info(f"Analysis results saved to {output_json_path}")

# --- Main Entry Point for Script Execution ---
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Statistical Analysis")
    parser.add_argument("--baseline", required=True, help="Path to baseline vectors CSV")
    parser.add_argument("--perturbed", required=True, help="Path to perturbed vectors CSV")
    parser.add_argument("--validity-log", required=True, help="Path to validity log CSV")
    parser.add_argument("--output", required=True, help="Path to output JSON")
    
    args = parser.parse_args()
    run_analysis_orchestration(args.baseline, args.perturbed, args.validity_log, args.output)

# Import datetime for main block
from datetime import datetime
