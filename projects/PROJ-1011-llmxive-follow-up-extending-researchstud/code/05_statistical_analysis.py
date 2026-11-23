import json
import logging
import os
import sys
import math
import statistics
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import csv
from datetime import datetime

# Import from utils as per API surface
from utils.logging_config import get_logger
from utils.error_handling import IRRGateFailError, ValidationError

# Import statsmodels for power analysis
try:
    from statsmodels.stats.power import tt_solve_power
    from statsmodels.stats.inter_rater import krippendorff_alpha as sk_krippendorff_alpha
    from scipy import stats
    from scipy.stats import iqr
    STATS_AVAILABLE = True
except ImportError:
    STATS_AVAILABLE = False
    # Fallback placeholders to allow import if statsmodels/scipy missing, 
    # but main() will fail loudly if used.
    def tt_solve_power(*args, **kwargs):
        raise ImportError("statsmodels required for power analysis")

# Constants
RESULTS_DIR = Path("data/results")
LOGS_DIR = Path("logs")
ALPHA_THRESHOLD = 0.6
IQR_MULTIPLIER = 1.5
DEFAULT_N = 50
DEFAULT_ALPHA = 0.05

logger = get_logger(__name__)

def ensure_results_dir():
    """Ensure the results directory exists."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

def load_ratings(filepath: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load expert ratings from CSV."""
    if filepath is None:
        filepath = RESULTS_DIR / "ratings_real.csv"
    if not filepath.exists():
        # Fallback to filled for testing if real not present, but log warning
        alt = RESULTS_DIR / "ratings_filled.csv"
        if alt.exists():
            logger.warning(f"Real ratings not found, using mock: {alt}")
            filepath = alt
        else:
            raise FileNotFoundError(f"Ratings file not found: {filepath} or {alt}")
    
    ratings = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert score fields to float
            if 'score' in row:
                row['score'] = float(row['score'])
            if 'contextual_alignment' in row:
                row['contextual_alignment'] = float(row['contextual_alignment'])
            ratings.append(row)
    return ratings

