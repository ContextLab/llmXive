import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from scipy import stats
from config import get_sample_limit
import pandas as pd
import logging
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_normality(differences: List[float]) -> Tuple[bool, float]:
    """
    Check normality of the differences using Shapiro-Wilk test.
    Returns (is_normal, p_value).
    Normality is assumed if p > 0.10 (stricter threshold per Plan).
    """
    if len(differences) < 3:
        logger.warning("Sample size too small for Shapiro-Wilk test. Assuming non-normal.")
        return False, 0.0
    
    stat, p_value = stats.shapiro(differences)
    is_normal = p_value > 0.10
    logger.info(f"Shapiro-Wilk test: stat={stat:.4f}, p-value={p_value:.4f}, is_normal={is_normal}")
    return is_normal, p_value

def run_statistical_test(manual_coverage: List[float], llm_coverage: List[float]) -> Dict[str, Any]:
    """
    Run the appropriate statistical test based on normality check.
    If normal, run paired t-test. Otherwise, run Wilcoxon signed-rank test.
    Returns a dictionary with test results.
    """
    if len(manual_coverage) != len(llm_coverage):
        raise ValueError("Manual and LLM coverage lists must have the same length.")
    
    differences = np.array(llm_coverage) - np.array(manual_coverage)
    is_normal, p_normal = check_normality(differences.tolist())
    
    result = {
        "test_type": "paired_t_test" if is_normal else "wilcoxon_signed_rank",
        "normality_p_value": p_normal,
        "mean_difference": float(np.mean(differences)),
        "std_difference": float(np.std(differences)),
        "n_samples": len(differences)
    }
    
    if is_normal:
        # Paired t-test
        t_stat, p_value = stats.ttest_rel(llm_coverage, manual_coverage)
        result["statistic"] = float(t_stat)
        result["p_value"] = float(p_value)
        logger.info(f"Paired t-test: t={t_stat:.4f}, p={p_value:.4f}")
    else:
        # Wilcoxon signed-rank test
        w_stat, p_value = stats.wilcoxon(llm_coverage, manual_coverage)
        result["statistic"] = float(w_stat)
        result["p_value"] = float(p_value)
        logger.info(f"Wilcoxon signed-rank test: W={w_stat:.4f}, p={p_value:.4f}")
    
    return result

def calculate_effect_size(manual_coverage: List[float], llm_coverage: List[float], test_type: str) -> Dict[str, float]:
    """
    Calculate effect size based on the test type.
    Cohen's d for t-test, Rank-biserial correlation for Wilcoxon.
    """
    differences = np.array(llm_coverage) - np.array(manual_coverage)
    
    if test_type == "paired_t_test":
        # Cohen's d for paired samples
        mean_diff = np.mean(differences)
        std_diff = np.std(differences, ddof=1)
        if std_diff == 0:
            cohens_d = 0.0
        else:
            cohens_d = mean_diff / std_diff
        
        logger.info(f"Cohen's d: {cohens_d:.4f}")
        return {"cohens_d": float(cohens_d), "effect_size_type": "cohens_d"}
    else:
        # Rank-biserial correlation for Wilcoxon
        # r = 1 - (2 * W) / (n * (n + 1))
        n = len(differences)
        if n < 2:
            rank_biserial = 0.0
        else:
            # Re-run wilcoxon to get W if not passed, or calculate from ranks
            # Using scipy's wilcoxon result directly is better, but here we calculate
            # Note: scipy.stats.wilcoxon returns (W, p)
            # We need W (sum of positive ranks)
            # Let's recompute W
            from scipy.stats import rankdata
            abs_diffs = np.abs(differences)
            ranks = rankdata(abs_diffs)
            signs = np.sign(differences)
            W = np.sum(ranks[signs > 0])
            rank_biserial = 1 - (2 * W) / (n * (n + 1))
        
        logger.info(f"Rank-biserial correlation: {rank_biserial:.4f}")
        return {"rank_biserial": float(rank_biserial), "effect_size_type": "rank_biserial"}

