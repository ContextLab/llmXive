import json
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats
from scipy.stats import mannwhitneyu, wilcoxon
from lifelines import CoxPHFitter

from config import get_path, get_config_summary

# ---------------------------------------------------------------------------
# Helper: Load paired logs
# ---------------------------------------------------------------------------
def load_agent_logs_for_pairing(results_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load baseline and iterative logs from data/results/agent_logs/ (or custom dir)
    and return a list of paired records keyed by issue_id.
    """
    if results_dir is None:
        results_dir = get_path("results")
    
    baseline_path = results_dir / "agent_logs" / "baseline.jsonl"
    iterative_path = results_dir / "agent_logs" / "iterative.jsonl"
    
    if not baseline_path.exists() or not iterative_path.exists():
        raise FileNotFoundError(
            f"Missing log files for pairing: {baseline_path}, {iterative_path}"
        )

    def load_jsonl(path: Path) -> Dict[str, Dict]:
        records = {}
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    # Use issue_id as key for pairing
                    rid = rec.get("issue_id")
                    if rid:
                        records[rid] = rec
        return records

    baseline_logs = load_jsonl(baseline_path)
    iterative_logs = load_jsonl(iterative_path)

    paired = []
    for rid in baseline_logs:
        if rid in iterative_logs:
            paired.append({
                "issue_id": rid,
                "baseline": baseline_logs[rid],
                "iterative": iterative_logs[rid]
            })
        else:
            warnings.warn(f"Issue {rid} missing in iterative logs, skipping pairing.")
    
    for rid in iterative_logs:
        if rid not in baseline_logs:
            warnings.warn(f"Issue {rid} missing in baseline logs, skipping pairing.")

    return paired

# ---------------------------------------------------------------------------
# Coverage Metrics
# ---------------------------------------------------------------------------
def calculate_coverage_metrics_for_issue(
    issue_rec: Dict[str, Any], 
    ground_truth_lines: List[int]
) -> float:
    """
    Calculate coverage % for a single issue record.
    Assumes 'retrieved_lines' is a list of integers in the record.
    """
    retrieved = set(issue_rec.get("retrieved_lines", []))
    gt_set = set(ground_truth_lines)
    if not gt_set:
        return 0.0
    hit = len(retrieved & gt_set)
    return (hit / len(gt_set)) * 100.0

def compute_paired_coverage_data(
    paired_logs: List[Dict[str, Any]],
    gt_map: Dict[str, List[int]]
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Extract paired coverage arrays (baseline, iterative) and issue_ids.
    Returns (baseline_covs, iterative_covs, ids)
    """
    b_covs = []
    i_covs = []
    ids = []
    
    for pair in paired_logs:
        rid = pair["issue_id"]
        gt_lines = gt_map.get(rid, [])
        if not gt_lines:
            continue
        
        b_cov = calculate_coverage_metrics_for_issue(pair["baseline"], gt_lines)
        i_cov = calculate_coverage_metrics_for_issue(pair["iterative"], gt_lines)
        
        b_covs.append(b_cov)
        i_covs.append(i_cov)
        ids.append(rid)
    
    return np.array(b_covs), np.array(i_covs), ids

# ---------------------------------------------------------------------------
# Statistical Tests
# ---------------------------------------------------------------------------
def run_wilcoxon_signed_rank_test(
    x: np.ndarray, 
    y: np.ndarray, 
    correction: bool = True
) -> Dict[str, Any]:
    """
    Run Wilcoxon signed-rank test on paired data.
    Returns dict with statistic, p-value, and interpretation.
    """
    if len(x) != len(y):
        raise ValueError("Arrays must be same length for Wilcoxon.")
    if len(x) < 2:
        return {"statistic": 0.0, "pvalue": 1.0, "method": "wilcoxon", "n": len(x)}

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        stat, pval = wilcoxon(x, y, correction=correction)
    
    return {
        "statistic": float(stat),
        "pvalue": float(pval),
        "method": "wilcoxon_signed_rank",
        "n": len(x),
        "correction_applied": correction
    }

def run_exact_permutation_test(
    x: np.ndarray, 
    y: np.ndarray, 
    n_permutations: int = 10000
) -> Dict[str, Any]:
    """
    Fallback: Exact permutation test for paired differences.
    """
    if len(x) != len(y):
        raise ValueError("Arrays must be same length.")
    if len(x) == 0:
        return {"statistic": 0.0, "pvalue": 1.0, "method": "permutation", "n": 0}

    diffs = x - y
    observed_stat = np.sum(diffs)
    
    # Generate permutation distribution
    n = len(diffs)
    # Sign-flip permutations (paired permutation test)
    counts = 0
    total = 0
    for _ in range(n_permutations):
        signs = np.random.choice([-1, 1], size=n)
        perm_stat = np.sum(diffs * signs)
        total += 1
        if abs(perm_stat) >= abs(observed_stat):
            counts += 1
    
    pval = counts / total
    return {
        "statistic": float(observed_stat),
        "pvalue": float(pval),
        "method": "exact_permutation",
        "n_permutations": n_permutations
    }

def run_cox_survival_analysis(
    data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Survival analysis for ranking metrics (time-to-relevant).
    Assumes data has 'rank_position' and 'censored' flags.
    """
    if not data:
        return {"method": "cox", "conclusion": "no_data"}
    
    df = pd.DataFrame(data)
    if 'rank_position' not in df.columns or 'censored' not in df.columns:
        raise ValueError("Data must contain 'rank_position' and 'censored' columns.")
    
    # Group by agent type if present, otherwise assume two groups
    if 'agent_type' in df.columns:
        groups = df['agent_type'].unique()
        if len(groups) != 2:
            return {"method": "cox", "conclusion": "expected_two_groups"}
        
        # Fit Cox model with agent type as covariate
        cph = CoxPHFitter()
        df_surv = df.rename(columns={"rank_position": "T", "censored": "E"})
        # Convert agent_type to dummy
        df_surv = pd.get_dummies(df_surv, columns=["agent_type"], drop_first=True)
        
        try:
            cph.fit(df_surv, duration_col='T', event_col='E')
            # Get p-value for the agent_type coefficient
            p_val = cph.summary['p'][0] # Assumes first col is the covariate
            return {
                "method": "cox",
                "pvalue": float(p_val),
                "concordance": float(cph.concordance_index_)
            }
        except Exception as e:
            return {"method": "cox", "error": str(e)}
    
    return {"method": "cox", "conclusion": "missing_agent_type"}

def analyze_ranking_metrics(
    paired_logs: List[Dict[str, Any]],
    gt_map: Dict[str, List[int]]
) -> Dict[str, Any]:
    """
    Calculate ranking metrics (First Relevant Position) and run stats.
    Handles censored data (if relevant line not found, rank = N+1).
    """
    baseline_ranks = []
    iterative_ranks = []
    ids = []
    
    # Determine max lines for censoring penalty (approximate N)
    max_n = max([len(gt) for gt in gt_map.values()]) if gt_map else 100
    penalty = max_n + 1

    for pair in paired_logs:
        rid = pair["issue_id"]
        gt_lines = gt_map.get(rid, [])
        if not gt_lines:
            continue
        
        # Baseline
        b_retrieved = pair["baseline"].get("retrieved_lines", [])
        b_found = False
        b_rank = penalty
        for r in b_retrieved:
            if r in gt_lines:
                b_rank = b_retrieved.index(r) + 1
                b_found = True
                break
        
        # Iterative
        i_retrieved = pair["iterative"].get("retrieved_lines", [])
        i_found = False
        i_rank = penalty
        for r in i_retrieved:
            if r in gt_lines:
                i_rank = i_retrieved.index(r) + 1
                i_found = True
                break
        
        baseline_ranks.append(b_rank)
        iterative_ranks.append(i_rank)
        ids.append(rid)

    if len(baseline_ranks) == 0:
        return {"method": "none", "conclusion": "no_data"}

    # Check for ties/censoring
    n_censored_b = sum(1 for r in baseline_ranks if r == penalty)
    n_censored_i = sum(1 for r in iterative_ranks if r == penalty)
    total = len(baseline_ranks)
    
    if n_censored_b > 0.2 * total or n_censored_i > 0.2 * total:
        # Use Survival Analysis
        data = []
        for i, rid in enumerate(ids):
            data.append({
                "T": baseline_ranks[i],
                "E": 0 if baseline_ranks[i] == penalty else 1,
                "agent_type": "baseline"
            })
            data.append({
                "T": iterative_ranks[i],
                "E": 0 if iterative_ranks[i] == penalty else 1,
                "agent_type": "iterative"
            })
        return run_cox_survival_analysis(data)
    else:
        # Wilcoxon on ranks (lower is better, so we test difference)
        # Note: Wilcoxon tests if distributions are same. 
        # Since lower is better, we might want to test if iterative < baseline.
        # Standard Wilcoxon is two-sided.
        res = run_wilcoxon_signed_rank_test(np.array(baseline_ranks), np.array(iterative_ranks))
        res["metric"] = "first_relevant_rank"
        return res

# ---------------------------------------------------------------------------
# Bonferroni Correction & Associational Framing
# ---------------------------------------------------------------------------
def apply_bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to a family of p-values.
    Returns adjusted p-values and which hypotheses are significant.
    """
    m = len(p_values)
    if m == 0:
        return {"adjusted_p_values": [], "significant": [], "alpha": alpha}
    
    adjusted = [min(p * m, 1.0) for p in p_values]
    significant = [p_adj < alpha for p_adj in adjusted]
    
    return {
        "original_p_values": p_values,
        "adjusted_p_values": adjusted,
        "significant": significant,
        "alpha": alpha,
        "num_tests": m,
        "method": "bonferroni"
    }

def format_associational_statement(
    test_name: str,
    p_value: float,
    adjusted_p: float,
    significant: bool,
    direction: str = "difference"
) -> str:
    """
    Generate a text statement framing the result as an associational difference.
    FR-007: Avoid causal claims.
    """
    sig_text = "statistically significant" if significant else "not statistically significant"
    # Direction is descriptive of the observed difference, not causal
    if significant:
        return (
            f"The analysis observed a {sig_text} {direction} in {test_name} "
            f"(p={p_value:.4f}, Bonferroni-adjusted p={adjusted_p:.4f}). "
            f"This suggests an association between the agent strategy and the observed metric."
        )
    else:
        return (
            f"The analysis did not observe a {sig_text} {direction} in {test_name} "
            f"(p={p_value:.4f}, Bonferroni-adjusted p={adjusted_p:.4f}). "
            f"No association was detected between the agent strategy and the metric."
        )

# ---------------------------------------------------------------------------
# Main Orchestrator for T031c
# ---------------------------------------------------------------------------
def main():
    """
    Execute T031c:
    1. Load paired logs.
    2. Compute coverage and ranking metrics.
    3. Run statistical tests (Wilcoxon/Permutation/Cox).
    4. Apply Bonferroni correction.
    5. Format results as associational differences.
    6. Save to data/results/final_metrics.json.
    """
    results_dir = get_path("results")
    curated_dir = get_path("curated")
    
    # Load ground truth mapping
    # We assume ground_truth_lines are stored in the curated issues or derived separately.
    # For this task, we load the hard_subset.jsonl to get the GT lines if they are embedded,
    # or we assume a mapping exists. 
    # Based on T013/T014, ground_truth_lines are derived. We need to load them.
    # Let's assume they are in the curated issues.
    hard_path = curated_dir / "hard_subset.jsonl"
    if not hard_path.exists():
        print(f"Error: {hard_path} not found. Cannot compute coverage.", file=sys.stderr)
        sys.exit(1)
    
    gt_map = {}
    with open(hard_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                rid = rec.get("issue_id")
                # Assuming 'ground_truth_lines' is a field in the curated record
                if "ground_truth_lines" in rec:
                    gt_map[rid] = rec["ground_truth_lines"]
                else:
                    # Fallback: try to parse from code if structure allows, but strictly
                    # we rely on the derived data from T013.
                    warnings.warn(f"Issue {rid} missing ground_truth_lines in curated data.")

    # Load paired logs
    try:
        paired_logs = load_agent_logs_for_pairing(results_dir)
    except FileNotFoundError as e:
        print(f"Error loading logs: {e}", file=sys.stderr)
        sys.exit(1)

    if not paired_logs:
        print("Error: No paired logs found.", file=sys.stderr)
        sys.exit(1)

    # 1. Coverage Analysis
    b_covs, i_covs, cov_ids = compute_paired_coverage_data(paired_logs, gt_map)
    coverage_test = run_wilcoxon_signed_rank_test(b_covs, i_covs)
    
    # 2. Ranking Analysis
    ranking_result = analyze_ranking_metrics(paired_logs, gt_map)
    
    # Collect p-values for Bonferroni
    p_values = []
    test_names = []
    test_details = {}
    
    # Coverage
    p_values.append(coverage_test["pvalue"])
    test_names.append("coverage")
    test_details["coverage"] = coverage_test
    
    # Ranking
    if "pvalue" in ranking_result:
        p_values.append(ranking_result["pvalue"])
        test_names.append("ranking")
        test_details["ranking"] = ranking_result
    else:
        # If ranking used Cox or returned error, handle gracefully
        if "error" in ranking_result:
            print(f"Ranking analysis failed: {ranking_result['error']}", file=sys.stderr)
        # Skip adding to Bonferroni if no valid p-value
        # But per SC-004, we need to correct the family of tests performed.
        # If we couldn't perform ranking, we note it.
        if ranking_result.get("method") != "none":
             # If Cox was used, it has a pvalue. If not, we might have an issue.
             pass

    # 3. Bonferroni Correction
    bonf_result = apply_bonferroni_correction(p_values)
    
    # 4. Format Associational Statements
    final_results = {
        "metadata": {
            "n_issues": len(paired_logs),
            "n_coverage_pairs": len(b_covs),
            "n_ranking_pairs": len(ranking_result.get("data", [])) if isinstance(ranking_result, dict) else 0,
            "bonferroni_alpha": 0.05,
            "timestamp": str(Path(__file__).parent.stat().st_mtime) # Placeholder for real timestamp
        },
        "coverage_analysis": {
            "test": test_details["coverage"],
            "bonferroni_adjusted_p": bonf_result["adjusted_p_values"][0] if len(bonf_result["adjusted_p_values"]) > 0 else None,
            "significant": bonf_result["significant"][0] if len(bonf_result["significant"]) > 0 else False,
            "statement": format_associational_statement(
                "coverage",
                test_details["coverage"]["pvalue"],
                bonf_result["adjusted_p_values"][0] if len(bonf_result["adjusted_p_values"]) > 0 else 1.0,
                bonf_result["significant"][0] if len(bonf_result["significant"]) > 0 else False
            )
        },
        "ranking_analysis": {},
        "bonferroni_summary": bonf_result
    }
    
    if len(bonf_result["adjusted_p_values"]) > 1:
        final_results["ranking_analysis"] = {
            "test": ranking_result,
            "bonferroni_adjusted_p": bonf_result["adjusted_p_values"][1],
            "significant": bonf_result["significant"][1],
            "statement": format_associational_statement(
                "ranking",
                ranking_result.get("pvalue", 1.0),
                bonf_result["adjusted_p_values"][1],
                bonf_result["significant"][1]
            )
        }
    else:
        # Only coverage was tested
        final_results["ranking_analysis"] = {
            "status": "skipped_or_failed",
            "details": ranking_result
        }

    # 5. Write Output
    output_path = results_dir / "final_metrics.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=2)
    
    print(f"Final metrics written to {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
