import os
import csv
import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy.stats import wilcoxon, chi2_contingency, shapiro, ttest_rel
from statsmodels.stats.power import TTestPower, TTestIndPower, z_power_proportion

# --- Loaders and Groupers ---

def load_paired_dataset(csv_path: str) -> List[Dict[str, Any]]:
    """Loads the final paired dataset from CSV."""
    data = []
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Paired dataset not found at {csv_path}")
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def group_by_task_type(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Groups dataset rows by task_type."""
    groups = {}
    for row in data:
        t_type = row.get('task_type', 'unknown')
        if t_type not in groups:
            groups[t_type] = []
        groups[t_type].append(row)
    return groups

def extract_success_pairs(group: List[Dict[str, Any]]) -> Tuple[List[int], List[int]]:
    """Extracts success flags (0/1) for 2D and 3D agents."""
    s_2d = []
    s_3d = []
    for row in group:
        try:
            val_2d = int(float(row.get('2d_success_rate', 0)))
            val_3d = int(float(row.get('3d_success', 0)))
            s_2d.append(val_2d)
            s_3d.append(val_3d)
        except (ValueError, TypeError):
            continue
    return s_2d, s_3d

def extract_latency_pairs(group: List[Dict[str, Any]]) -> Tuple[List[float], List[float]]:
    """Extracts latency values for 2D and 3D agents."""
    l_2d = []
    l_3d = []
    for row in group:
        try:
            val_2d = float(row.get('2d_mean_latency', 0))
            val_3d = float(row.get('3d_latency', 0))
            l_2d.append(val_2d)
            l_3d.append(val_3d)
        except (ValueError, TypeError):
            continue
    return l_2d, l_3d

# --- Statistical Tests ---

def run_mcnemar_test(s_2d: List[int], s_3d: List[int]) -> Dict[str, Any]:
    """
    Performs McNemar's test for paired binary data.
    Returns dict with statistic, p-value, and conclusion.
    """
    if len(s_2d) == 0 or len(s_3d) == 0:
        return {"error": "Insufficient data for McNemar test"}
    
    # Construct contingency table for discordant pairs
    # b: 2D Fail (0), 3D Success (1)
    # c: 2D Success (1), 3D Fail (0)
    b = 0
    c = 0
    for a, b_val in zip(s_2d, s_3d):
        if a == 0 and b_val == 1:
            b += 1
        elif a == 1 and b_val == 0:
            c += 1
    
    if b + c == 0:
        return {"statistic": 0.0, "p_value": 1.0, "conclusion": "No discordant pairs"}
    
    # McNemar statistic: (|b - c| - 1)^2 / (b + c) with continuity correction
    stat = (abs(b - c) - 1) ** 2 / (b + c)
    # P-value from Chi-square distribution with 1 df
    p_val = 1 - chi2_contingency([[b, b], [c, c]])[1] # Approximation logic, using scipy directly
    # Actually, scipy.stats.chi2.sf is better for manual calculation
    from scipy.stats import chi2
    p_val = chi2.sf(stat, 1)
    
    return {
        "statistic": float(stat),
        "p_value": float(p_val),
        "discordant_b": b,
        "discordant_c": c,
        "conclusion": "Significant difference" if p_val < 0.05 else "No significant difference"
    }

def check_normality(diffs: List[float]) -> Dict[str, Any]:
    """
    Performs Shapiro-Wilk test for normality.
    Returns dict with statistic, p-value, and is_normal boolean.
    """
    if len(diffs) < 3:
        return {"error": "Insufficient data for Shapiro-Wilk test"}
    
    stat, p_val = shapiro(diffs)
    is_normal = p_val > 0.05
    
    return {
        "statistic": float(stat),
        "p_value": float(p_val),
        "is_normal": is_normal,
        "conclusion": "Normal distribution" if is_normal else "Non-normal distribution"
    }

def run_ttest(l_2d: List[float], l_3d: List[float]) -> Dict[str, Any]:
    """
    Performs paired t-test.
    Returns dict with statistic, p-value, and effect size (Cohen's d).
    """
    if len(l_2d) < 2 or len(l_3d) < 2:
        return {"error": "Insufficient data for t-test"}
    
    stat, p_val = ttest_rel(l_2d, l_3d)
    
    # Calculate Cohen's d for paired samples
    # d = mean(diff) / std(diff)
    diffs = np.array(l_2d) - np.array(l_3d)
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1) # Sample std dev
    
    if std_diff == 0:
        cohens_d = 0.0
    else:
        cohens_d = mean_diff / std_diff
    
    # Qualitative interpretation
    abs_d = abs(cohens_d)
    if abs_d < 0.2:
        interpretation = "negligible"
    elif abs_d < 0.5:
        interpretation = "small"
    elif abs_d < 0.8:
        interpretation = "medium"
    else:
        interpretation = "large"
    
    return {
        "statistic": float(stat),
        "p_value": float(p_val),
        "cohens_d": float(cohens_d),
        "effect_size_interpretation": interpretation,
        "conclusion": "Significant difference" if p_val < 0.05 else "No significant difference"
    }

def run_wilcoxon_test(l_2d: List[float], l_3d: List[float]) -> Dict[str, Any]:
    """
    Performs Wilcoxon signed-rank test.
    Returns dict with statistic, p-value, and effect size (Rank-Biserial Correlation).
    """
    if len(l_2d) < 2 or len(l_3d) < 2:
        return {"error": "Insufficient data for Wilcoxon test"}
    
    stat, p_val = wilcoxon(l_2d, l_3d)
    
    # Calculate Rank-Biserial Correlation (r)
    # r = Z / sqrt(N)
    # Approximation for Z from Wilcoxon statistic (W)
    # For large N, W is approximately normal.
    # A common approximation for effect size r is:
    # r = 1 - (2 * U) / (n1 * n2) for Mann-Whitney, but for Wilcoxon signed rank:
    # r = Z / sqrt(N)
    # We can estimate Z from the p-value if we assume normality, but scipy doesn't return Z directly.
    # Alternative: r = (W - expected_W) / std_W ?
    # Simpler robust approximation for paired data effect size:
    # r = 1 - (2 * |W - n(n+1)/4|) / (n(n+1)/2) ? No.
    # Let's use the standard approximation: r = Z / sqrt(N)
    # We can derive Z from the p-value (two-tailed)
    from scipy.stats import norm
    z_score = norm.ppf(1 - p_val / 2)
    # Handle edge cases where p_val is very small or 1
    if p_val <= 0:
        z_score = 10 # Cap
    elif p_val >= 1:
        z_score = 0
    
    n = len(l_2d)
    if n == 0:
        r = 0.0
    else:
        r = z_score / np.sqrt(n)
    
    # Qualitative interpretation (Cohen's conventions for r)
    abs_r = abs(r)
    if abs_r < 0.1:
        interpretation = "negligible"
    elif abs_r < 0.3:
        interpretation = "small"
    elif abs_r < 0.5:
        interpretation = "medium"
    else:
        interpretation = "large"
    
    return {
        "statistic": float(stat),
        "p_value": float(p_val),
        "rank_biserial_correlation": float(r),
        "effect_size_interpretation": interpretation,
        "conclusion": "Significant difference" if p_val < 0.05 else "No significant difference"
    }

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Applies Bonferroni correction to a list of p-values.
    Returns list of dicts with raw_p, corrected_p, and significance.
    """
    results = []
    m = len(p_values)
    if m == 0:
        return results
    
    adjusted_alpha = alpha / m
    
    for i, p in enumerate(p_values):
        corrected_p = min(p * m, 1.0)
        is_sig = corrected_p < alpha
        results.append({
            "index": i,
            "raw_p": float(p),
            "corrected_p": float(corrected_p),
            "significant": is_sig
        })
    return results

# --- Main Orchestration for T062 ---

def run_statistical_tests(paired_csv_path: str) -> Dict[str, Any]:
    """
    Runs statistical tests on the paired dataset and calculates effect sizes.
    This function fulfills T062 requirements.
    """
    try:
        data = load_paired_dataset(paired_csv_path)
    except FileNotFoundError as e:
        return {"error": str(e)}
    
    groups = group_by_task_type(data)
    results = {}
    
    for task_type, rows in groups.items():
        # Extract data
        s_2d, s_3d = extract_success_pairs(rows)
        l_2d, l_3d = extract_latency_pairs(rows)
        
        # 1. Success Rate Analysis (McNemar)
        mcnemar_res = run_mcnemar_test(s_2d, s_3d)
        
        # 2. Latency Analysis (Normality -> T-test or Wilcoxon)
        if len(l_2d) < 3:
            latency_res = {"error": "Insufficient data for latency analysis"}
        else:
            diffs = np.array(l_2d) - np.array(l_3d)
            normality_res = check_normality(diffs.tolist())
            
            if normality_res.get("is_normal", False):
                latency_res = run_ttest(l_2d, l_3d)
                latency_res["test_used"] = "Paired T-test"
                latency_res["normality_check"] = normality_res
            else:
                latency_res = run_wilcoxon_test(l_2d, l_3d)
                latency_res["test_used"] = "Wilcoxon Signed-Rank Test"
                latency_res["normality_check"] = normality_res
        
        results[task_type] = {
            "n_samples": len(rows),
            "success_analysis": mcnemar_res,
            "latency_analysis": latency_res
        }
    
    return results

def generate_report_markdown(results: Dict[str, Any], output_path: str):
    """
    Generates the final statistical report markdown including effect sizes.
    """
    lines = []
    lines.append("# Final Statistical Report (with Effect Sizes)")
    lines.append("")
    lines.append(f"Generated on: {os.popen('date').read().strip()}")
    lines.append("")
    
    all_p_values = []
    
    for task_type, res in results.items():
        lines.append(f"## Task Type: {task_type}")
        lines.append("")
        lines.append(f"- **Sample Size (N):** {res['n_samples']}")
        lines.append("")
        
        # Success Analysis
        lines.append("### Success Rate Analysis (McNemar's Test)")
        if "error" in res["success_analysis"]:
            lines.append(f"- **Error:** {res['success_analysis']['error']}")
        else:
            stat = res["success_analysis"]["statistic"]
            p = res["success_analysis"]["p_value"]
            all_p_values.append(p)
            lines.append(f"- **Statistic:** {stat:.4f}")
            lines.append(f"- **P-value:** {p:.4f}")
            lines.append(f"- **Conclusion:** {res['success_analysis']['conclusion']}")
        lines.append("")
        
        # Latency Analysis
        lines.append("### Latency Analysis")
        if "error" in res["latency_analysis"]:
            lines.append(f"- **Error:** {res['latency_analysis']['error']}")
        else:
            test_used = res["latency_analysis"].get("test_used", "Unknown")
            lines.append(f"- **Test Used:** {test_used}")
            
            # Normality Check
            if "normality_check" in res["latency_analysis"]:
                nc = res["latency_analysis"]["normality_check"]
                lines.append(f"- **Normality (Shapiro-Wilk):** p={nc['p_value']:.4f} ({nc['conclusion']})")
            
            stat = res["latency_analysis"]["statistic"]
            p = res["latency_analysis"]["p_value"]
            all_p_values.append(p)
            
            lines.append(f"- **Statistic:** {stat:.4f}")
            lines.append(f"- **P-value:** {p:.4f}")
            
            # Effect Size
            if "cohens_d" in res["latency_analysis"]:
                d = res["latency_analysis"]["cohens_d"]
                interp = res["latency_analysis"]["effect_size_interpretation"]
                lines.append(f"- **Effect Size (Cohen's d):** {d:.4f} ({interp})")
            elif "rank_biserial_correlation" in res["latency_analysis"]:
                r = res["latency_analysis"]["rank_biserial_correlation"]
                interp = res["latency_analysis"]["effect_size_interpretation"]
                lines.append(f"- **Effect Size (Rank-Biserial r):** {r:.4f} ({interp})")
            
            lines.append(f"- **Conclusion:** {res['latency_analysis']['conclusion']}")
        lines.append("")
    
    # Bonferroni Correction
    lines.append("## Multiple Comparison Correction (Bonferroni)")
    lines.append("")
    if len(all_p_values) > 0:
        corrections = apply_bonferroni_correction(all_p_values)
        lines.append("| Task Type | Raw P-value | Corrected P-value | Significant? |")
        lines.append("| :--- | :--- | :--- | :--- |")
        idx = 0
        for task_type in results:
            if idx < len(corrections):
                c = corrections[idx]
                lines.append(f"| {task_type} | {c['raw_p']:.4f} | {c['corrected_p']:.4f} | {'Yes' if c['significant'] else 'No'} |")
                idx += 1
    else:
        lines.append("No p-values to correct.")
    lines.append("")
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run statistical tests and generate report with effect sizes (T062)")
    parser.add_argument("--input", type=str, default="results/analysis/final_paired_dataset.csv", help="Path to paired dataset CSV")
    parser.add_argument("--output", type=str, default="results/analysis/final_statistical_report.md", help="Path for output markdown report")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Loading data from {args.input}")
    results = run_statistical_tests(args.input)
    
    if "error" in results:
        logger.error(f"Statistical analysis failed: {results['error']}")
        return 1
    
    logger.info(f"Generating report at {args.output}")
    generate_report_markdown(results, args.output)
    
    logger.info("Done.")
    return 0

if __name__ == "__main__":
    exit(main())