def interpret_cohen_d(cohens_d: float) -> str:
    """
    Interpret Cohen's d effect size.
    """
    abs_d = abs(cohens_d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"

def interpret_rank_biserial(r: float) -> str:
    """
    Interpret Rank-biserial correlation effect size.
    """
    abs_r = abs(r)
    if abs_r < 0.1:
        return "negligible"
    elif abs_r < 0.3:
        return "small"
    elif abs_r < 0.5:
        return "medium"
    else:
        return "large"

def run_power_analysis(effect_size: float, n_samples: int, alpha: float = 0.05) -> Dict[str, float]:
    """
    Run power analysis to calculate achieved power.
    Returns achieved power as a descriptive metric.
    """
    from statsmodels.stats.power import TTestPower, TTestIndPower, TTestPower
    # Note: For paired t-test, we can approximate with TTestPower using effect size d
    # However, statsmodels TTestPower is for one-sample or two-sample independent.
    # For paired, we treat it as one-sample on differences.
    power_analysis = TTestPower()
    
    try:
        # power = 1 - beta
        # effect_size = d, nobs = n, alpha = alpha, alternative = 'two-sided'
        achieved_power = power_analysis.solve_power(effect_size=effect_size, nobs1=n_samples, alpha=alpha, alternative='two-sided')
        # solve_power might return None if not found, but usually it works
        if achieved_power is None:
            achieved_power = 0.0
        else:
            achieved_power = float(achieved_power)
    except Exception as e:
        logger.warning(f"Power analysis failed: {e}. Setting power to 0.0.")
        achieved_power = 0.0
    
    logger.info(f"Achieved power: {achieved_power:.4f}")
    return {"achieved_power": achieved_power}

def calculate_confidence_intervals(manual_coverage: List[float], llm_coverage: List[float]) -> Dict[str, Any]:
    """
    Compute 95% confidence intervals for the mean ratio (LLM/Manual) using scipy.stats.t.interval.
    This satisfies the Plan's 'Statistical Interpretation Note'.
    Returns a dictionary with the mean ratio, confidence interval, and sample size.
    """
    if len(manual_coverage) != len(llm_coverage):
        raise ValueError("Manual and LLM coverage lists must have the same length.")
    if len(manual_coverage) == 0:
        raise ValueError("Coverage lists cannot be empty.")
    
    manual_arr = np.array(manual_coverage)
    llm_arr = np.array(llm_coverage)
    
    # Avoid division by zero
    if np.any(manual_arr == 0):
        # Handle zeros: either skip or add a small epsilon. 
        # For ratio, if manual is 0 and llm is > 0, ratio is infinite.
        # If both are 0, ratio is undefined.
        # We will filter out pairs where manual is 0 to avoid infinite ratios.
        valid_mask = manual_arr != 0
        if not np.any(valid_mask):
            raise ValueError("All manual coverage values are zero; cannot compute ratio.")
        manual_arr = manual_arr[valid_mask]
        llm_arr = llm_arr[valid_mask]
    
    ratios = llm_arr / manual_arr
    
    n = len(ratios)
    mean_ratio = np.mean(ratios)
    std_ratio = np.std(ratios, ddof=1)
    
    # 95% Confidence Interval for the mean ratio
    # Using t-distribution
    alpha = 0.05
    confidence_level = 1 - alpha
    dof = n - 1
    t_crit = stats.t.ppf(1 - alpha/2, dof)
    margin_error = t_crit * (std_ratio / np.sqrt(n))
    
    ci_lower = mean_ratio - margin_error
    ci_upper = mean_ratio + margin_error
    
    logger.info(f"Mean ratio: {mean_ratio:.4f}, 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    
    return {
        "mean_ratio": float(mean_ratio),
        "std_ratio": float(std_ratio),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "confidence_level": confidence_level,
        "n_samples": n
    }

def main():
    """
    Main function to run the analysis pipeline.
    This is a placeholder for the full pipeline execution.
    In a real scenario, this would load data, run tests, and generate reports.
    """
    logger.info("Analyzer module loaded successfully.")
    # Example usage (would be replaced by actual data loading in full pipeline)
    # manual = [50.0, 60.0, 70.0]
    # llm = [55.0, 65.0, 75.0]
    # result = calculate_confidence_intervals(manual, llm)
    # print(result)

if __name__ == "__main__":
    main()