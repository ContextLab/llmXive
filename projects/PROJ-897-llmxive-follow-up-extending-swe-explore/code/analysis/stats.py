"""
Statistical analysis module for SWE-Explore benchmark.
Implements paired tests, survival analysis, and Bonferroni correction.
"""
import json
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats
from scipy.stats import survival_function

# Local imports
from config import get_config_summary

# --------------------------------------------------------------------------
# Data Loading Helpers
# --------------------------------------------------------------------------

def load_agent_logs_for_pairing(
    baseline_dir: Path, iterative_dir: Path
) -> Dict[str, Dict[str, Any]]:
    """
    Load agent logs from baseline and iterative runs and pair them by issue_id.
    Returns a dict: { issue_id: { 'baseline': log, 'iterative': log } }
    """
    paired_data: Dict[str, Dict[str, Any]] = {}

    # Load baseline logs
    baseline_logs = {}
    if baseline_dir.exists():
        for f in baseline_dir.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    log = json.load(fh)
                    if "issue_id" in log:
                        baseline_logs[log["issue_id"]] = log
            except (json.JSONDecodeError, IOError):
                continue

    # Load iterative logs
    iterative_logs = {}
    if iterative_dir.exists():
        for f in iterative_dir.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    log = json.load(fh)
                    if "issue_id" in log:
                        iterative_logs[log["issue_id"]] = log
            except (json.JSONDecodeError, IOError):
                continue

    # Pair them
    all_ids = set(baseline_logs.keys()) & set(iterative_logs.keys())
    for issue_id in all_ids:
        paired_data[issue_id] = {
            "baseline": baseline_logs[issue_id],
            "iterative": iterative_logs[issue_id],
        }

    return paired_data

def calculate_coverage_metrics_for_issue(
    log: Dict[str, Any], ground_truth_lines: List[int]
) -> float:
    """
    Calculate coverage percentage for a single agent log.
    Coverage = (number of ground truth lines retrieved) / (total ground truth lines)
    """
    if not ground_truth_lines:
        return 0.0
    retrieved = set(log.get("retrieved_lines", []))
    relevant_retrieved = len(retrieved.intersection(set(ground_truth_lines)))
    return relevant_retrieved / len(ground_truth_lines)

