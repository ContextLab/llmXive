import os
import json
import logging
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.power import TTestIndPower
from typing import Dict, Any, List, Optional, Tuple

# --- Custom Exceptions ---
class DataNotFoundError(Exception):
    """Raised when required data files are missing or empty."""
    pass

# --- Logging Setup ---
logger = logging.getLogger(__name__)

# --- Helper Functions (from existing API surface) ---
def load_cleaned_dataset(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Loads the final cleaned dataset from the specified path or default location.
    """
    if filepath is None:
        config_path = os.environ.get('PROJECT_ROOT', '.')
        filepath = os.path.join(config_path, 'data', 'processed', 'final_cleaned_dataset.csv')
    
    if not os.path.exists(filepath):
        raise DataNotFoundError(f"Cleaned dataset not found at {filepath}")
    
    df = pd.read_csv(filepath)
    if df.empty:
        raise DataNotFoundError(f"Cleaned dataset at {filepath} is empty.")
    
    logger.info(f"Loaded cleaned dataset with {len(df)} records from {filepath}")
    return df

def welch_t_test(group1: pd.Series, group2: pd.Series) -> Tuple[float, float]:
    """
    Performs Welch's independent samples t-test.
    Returns (statistic, pvalue).
    """
    if len(group1) < 2 or len(group2) < 2:
        logger.warning("One of the groups has fewer than 2 samples. Cannot perform t-test.")
        return np.nan, np.nan
    
    # Check for zero variance
    if group1.var() == 0 and group2.var() == 0:
        logger.warning("Both groups have zero variance.")
        return 0.0, 1.0
    
    t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False)
    return t_stat, p_val

def bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Applies Bonferroni correction to a list of p-values.
    """
    if not p_values:
        return []
    return [p * len(p_values) for p in p_values]

def calculate_cohen_d(group1: pd.Series, group2: pd.Series) -> float:
    """
    Calculates Cohen's d effect size.
    """
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = group1.mean(), group2.mean()
    var1, var2 = group1.var(), group2.var()
    
    if n1 + n2 - 2 == 0:
        return np.nan
        
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
        
    return (mean1 - mean2) / pooled_std

def calculate_effect_size_ci(group1: pd.Series, group2: pd.Series, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculates 95% Confidence Interval for Cohen's d.
    Approximation using non-central t-distribution logic or bootstrap.
    Here using a standard approximation for CI of d.
    """
    d = calculate_cohen_d(group1, group2)
    if np.isnan(d):
        return np.nan, np.nan
    
    n1, n2 = len(group1), len(group2)
    # Approximate standard error of d
    # SE_d = sqrt((n1+n2)/(n1*n2) + d^2/(2*(n1+n2)))
    se_d = np.sqrt((n1 + n2) / (n1 * n2) + (d**2) / (2 * (n1 + n2)))
    
    z = stats.norm.ppf((1 + confidence) / 2)
    ci_low = d - z * se_d
    ci_high = d + z * se_d
    
    return ci_low, ci_high

def calculate_power_and_mdes(effect_size: float, n1: int, n2: int, alpha: float = 0.05) -> Dict[str, float]:
    """
    Calculates statistical power and Minimum Detectable Effect Size (MDES).
    """
    power_analysis = TTestIndPower()
    n_obs = (n1 + n2) / 2
    
    # Calculate Power
    try:
        power = power_analysis.solve_power(effect_size=effect_size, nobs1=n_obs, alpha=alpha, ratio=1.0)
    except Exception:
        power = 0.0
    
    # Calculate MDES for 80% power
    try:
        mdes = power_analysis.solve_power(power=0.80, nobs1=n_obs, alpha=alpha, ratio=1.0)
    except Exception:
        mdes = np.nan
        
    return {"power": float(power), "m_des": float(mdes)}

def run_analysis(df: pd.DataFrame, metric: str = 'perseverative_errors', group_col: str = 'stimulus_type') -> Dict[str, Any]:
    """
    Runs Welch's t-test and effect size calculation for a specific metric.
    """
    if group_col not in df.columns or metric not in df.columns:
        raise DataNotFoundError(f"Columns '{group_col}' or '{metric}' not found in dataframe.")
    
    # Filter non-nulls
    valid_df = df[[group_col, metric]].dropna()
    groups = valid_df[group_col].unique()
    
    if len(groups) < 2:
        logger.warning(f"Less than 2 groups found for {metric}. Skipping.")
        return {}
    
    g1 = valid_df[valid_df[group_col] == groups[0]][metric]
    g2 = valid_df[valid_df[group_col] == groups[1]][metric]
    
    t_stat, p_val = welch_t_test(g1, g2)
    d = calculate_cohen_d(g1, g2)
    ci_low, ci_high = calculate_effect_size_ci(g1, g2)
    power_info = calculate_power_and_mdes(d, len(g1), len(g2))
    
    return {
        "metric": metric,
        "group1": str(groups[0]),
        "group2": str(groups[1]),
        "n1": len(g1),
        "n2": len(g2),
        "t_statistic": float(t_stat) if not np.isnan(t_stat) else None,
        "p_value": float(p_val) if not np.isnan(p_val) else None,
        "cohens_d": float(d) if not np.isnan(d) else None,
        "ci_95_low": float(ci_low) if not np.isnan(ci_low) else None,
        "ci_95_high": float(ci_high) if not np.isnan(ci_high) else None,
        "power": power_info["power"],
        "m_des": power_info["m_des"]
    }

def run_full_analysis(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Runs analysis for all primary metrics.
    """
    metrics = ['perseverative_errors', 'categories_completed']
    results = []
    for metric in metrics:
        try:
            res = run_analysis(df, metric=metric)
            if res:
                results.append(res)
        except Exception as e:
            logger.error(f"Error analyzing {metric}: {e}")
    return results

def save_report(results: List[Dict[str, Any]], output_path: str):
    """
    Saves analysis results to a JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Report saved to {output_path}")

# --- T026: Sensitivity Sweep Implementation ---
def run_sensitivity_sweep(results: List[Dict[str, Any]], thresholds: Optional[List[float]] = None) -> Dict[str, Any]:
    """
    Performs a sensitivity sweep across specified significance thresholds.
    Explicitly tests: 0.01, 0.04, 0.05, 0.06, 0.10 as per T026.
    
    Args:
        results: List of analysis result dictionaries from run_full_analysis.
        thresholds: List of alpha thresholds to test. Defaults to [0.01, 0.04, 0.05, 0.06, 0.10].
    
    Returns:
        Dictionary containing the sensitivity analysis results.
    """
    if thresholds is None:
        thresholds = [0.01, 0.04, 0.05, 0.06, 0.10]
    
    logger.info(f"Running sensitivity sweep for thresholds: {thresholds}")
    
    sweep_results = {
        "thresholds_tested": thresholds,
        "results": []
    }
    
    for result in results:
        metric = result.get("metric")
        p_val = result.get("p_value")
        
        if p_val is None:
            logger.warning(f"P-value missing for {metric}, skipping sensitivity check.")
            continue
        
        metric_sweep = {
            "metric": metric,
            "p_value": p_val,
            "threshold_significance": {}
        }
        
        for alpha in thresholds:
            is_significant = p_val < alpha
            metric_sweep["threshold_significance"][str(alpha)] = {
                "alpha": alpha,
                "is_significant": is_significant
            }
            
            # T029: Borderline Flag Logic (0.04 <= p <= 0.06)
            if 0.04 <= p_val <= 0.06:
                metric_sweep["threshold_significance"][str(alpha)]["is_sensitive_to_threshold"] = True
            else:
                metric_sweep["threshold_significance"][str(alpha)]["is_sensitive_to_threshold"] = False
        
        sweep_results["results"].append(metric_sweep)
    
    return sweep_results

def save_sensitivity_report(sweep_data: Dict[str, Any], output_path: str):
    """
    Saves the sensitivity sweep report to a JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(sweep_data, f, indent=2)
    logger.info(f"Sensitivity report saved to {output_path}")

# --- Main Entry Point for T026 ---
def main():
    """
    Executes the sensitivity sweep (T026) on the cleaned dataset.
    Reads from data/processed/final_cleaned_dataset.csv.
    Writes to data/results/sensitivity_sweep.json (or similar).
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # 1. Load Data
        df = load_cleaned_dataset()
        
        # 2. Run Primary Analysis (T018-T022 logic) to get p-values
        # Note: In a real pipeline, this might load pre-computed results from T022.
        # For this task, we re-run the calculation to ensure fresh p-values.
        analysis_results = run_full_analysis(df)
        
        if not analysis_results:
            raise DataNotFoundError("No analysis results generated from the dataset.")
        
        # 3. Run Sensitivity Sweep (T026)
        sweep_output = run_sensitivity_sweep(analysis_results)
        
        # 4. Save Output
        output_path = os.path.join(os.environ.get('PROJECT_ROOT', '.'), 'data', 'results', 'sensitivity_sweep.json')
        save_sensitivity_report(sweep_output, output_path)
        
        print(f"Sensitivity sweep completed successfully. Output: {output_path}")
        
    except DataNotFoundError as e:
        logger.error(f"Data Error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during sensitivity sweep: {e}")
        raise

if __name__ == "__main__":
    main()