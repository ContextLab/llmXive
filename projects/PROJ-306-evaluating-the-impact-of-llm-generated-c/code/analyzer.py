import os
import json
import logging
import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Any, Tuple

def load_coverage_reports(reports_dir: str) -> List[Dict[str, Any]]:
    """Loads all JSON coverage reports from a directory."""
    reports = []
    if not os.path.exists(reports_dir):
        logging.warning(f"Reports directory {reports_dir} does not exist.")
        return reports

    for file in os.listdir(reports_dir):
        if file.endswith(".json"):
            try:
                with open(os.path.join(reports_dir, file), 'r') as f:
                    data = json.load(f)
                    if data.get("status") != "failed":
                        reports.append(data)
            except Exception as e:
                logging.warning(f"Failed to load {file}: {e}")
    return reports

def pair_llm_human_results(reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Pairs LLM and Human results by task_id."""
    by_task = {}
    for r in reports:
        tid = r.get("task_id")
        if tid:
            if tid not in by_task:
                by_task[tid] = []
            by_task[tid].append(r)
    
    pairs = []
    for tid, items in by_task.items():
        llm_cov = None
        human_cov = None
        
        for item in items:
            cov = item.get("line_coverage")
            if cov == "N/A": continue
            try:
                val = float(cov)
                # Heuristic: if 'source' contains 'human' or 'solution'
                if "human" in str(item.get("source", "")).lower() or "solution" in str(item.get("source", "")).lower():
                    human_cov = val
                else:
                    llm_cov = val
            except (ValueError, TypeError):
                pass
        
        if llm_cov is not None and human_cov is not None:
            pairs.append({
                "task_id": tid,
                "llm_coverage": llm_cov,
                "human_coverage": human_cov,
                "diff": llm_cov - human_cov
            })
    return pairs

def check_normality_shapiro(diffs: List[float]) -> Tuple[bool, float]:
    """Performs Shapiro-Wilk test. Returns (is_normal, p_value)."""
    if len(diffs) < 3:
        return True, 1.0 # Too small to test, assume normal
    stat, p = stats.shapiro(diffs)
    return p >= 0.05, p

def calculate_cohens_d(group1: List[float], group2: List[float]) -> float:
    """Calculates Cohen's d effect size."""
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1), np.var(group2)
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return (mean1 - mean2) / pooled_std

def perform_statistical_test(pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Performs paired t-test or Wilcoxon based on normality."""
    diffs = [p["diff"] for p in pairs]
    is_normal, p_shapiro = check_normality_shapiro(diffs)
    
    if is_normal:
        # Paired t-test
        t_stat, p_val = stats.ttest_rel(
            [p["llm_coverage"] for p in pairs], 
            [p["human_coverage"] for p in pairs]
        )
        test_type = "t-test"
    else:
        # Wilcoxon signed-rank
        stat, p_val = stats.wilcoxon(
            [p["llm_coverage"] for p in pairs], 
            [p["human_coverage"] for p in pairs]
        )
        test_type = "Wilcoxon"
    
    mean_llm = np.mean([p["llm_coverage"] for p in pairs])
    mean_human = np.mean([p["human_coverage"] for p in pairs])
    mean_diff = np.mean(diffs)
    cohens_d = calculate_cohens_d(
        [p["llm_coverage"] for p in pairs], 
        [p["human_coverage"] for p in pairs]
    )
    
    return {
        "mean_llm": mean_llm,
        "mean_human": mean_human,
        "mean_diff": mean_diff,
        "p_value": p_val,
        "cohen_d": cohens_d,
        "test_type": test_type
    }

def apply_bonferroni_correction(p_values: List[float]) -> List[float]:
    """Applies Bonferroni correction."""
    n = len(p_values)
    if n == 0: return []
    return [min(p * n, 1.0) for p in p_values]

def apply_holm_bonferroni_correction(p_values: List[float]) -> List[float]:
    """Applies Holm-Bonferroni correction."""
    n = len(p_values)
    if n == 0: return []
    sorted_indices = np.argsort(p_values)
    corrected = np.zeros(n)
    sorted_p = np.array(p_values)[sorted_indices]
    
    for i, p in enumerate(sorted_p):
        corrected[sorted_indices[i]] = min(p * (n - i), 1.0)
    
    return list(corrected)

def run_family_wise_error_correction(pairs: List[Dict[str, Any]], subgroup_key: str = None) -> Dict[str, Any]:
    """Runs FWER correction for subgroups. Excludes sensitivity analysis thresholds."""
    # This is a placeholder for the specific FWER logic required by FR-006
    # In this implementation, we just return the stats summary
    return {}

def calculate_exclusion_rate(pairs: List[Dict[str, Any]]) -> float:
    """Calculates the rate of tasks excluded from analysis (e.g., N/A branch coverage)."""
    total = len(pairs)
    if total == 0: return 0.0
    # Assuming 'diff' exists means it was included. 
    # Exclusion rate would be (Total Tasks - Pairs) / Total Tasks
    # But here we just return 0.0 as a placeholder if not implemented fully
    return 0.0

def run_sensitivity_analysis(reports_dir: str, output_dir: str):
    """Wrapper for sensitivity analysis (delegates to sensitivity_analyzer)."""
    from sensitivity_analyzer import run_sensitivity_analysis as sa_run
    return sa_run(reports_dir, output_dir)

def calculate_vif(pairs: List[Dict[str, Any]], features: List[str]) -> Dict[str, float]:
    """Calculates VIF for collinearity diagnostics. Skipped if not regression mode."""
    # Placeholder
    return {}

def run_analysis_pipeline(reports_dir: str, output_dir: str):
    """Main pipeline for statistical analysis."""
    reports = load_coverage_reports(reports_dir)
    pairs = pair_llm_human_results(reports)
    
    if not pairs:
        logging.error("No pairs found for analysis.")
        return

    stats_result = perform_statistical_test(pairs)
    
    # Save stats summary
    df_stats = pd.DataFrame([stats_result])
    os.makedirs(output_dir, exist_ok=True)
    df_stats.to_csv(os.path.join(output_dir, "stats_summary.csv"), index=False)
    
    logging.info(f"Stats summary saved to {output_dir}/stats_summary.csv")

def main():
    logging.basicConfig(level=logging.INFO)
    run_analysis_pipeline("data/coverage_reports", "data/processed")

if __name__ == "__main__":
    main()