def compute_paired_coverage_data(
    paired_logs: Dict[str, Dict[str, Any]],
    ground_truth_map: Dict[str, List[int]],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute paired coverage arrays for baseline and iterative agents.
    Returns (baseline_coverage, iterative_coverage) as numpy arrays.
    """
    baseline_vals = []
    iterative_vals = []

    for issue_id, logs in paired_logs.items():
        gt_lines = ground_truth_map.get(issue_id, [])
        if not gt_lines:
            continue

        b_cov = calculate_coverage_metrics_for_issue(logs["baseline"], gt_lines)
        i_cov = calculate_coverage_metrics_for_issue(logs["iterative"], gt_lines)

        baseline_vals.append(b_cov)
        iterative_vals.append(i_cov)

    return np.array(baseline_vals), np.array(iterative_vals)

def run_wilcoxon_signed_rank_test(
    x: np.ndarray, y: np.ndarray
) -> Dict[str, Any]:
    """
    Run Wilcoxon signed-rank test with continuity correction.
    Returns dict with statistic, p-value, and interpretation.
    """
    if len(x) != len(y):
        raise ValueError("Arrays must be same length for paired test")
    if len(x) < 2:
        return {
            "test": "wilcoxon",
            "statistic": None,
            "p_value": None,
            "significant": False,
            "message": "Insufficient data for test (n < 2)",
        }

    # Handle ties and zero differences
    try:
        statistic, p_value = stats.wilcoxon(x, y, correction=True)
    except Exception as e:
        # Fallback if all differences are zero or other edge cases
        return {
            "test": "wilcoxon",
            "statistic": 0.0,
            "p_value": 1.0,
            "significant": False,
            "message": f"Wilcoxon failed: {str(e)}",
        }

    return {
        "test": "wilcoxon",
        "statistic": float(statistic),
        "p_value": float(p_value),
        "significant": p_value < 0.05,
        "message": "Wilcoxon signed-rank test completed with continuity correction.",
    }

def run_exact_permutation_test(
    x: np.ndarray, y: np.ndarray
) -> Dict[str, Any]:
    """
    Run exact permutation test as fallback for censored/high-tie data.
    """
    if len(x) != len(y):
        raise ValueError("Arrays must be same length")
    if len(x) > 20:
        # Exact permutation is computationally expensive for large N
        return {
            "test": "permutation_exact",
            "statistic": None,
            "p_value": None,
            "significant": False,
            "message": "Sample size too large for exact permutation test (n > 20)",
        }

    diffs = x - y
    observed_stat = np.mean(diffs)
    n = len(diffs)
    count_extreme = 0
    total_perms = 2**n

    # Enumerate all sign flips
    for i in range(total_perms):
        signs = np.array([1 if (i >> j) & 1 else -1 for j in range(n)])
        perm_stat = np.mean(diffs * signs)
        if abs(perm_stat) >= abs(observed_stat):
            count_extreme += 1

    p_value = count_extreme / total_perms

    return {
        "test": "permutation_exact",
        "statistic": float(observed_stat),
        "p_value": float(p_value),
        "significant": p_value < 0.05,
        "message": "Exact permutation test completed.",
    }

def run_cox_survival_analysis(
    coverage_baseline: np.ndarray, coverage_iterative: np.ndarray
) -> Dict[str, Any]:
    """
    Run Cox Proportional Hazards model comparing coverage distributions.
    Treats coverage as 'time-to-event' (higher coverage = faster event).
    """
    try:
        from lifelines import CoxPHFitter
        import pandas as pd

        # Create survival data: event = coverage > 0 (simplified)
        # In a full implementation, we would use actual 'turns to first relevant line'
        df = pd.DataFrame({
            "T": np.concatenate([coverage_baseline, coverage_iterative]),
            "E": np.ones(len(coverage_baseline) + len(coverage_iterative)),
            "group": [0] * len(coverage_baseline) + [1] * len(coverage_iterative),
        })

        cph = CoxPHFitter()
        cph.fit(df, duration_col="T", event_col="E")
        
        # Get hazard ratio and p-value for group
        summary = cph.summary
        if "group" in summary.index:
            p_val = summary.loc["group", "p"]
            hr = summary.loc["group", "exp(coef)"]
        else:
            p_val = 1.0
            hr = 1.0

        return {
            "test": "cox_survival",
            "hazard_ratio": float(hr),
            "p_value": float(p_val),
            "significant": p_val < 0.05,
            "message": "Cox survival analysis completed.",
        }
    except ImportError:
        return {
            "test": "cox_survival",
            "p_value": None,
            "significant": False,
            "message": "lifelines library not installed for survival analysis.",
        }
    except Exception as e:
        return {
            "test": "cox_survival",
            "p_value": None,
            "significant": False,
            "message": f"Cox survival analysis failed: {str(e)}",
        }

def analyze_ranking_metrics(
    paired_logs: Dict[str, Dict[str, Any]],
    ground_truth_map: Dict[str, List[int]],
) -> Dict[str, Any]:
    """
    Analyze ranking metrics (First Relevant Position) with fallback logic.
    """
    baseline_ranks = []
    iterative_ranks = []

    for issue_id, logs in paired_logs.items():
        gt_lines = ground_truth_map.get(issue_id, [])
        if not gt_lines:
            continue

        # Simplified: use retrieved_lines to find first relevant
        b_retrieved = logs["baseline"].get("retrieved_lines", [])
        i_retrieved = logs["iterative"].get("retrieved_lines", [])

        b_rank = next(
            (i + 1 for i, line in enumerate(b_retrieved) if line in gt_lines),
            len(gt_lines) + 1,
        )
        i_rank = next(
            (i + 1 for i, line in enumerate(i_retrieved) if line in gt_lines),
            len(gt_lines) + 1,
        )

        baseline_ranks.append(b_rank)
        iterative_ranks.append(i_rank)

    if not baseline_ranks:
        return {"test": "ranking", "p_value": None, "significant": False, "message": "No ranking data."}

    # Check for excessive ties/censoring (rank = N+1)
    n_total = len(baseline_ranks)
    censored_baseline = sum(1 for r in baseline_ranks if r > max(gt_lines) for gt_lines in [ground_truth_map.get(list(paired_logs.keys())[0], [])])
    # Simplified censoring check
    if n_total > 0 and (sum(1 for r in baseline_ranks if r == n_total + 1) + sum(1 for r in iterative_ranks if r == n_total + 1)) / (2 * n_total) > 0.5:
        # High censoring -> use survival or permutation
        return run_cox_survival_analysis(np.array(baseline_ranks), np.array(iterative_ranks))
    
    # Default to Wilcoxon
    return run_wilcoxon_signed_rank_test(np.array(baseline_ranks), np.array(iterative_ranks))

def apply_bonferroni_correction(
    p_values: List[float], alpha: float = 0.05
) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction to a family of p-values.
    Returns corrected p-values and significance flags.
    """
    m = len(p_values)
    if m == 0:
        return [], []

    corrected_p = [min(p * m, 1.0) for p in p_values]
    significant = [p < alpha for p in corrected_p]
    return corrected_p, significant

def format_associational_statement(
    test_name: str, significant: bool, p_value: float, effect_direction: str
) -> str:
    """
    Generate a strictly associational statement per FR-007.
    """
    if significant:
        return (
            f"A statistically significant associational difference was observed in {test_name} "
            f"(Bonferroni-corrected p = {p_value:.4f}), with the iterative agent showing "
            f"{effect_direction} performance compared to the static baseline."
        )
    else:
        return (
            f"No statistically significant associational difference was observed in {test_name} "
            f"(Bonferroni-corrected p = {p_value:.4f})."
        )

def main():
    """
    Main entry point for T031c: Bonferroni correction and final metrics generation.
    """
    config = get_config_summary()
    base_path = Path(config.get("base_path", "."))
    results_dir = base_path / "data" / "results"
    curated_dir = base_path / "data" / "curated"

    results_dir.mkdir(parents=True, exist_ok=True)

    # Load paired logs
    baseline_dir = results_dir / "agent_logs" / "baseline"
    iterative_dir = results_dir / "agent_logs" / "iterative"

    if not baseline_dir.exists() or not iterative_dir.exists():
        print("Error: Agent log directories not found. Run T024 first.")
        sys.exit(1)

    paired_logs = load_agent_logs_for_pairing(baseline_dir, iterative_dir)
    if not paired_logs:
        print("Error: No paired logs found.")
        sys.exit(1)

    # Load ground truth mapping
    ground_truth_map = {}
    gt_file = curated_dir / "ground_truth_map.json"
    if gt_file.exists():
        with open(gt_file, "r") as f:
            ground_truth_map = json.load(f)
    else:
        # Fallback: try to load from hard_subset if map missing
        hard_file = curated_dir / "hard_subset.jsonl"
        if hard_file.exists():
            with open(hard_file, "r") as f:
                for line in f:
                    item = json.loads(line)
                    ground_truth_map[item["issue_id"]] = item.get("ground_truth_lines", [])

    # 1. Coverage Analysis
    b_cov, i_cov = compute_paired_coverage_data(paired_logs, ground_truth_map)
    coverage_result = run_wilcoxon_signed_rank_test(b_cov, i_cov)

    # 2. Ranking Analysis
    ranking_result = analyze_ranking_metrics(paired_logs, ground_truth_map)

    # 3. Bonferroni Correction
    # Family of tests: Coverage + Ranking
    raw_p_values = [
        coverage_result.get("p_value", 1.0),
        ranking_result.get("p_value", 1.0),
    ]
    corrected_p_values, significant_flags = apply_bonferroni_correction(raw_p_values)

    # Update results with corrected p-values
    coverage_result["bonferroni_p_value"] = corrected_p_values[0]
    coverage_result["bonferroni_significant"] = significant_flags[0]
    ranking_result["bonferroni_p_value"] = corrected_p_values[1]
    ranking_result["bonferroni_significant"] = significant_flags[1]

    # 4. Generate Associational Statements
    coverage_statement = format_associational_statement(
        "coverage",
        coverage_result["bonferroni_significant"],
        coverage_result["bonferroni_p_value"],
        "higher" if np.mean(i_cov) > np.mean(b_cov) else "lower",
    )
    ranking_statement = format_associational_statement(
        "ranking",
        ranking_result["bonferroni_significant"],
        ranking_result["bonferroni_p_value"],
        "better" if ranking_result.get("hazard_ratio", 1) > 1 else "worse",
    )

    # 5. Assemble Final Metrics
    final_metrics = {
        "metadata": {
            "task_id": "T031c",
            "description": "Bonferroni-corrected paired statistical analysis",
            "n_pairs": len(paired_logs),
            "correction_method": "Bonferroni",
            "alpha": 0.05,
            "family_size": 2,
        },
        "coverage": {
            **coverage_result,
            "statement": coverage_statement,
            "mean_baseline": float(np.mean(b_cov)),
            "mean_iterative": float(np.mean(i_cov)),
        },
        "ranking": {
            **ranking_result,
            "statement": ranking_statement,
        },
        "conclusion": {
            "overall_significant": any(significant_flags),
            "associational_summary": (
                f"Analysis of {len(paired_logs)} paired instances reveals "
                f"{'significant' if any(significant_flags) else 'no significant'} "
                "associational differences between the iterative and static baseline agents "
                "after Bonferroni correction. No causal claims are made."
            ),
        },
    }

    # Write output
    output_file = results_dir / "final_metrics.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_metrics, f, indent=2)

    print(f"Final metrics written to {output_file}")
    print(f"Coverage significant (Bonferroni): {coverage_result['bonferroni_significant']}")
    print(f"Ranking significant (Bonferroni): {ranking_result['bonferroni_significant']}")
    print(f"Conclusion: {final_metrics['conclusion']['associational_summary']}")

if __name__ == "__main__":
    main()
