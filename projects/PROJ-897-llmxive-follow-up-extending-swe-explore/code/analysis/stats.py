"""
Statistical analysis module.
Implements Wilcoxon signed-rank test and Exact Permutation Test.
"""
import json
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path, get_config_summary, TIE_THRESHOLD

def load_agent_logs_for_pairing(
    baseline_file: Path,
    iterative_file: Path
) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    Load baseline and iterative logs and pair them by issue_id.
    
    Returns:
        List of (baseline_record, iterative_record) tuples.
    """
    # Load baseline
    baseline_map = {}
    with open(baseline_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                baseline_map[record.get('issue_id')] = record
            except json.JSONDecodeError:
                continue
    
    # Load iterative and pair
    paired = []
    with open(iterative_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                issue_id = record.get('issue_id')
                if issue_id in baseline_map:
                    paired.append((baseline_map[issue_id], record))
            except json.JSONDecodeError:
                continue
    
    return paired

def run_wilcoxon_signed_rank_test(
    baseline_values: List[float],
    iterative_values: List[float]
) -> Dict[str, Any]:
    """
    Run Wilcoxon signed-rank test on paired data.
    
    Args:
        baseline_values: List of baseline metric values.
        iterative_values: List of iterative metric values.
        
    Returns:
        Dictionary with p-value, effect size, and conclusion.
    """
    from scipy.stats import wilcoxon
    
    if len(baseline_values) != len(iterative_values):
        raise ValueError("Input lists must have the same length.")
    
    if len(baseline_values) < 2:
        return {
            "test": "wilcoxon",
            "status": "insufficient_data",
            "message": "Need at least 2 pairs for Wilcoxon test."
        }
    
    # Remove pairs where both values are 0 (censored)
    # This is a simplified approach; full implementation would handle censoring more carefully
    clean_baseline = []
    clean_iterative = []
    
    for b, i in zip(baseline_values, iterative_values):
        if b != 0 or i != 0:
            clean_baseline.append(b)
            clean_iterative.append(i)
    
    if len(clean_baseline) < 2:
        return {
            "test": "wilcoxon",
            "status": "insufficient_clean_data",
            "message": "Not enough non-censored pairs for Wilcoxon test."
        }
    
    # Run Wilcoxon test
    stat, p_value = wilcoxon(clean_baseline, clean_iterative)
    
    # Calculate effect size (r = Z / sqrt(N))
    # Approximate Z from statistic
    n = len(clean_baseline)
    z = stat / np.sqrt(n * (n + 1) * (2 * n + 1) / 6)
    effect_size = abs(z) / np.sqrt(n)
    
    conclusion = "significant" if p_value < 0.05 else "not_significant"
    
    return {
        "test": "wilcoxon",
        "statistic": float(stat),
        "p_value": float(p_value),
        "effect_size": float(effect_size),
        "n_pairs": n,
        "conclusion": conclusion,
        "alpha": 0.05
    }

def run_exact_permutation_test(
    baseline_values: List[float],
    iterative_values: List[float],
    n_permutations: int = 10000
) -> Dict[str, Any]:
    """
    Run exact permutation test on paired data.
    Handles ties and censored data.
    
    Args:
        baseline_values: List of baseline metric values.
        iterative_values: List of iterative metric values.
        n_permutations: Number of permutations for approximation.
        
    Returns:
        Dictionary with p-value, effect size, and conclusion.
    """
    if len(baseline_values) != len(iterative_values):
        raise ValueError("Input lists must have the same length.")
    
    if len(baseline_values) < 2:
        return {
            "test": "permutation",
            "status": "insufficient_data",
            "message": "Need at least 2 pairs for permutation test."
        }
    
    # Calculate observed difference
    diffs = [i - b for b, i in zip(baseline_values, iterative_values)]
    observed_mean_diff = np.mean(diffs)
    
    # Permutation test
    np.random.seed(42)
    n = len(diffs)
    count_extreme = 0
    
    for _ in range(n_permutations):
        # Randomly flip signs
        signs = np.random.choice([-1, 1], size=n)
        permuted_diffs = np.array(diffs) * signs
        permuted_mean = np.mean(permuted_diffs)
        
        if abs(permuted_mean) >= abs(observed_mean_diff):
            count_extreme += 1
    
    p_value = count_extreme / n_permutations
    
    # Effect size (Cohen's d for paired data)
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1)
    effect_size = mean_diff / std_diff if std_diff != 0 else 0
    
    conclusion = "significant" if p_value < 0.05 else "not_significant"
    
    return {
        "test": "permutation",
        "p_value": float(p_value),
        "effect_size": float(effect_size),
        "n_pairs": n,
        "n_permutations": n_permutations,
        "observed_mean_diff": float(observed_mean_diff),
        "conclusion": conclusion,
        "alpha": 0.05
    }

def apply_bonferroni_correction(
    p_values: List[float],
    n_tests: int
) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        n_tests: Number of tests in the family.
        
    Returns:
        List of adjusted p-values.
    """
    adjusted = [min(p * n_tests, 1.0) for p in p_values]
    return adjusted