def load_generated_proposals(filepath: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load generated proposals from JSONL."""
    if filepath is None:
        filepath = RESULTS_DIR / "generated_proposals.jsonl"
    if not filepath.exists():
        raise FileNotFoundError(f"Generated proposals not found: {filepath}")
    
    proposals = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                proposals.append(json.loads(line))
    return proposals

def calculate_krippendorff_alpha(ratings: List[Dict[str, Any]]) -> float:
    """Calculate Krippendorff's alpha for inter-rater reliability."""
    if not STATS_AVAILABLE:
        raise ImportError("statsmodels required for IRR calculation")
    
    # Reshape data: rows = items, cols = raters (simplified aggregation)
    # Assuming each row in ratings is a single rating event. 
    # We need to group by problem_id and extract scores.
    items = {}
    for r in ratings:
        pid = r.get('problem_id') or r.get('proposal_id')
        if pid not in items:
            items[pid] = []
        # Use 'score' if available, else 'contextual_alignment'
        score = r.get('score') or r.get('contextual_alignment')
        if score is not None:
            items[pid].append(score)
    
    if not items:
        raise ValueError("No valid ratings found for IRR calculation")
    
    # Pad to max length with None (krippendorff_alpha handles NaN)
    max_len = max(len(v) for v in items.values())
    matrix = []
    for pid, scores in items.items():
        row = scores + [float('nan')] * (max_len - len(scores))
        matrix.append(row)
    
    alpha = sk_krippendorff_alpha(matrix, level_of_measurement='interval')
    return alpha

def check_normality(scores: List[float]) -> Tuple[bool, float]:
    """Perform Shapiro-Wilk normality test."""
    if not STATS_AVAILABLE:
        raise ImportError("scipy required for normality check")
    
    if len(scores) < 3:
        logger.warning("Insufficient data for normality test, assuming normal.")
        return True, 1.0
    
    stat, p_value = stats.shapiro(scores)
    is_normal = p_value > 0.05
    return is_normal, p_value

def handle_outliers_iqr(scores: List[float]) -> Tuple[List[float], List[int]]:
    """Remove outliers based on IQR method."""
    if len(scores) < 4:
        return scores, []
    
    q1 = statistics.quantiles(scores, n=4)[0]
    q3 = statistics.quantiles(scores, n=4)[2]
    iqr_val = q3 - q1
    lower_bound = q1 - (IQR_MULTIPLIER * iqr_val)
    upper_bound = q3 + (IQR_MULTIPLIER * iqr_val)
    
    cleaned = []
    removed_indices = []
    for i, s in enumerate(scores):
        if lower_bound <= s <= upper_bound:
            cleaned.append(s)
        else:
            removed_indices.append(i)
    
    return cleaned, removed_indices

def perform_statistical_test(group_a: List[float], group_b: List[float]) -> Dict[str, Any]:
    """Perform paired t-test or Wilcoxon signed-rank test."""
    if not STATS_AVAILABLE:
        raise ImportError("scipy required for statistical tests")
    
    # Check normality of differences
    diffs = [a - b for a, b in zip(group_a, group_b)]
    is_normal, p_norm = check_normality(diffs)
    
    result = {
        "test_type": "t-test" if is_normal else "wilcoxon",
        "normality_p_value": p_norm
    }
    
    if is_normal:
        stat, p_val = stats.ttest_rel(group_a, group_b)
        # Cohen's d for paired samples
        mean_diff = statistics.mean(diffs)
        std_diff = statistics.stdev(diffs) if len(diffs) > 1 else 0
        cohens_d = mean_diff / std_diff if std_diff != 0 else 0
        result["p_value"] = p_val
        result["effect_size"] = cohens_d
        result["effect_size_type"] = "cohen_d"
    else:
        stat, p_val = stats.wilcoxon(group_a, group_b)
        # Rank-biserial correlation for Wilcoxon
        n = len(diffs)
        r = abs(stat) / (0.5 * n * (n + 1))
        result["p_value"] = p_val
        result["effect_size"] = r
        result["effect_size_type"] = "rank_biserial"
    
    return result

def correct_multiple_comparisons(p_values: List[float], method: str = "bonferroni") -> List[float]:
    """Apply multiple comparison correction."""
    if not STATS_AVAILABLE:
        raise ImportError("scipy required for multiple comparison correction")
    
    if method == "bonferroni":
        return [min(p * len(p_values), 1.0) for p in p_values]
    elif method == "benjamini_hochberg":
        # Simple implementation of BH
        n = len(p_values)
        sorted_indices = sorted(range(n), key=lambda i: p_values[i])
        corrected = [0.0] * n
        rank = 1
        for i in sorted_indices:
            corrected[i] = min(p_values[i] * n / rank, 1.0)
            rank += 1
        return corrected
    else:
        return p_values

def run_sensitivity_analysis(
    group_a: List[float], 
    group_b: List[float], 
    with_outliers: bool = True
) -> Dict[str, Any]:
    """Run statistical test with or without outliers."""
    if with_outliers:
        scores_a, scores_b = group_a, group_b
    else:
        scores_a, _ = handle_outliers_iqr(group_a)
        scores_b, _ = handle_outliers_iqr(group_b)
    
    if len(scores_a) != len(scores_b) or len(scores_a) == 0:
        raise ValueError("Insufficient data for sensitivity analysis after outlier removal.")
    
    return perform_statistical_test(scores_a, scores_b)

def calculate_validity_improvement(ratings: List[Dict[str, Any]], proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate mean difference in contextual alignment scores."""
    # Group by problem_id and calculate mean per group
    pg_scores = []
    bg_scores = []
    
    # Create lookup for proposals to get group
    prop_map = {p.get('problem_id'): p.get('group') for p in proposals}
    
    for r in ratings:
        pid = r.get('problem_id') or r.get('proposal_id')
        group = prop_map.get(pid)
        score = r.get('contextual_alignment') or r.get('score')
        if score is not None:
            if group == 'pattern-guided':
                pg_scores.append(score)
            elif group == 'baseline':
                bg_scores.append(score)
    
    if not pg_scores or not bg_scores:
        raise ValueError("Missing scores for one of the groups.")
    
    mean_diff = statistics.mean(pg_scores) - statistics.mean(bg_scores)
    
    # Perform test on these specific scores
    test_result = perform_statistical_test(pg_scores, bg_scores)
    
    return {
        "mean_diff": mean_diff,
        "p_value": test_result["p_value"],
        "effect_size": test_result["effect_size"]
    }

def calculate_post_hoc_power(n: int, effect_size: float, alpha: float = 0.05) -> float:
    """Calculate achieved statistical power."""
    if not STATS_AVAILABLE:
        raise ImportError("statsmodels required for power analysis")
    
    # For paired t-test, use tt_solve_power
    # effect_size is Cohen's d
    try:
        power = tt_solve_power(effect_size=effect_size, nobs1=n, alpha=alpha, alternative='two-sided')
        return power
    except Exception as e:
        logger.error(f"Power calculation failed: {e}")
        return 0.0

def calculate_mdes(n: int, alpha: float = 0.05, power: float = 0.80) -> float:
    """Calculate Minimum Detectable Effect Size for given power."""
    if not STATS_AVAILABLE:
        raise ImportError("statsmodels required for MDES calculation")
    
    try:
        mdes = tt_solve_power(effect_size=None, nobs1=n, alpha=alpha, power=power, alternative='two-sided')
        return mdes
    except Exception as e:
        logger.error(f"MDES calculation failed: {e}")
        return 0.0

def generate_final_report(
    ratings: List[Dict[str, Any]], 
    proposals: List[Dict[str, Any]],
    power_report_path: Optional[Path] = None
) -> str:
    """Generate the final analysis report including sensitivity and power analysis."""
    ensure_results_dir()
    
    # 1. IRR Gate
    try:
        alpha = calculate_krippendorff_alpha(ratings)
        if alpha < ALPHA_THRESHOLD:
            raise IRRGateFailError(f"IRR gate failed: Krippendorff's alpha ({alpha:.3f}) < {ALPHA_THRESHOLD}")
        logger.info(f"IRR Gate Passed: Alpha = {alpha:.3f}")
    except IRRGateFailError:
        raise
    except Exception as e:
        logger.error(f"IRR calculation error: {e}")
        raise

    # 2. Extract scores
    pg_scores = []
    bg_scores = []
    prop_map = {p.get('problem_id'): p for p in proposals}
    
    for r in ratings:
        pid = r.get('problem_id') or r.get('proposal_id')
        group = prop_map.get(pid, {}).get('group')
        score = r.get('contextual_alignment') or r.get('score')
        if score is not None:
            if group == 'pattern-guided':
                pg_scores.append(score)
            elif group == 'baseline':
                bg_scores.append(score)
    
    if len(pg_scores) != len(bg_scores) or len(pg_scores) == 0:
        raise ValueError("Mismatched or empty groups for statistical test.")
    
    # 3. Outlier Handling & Sensitivity
    pg_clean, rem_pg = handle_outliers_iqr(pg_scores)
    bg_clean, rem_bg = handle_outliers_iqr(bg_scores)
    
    report_lines = [
        "# Statistical Analysis Report",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## 1. Inter-Rater Reliability",
        f"- Krippendorff's Alpha: {alpha:.3f} (Threshold: {ALPHA_THRESHOLD})",
        "",
        "## 2. Outlier Handling (IQR Method)",
        f"- Outliers removed from Pattern-Guided: {len(pg_scores) - len(pg_clean)}",
        f"- Outliers removed from Baseline: {len(bg_scores) - len(bg_clean)}",
        "",
        "## 3. Sensitivity Analysis",
    ]
    
    # Run tests
    res_with = run_sensitivity_analysis(pg_scores, bg_scores, with_outliers=True)
    res_without = run_sensitivity_analysis(pg_scores, bg_scores, with_outliers=False)
    
    report_lines.append(f"### With Outliers")
    report_lines.append(f"- Test: {res_with['test_type']}")
    report_lines.append(f"- P-value: {res_with['p_value']:.4f}")
    report_lines.append(f"- Effect Size ({res_with['effect_size_type']}): {res_with['effect_size']:.4f}")
    
    report_lines.append(f"### Without Outliers")
    report_lines.append(f"- Test: {res_without['test_type']}")
    report_lines.append(f"- P-value: {res_without['p_value']:.4f}")
    report_lines.append(f"- Effect Size ({res_without['effect_size_type']}): {res_without['effect_size']:.4f}")
    
    delta_p = abs(res_with['p_value'] - res_without['p_value'])
    report_lines.append(f"- Delta P-value: {delta_p:.4f}")
    report_lines.append("")
    
    # 4. Primary Test (on cleaned data)
    final_test = res_without
    report_lines.append("## 4. Primary Statistical Test (Cleaned Data)")
    report_lines.append(f"- Method: {final_test['test_type']}")
    report_lines.append(f"- P-value: {final_test['p_value']:.4f}")
    report_lines.append(f"- Effect Size: {final_test['effect_size']:.4f} ({final_test['effect_size_type']})")
    
    # 5. Multiple Comparison Correction
    corrected_p = correct_multiple_comparisons([final_test['p_value']])[0]
    report_lines.append(f"- Corrected P-value (Bonferroni): {corrected_p:.4f}")
    report_lines.append("")
    
    # 6. Power Analysis & Sensitivity (T069)
    n_pairs = len(pg_clean)
    effect_size = final_test['effect_size']
    power = calculate_post_hoc_power(n_pairs, effect_size)
    
    report_lines.append("## 5. Power Analysis")
    report_lines.append(f"- Sample Size (n): {n_pairs}")
    report_lines.append(f"- Observed Effect Size: {effect_size:.4f}")
    report_lines.append(f"- Achieved Power: {power:.4f}")
    
    # T069: Power Analysis Sensitivity
    if power < 0.80:
        mdes = calculate_mdes(n_pairs)
        report_lines.append("")
        report_lines.append("### Power Analysis Sensitivity (T069)")
        report_lines.append(f"- **Warning**: Achieved power ({power:.4f}) is below 0.80.")
        report_lines.append(f"- **Minimum Detectable Effect Size (MDES)** for n={n_pairs}, alpha=0.05, power=0.80: {mdes:.4f}")
        report_lines.append(f"- Interpretation: The study was underpowered to detect effects smaller than {mdes:.4f}.")
    
    report_lines.append("")
    report_lines.append("## 6. Conclusion")
    report_lines.append(f"- The analysis is **associational, not causal**.")
    if final_test['p_value'] < 0.05:
        report_lines.append("- There is a statistically significant difference between groups.")
    else:
        report_lines.append("- No statistically significant difference was found.")
    
    report_content = "\n".join(report_lines)
    
    # Write report
    report_path = RESULTS_DIR / "analysis_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"Final report written to {report_path}")
    
    # Write Power Report JSON
    power_report = {
        "n": n_pairs,
        "effect_size": effect_size,
        "power": power,
        "threshold": 0.80,
        "status": "underpowered" if power < 0.80 else "adequate",
        "mdes": calculate_mdes(n_pairs) if power < 0.80 else None
    }
    power_json_path = RESULTS_DIR / "power_analysis_report.json"
    with open(power_json_path, 'w', encoding='utf-8') as f:
        json.dump(power_report, f, indent=2)
    
    logger.info(f"Power analysis report written to {power_json_path}")
    
    return report_content

def main():
    """Main entry point for statistical analysis."""
    ensure_results_dir()
    
    try:
        # Load data
        ratings = load_ratings()
        proposals = load_generated_proposals()
        
        # Run full pipeline
        generate_final_report(ratings, proposals)
        
        # Also generate validity metrics
        validity = calculate_validity_improvement(ratings, proposals)
        validity_path = RESULTS_DIR / "validity_metrics.json"
        with open(validity_path, 'w', encoding='utf-8') as f:
            json.dump(validity, f, indent=2)
        logger.info(f"Validity metrics written to {validity_path}")
        
    except IRRGateFailError as e:
        logger.critical(f"Pipeline halted: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()