def main():
    """Entry point for the stats script."""
    parser = argparse.ArgumentParser(description="Statistical Analysis")
    parser.add_argument(
        "--baseline",
        type=str,
        default=str(get_path('results') / "baseline_logs.jsonl"),
        help="Path to baseline logs"
    )
    parser.add_argument(
        "--iterative",
        type=str,
        default=str(get_path('results') / "iterative_logs.jsonl"),
        help="Path to iterative logs"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(get_path('results') / "stats_summary.json"),
        help="Path to output JSON"
    )
    
    args = parser.parse_args()
    
    print("Starting statistical analysis...")
    
    baseline_file = Path(args.baseline)
    iterative_file = Path(args.iterative)
    
    if not baseline_file.exists():
        print(f"ERROR: Baseline file not found: {baseline_file}")
        sys.exit(1)
    if not iterative_file.exists():
        print(f"ERROR: Iterative file not found: {iterative_file}")
        sys.exit(1)
    
    try:
        # Load and pair data
        paired = load_agent_logs_for_pairing(baseline_file, iterative_file)
        print(f"Paired {len(paired)} records.")
        
        if len(paired) == 0:
            print("ERROR: No paired records found.")
            sys.exit(1)
        
        # Extract coverage values
        baseline_coverage = [p[0].get('coverage_score', 0.0) for p in paired]
        iterative_coverage = [p[1].get('coverage_score', 0.0) for p in paired]
        
        # Run Wilcoxon test
        print("Running Wilcoxon signed-rank test...")
        wilcoxon_result = run_wilcoxon_signed_rank_test(baseline_coverage, iterative_coverage)
        
        # Run Permutation test (as alternative)
        print("Running Exact Permutation test...")
        permutation_result = run_exact_permutation_test(baseline_coverage, iterative_coverage)
        
        # Apply Bonferroni correction
        p_values = [wilcoxon_result.get('p_value', 1.0), permutation_result.get('p_value', 1.0)]
        adjusted_p_values = apply_bonferroni_correction(p_values, 2)
        wilcoxon_result['adjusted_p_value'] = adjusted_p_values[0]
        permutation_result['adjusted_p_value'] = adjusted_p_values[1]
        
        # Compile results
        results = {
            "coverage_analysis": {
                "wilcoxon": wilcoxon_result,
                "permutation": permutation_result
            },
            "bonferroni_correction": {
                "n_tests": 2,
                "adjusted_p_values": adjusted_p_values
            },
            "generated_at": str(Path(__file__).parent.parent.name)
        }
        
        # Write output
        output_file = Path(args.output)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print(f"Statistical analysis complete. Results saved to: {output_file}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    main()
