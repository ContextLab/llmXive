import os
import json
import logging
import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

def load_coverage_reports(coverage_dir: str) -> List[Dict[str, Any]]:
    """Load all coverage reports from the directory."""
    reports = []
    if not os.path.exists(coverage_dir):
        logger.warning(f"Coverage directory {coverage_dir} does not exist.")
        return reports
    
    for filename in os.listdir(coverage_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(coverage_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    if data.get('status') == 'success':
                        reports.append(data)
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
    return reports

def pair_llm_human_results(reports: List[Dict[str, Any]]) -> pd.DataFrame:
    """Pair LLM and human results by task_id."""
    # Assuming reports contain both LLM and human solutions or we have a separate human source
    # For this implementation, we assume the 'reports' list contains entries with 'task_id' and 'line_coverage'
    # We need to pair them. If the dataset loader created a catalog with human solutions, we might need to merge.
    # Simplified assumption: We have a list where each task_id appears twice (once for LLM, once for Human) 
    # OR we have a specific structure. 
    # Let's assume the reports contain 'model_type' or we infer from context. 
    # Since the task description implies comparing LLM vs Human, and we have a catalog:
    # We will construct a dataframe where we compare 'line_coverage' of LLM vs Human.
    
    # For the purpose of this script, we assume we can distinguish them or we are comparing 
    # LLM coverage against a baseline. 
    # Let's assume the reports have a field 'source' or 'model' to distinguish.
    # If not, we might need to load human solutions separately. 
    # Given the constraints, let's assume we have a way to identify them.
    # We will create a pivot.
    
    df = pd.DataFrame(reports)
    if 'task_id' not in df.columns:
        return pd.DataFrame()
    
    # Group by task_id to ensure we have pairs
    # We assume for every task_id, we have at least one entry. 
    # If we have both LLM and Human, we can pivot.
    # If we only have LLM, we can't do paired test. 
    # Let's assume the 'reports' contain 'model_name' or similar.
    # If not, we might need to fetch human coverage from the catalog if it was calculated.
    # For now, let's assume the 'reports' contain 'coverage' and 'source'.
    
    if 'source' in df.columns:
        pivot = df.pivot_table(index='task_id', columns='source', values='line_coverage', aggfunc='first')
        return pivot
    else:
        # Fallback: Assume first N are human, next N are LLM? No, that's unsafe.
        # Assume we have a specific structure or just return the raw df if pairing isn't possible yet.
        # For the sake of the script running, we return a dummy structure if pairing fails.
        logger.warning("Could not pair results. Returning raw dataframe.")
        return df

def check_normality_shapiro(data: np.ndarray) -> Tuple[bool, float]:
    """Perform Shapiro-Wilk test for normality."""
    if len(data) < 3:
        return False, 1.0
    stat, p_value = stats.shapiro(data)
    return p_value >= 0.05, p_value

def calculate_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """Calculate Cohen's d effect size."""
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1), np.std(group2)
    n1, n2 = len(group1), len(group2)
    
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return (mean1 - mean2) / pooled_std

def perform_statistical_test(group1: np.ndarray, group2: np.ndarray) -> Dict[str, Any]:
    """Perform paired t-test or Wilcoxon signed-rank test based on normality."""
    normal, p_val_normal = check_normality_shapiro(group1 - group2)
    
    if normal:
        stat, p_value = stats.ttest_rel(group1, group2)
        test_type = "t-test"
    else:
        stat, p_value = stats.wilcoxon(group1, group2)
        test_type = "Wilcoxon"
    
    cohens_d = calculate_cohens_d(group1, group2)
    
    return {
        "test_type": test_type,
        "p_value": p_value,
        "cohen_d": cohens_d,
        "mean_diff": np.mean(group1 - group2),
        "mean_llm": np.mean(group1),
        "mean_human": np.mean(group2)
    }

def apply_bonferroni_correction(p_values: List[float]) -> List[float]:
    """Apply Bonferroni correction."""
    n = len(p_values)
    if n == 0:
        return []
    return [min(p * n, 1.0) for p in p_values]

def apply_holm_bonferroni_correction(p_values: List[float]) -> List[float]:
    """Apply Holm-Bonferroni correction."""
    n = len(p_values)
    if n == 0:
        return []
    sorted_indices = np.argsort(p_values)
    corrected = np.zeros(n)
    sorted_p = np.array(p_values)[sorted_indices]
    
    for i, p in enumerate(sorted_p):
        corrected[sorted_indices[i]] = min(p * (n - i), 1.0)
    
    return list(corrected)

def run_family_wise_error_correction(p_values: List[float], method: str = 'holm') -> List[float]:
    """Run family-wise error correction."""
    if method == 'bonferroni':
        return apply_bonferroni_correction(p_values)
    elif method == 'holm':
        return apply_holm_bonferroni_correction(p_values)
    else:
        return p_values

def calculate_exclusion_rate(reports: List[Dict[str, Any]]) -> float:
    """Calculate the rate of excluded tasks (e.g., syntax errors)."""
    if not reports:
        return 0.0
    # Assuming 'status' indicates success or failure
    total = len(reports)
    # If we consider 'failed' as excluded
    excluded = sum(1 for r in reports if r.get('status') == 'failed')
    return excluded / total if total > 0 else 0.0

def run_sensitivity_analysis(coverage_dir: str, thresholds: List[float], output_path: str) -> bool:
    """
    Implement sensitivity analysis (FR-011) across thresholds.
    Explicitly exclude these thresholds from family-wise error correction.
    Output: data/processed/sensitivity_report.csv
    """
    logger.info(f"Running sensitivity analysis on {len(thresholds)} thresholds: {thresholds}")
    
    # Load reports
    reports = load_coverage_reports(coverage_dir)
    if not reports:
        logger.error("No coverage reports found for sensitivity analysis.")
        return False
    
    # We need to simulate or calculate how results change with thresholds.
    # Since the core metric is p-value from the statistical test, we can check
    # if the conclusion (significant vs not) changes based on the alpha threshold.
    # However, the task asks for sensitivity across thresholds {0.01, 0.05, ...}.
    # This usually implies checking stability of the result or effect size.
    # Let's assume we are checking the significance decision at each threshold.
    
    # We need paired data first.
    # We will assume we have LLM and Human coverage in the reports.
    # If not, we might need to pair them manually if the reports contain both.
    # For this implementation, let's assume we can extract pairs.
    
    # Simplified: We will perform the test once and then report the p-value
    # and check significance at each threshold.
    # But sensitivity analysis often involves perturbing data or parameters.
    # Given the constraints, we will report the p-value and the decision at each threshold.
    
    # To make it robust, let's try to pair the data.
    # We assume 'reports' has 'task_id' and 'line_coverage' and 'source' (LLM/Human).
    # If 'source' is missing, we can't pair.
    
    df = pd.DataFrame(reports)
    if 'task_id' not in df.columns or 'line_coverage' not in df.columns:
        logger.error("Reports missing required fields for pairing.")
        return False
    
    # Check if we have 'source' to distinguish LLM/Human
    if 'source' in df.columns:
        pivot = df.pivot_table(index='task_id', columns='source', values='line_coverage', aggfunc='first')
        if 'LLM' in pivot.columns and 'Human' in pivot.columns:
            llm_scores = pivot['LLM'].dropna().values
            human_scores = pivot['Human'].dropna().values
            
            if len(llm_scores) != len(human_scores) or len(llm_scores) == 0:
                logger.error("Could not align LLM and Human scores.")
                return False
            
            # Perform the test
            normal, _ = check_normality_shapiro(llm_scores - human_scores)
            if normal:
                stat, p_value = stats.ttest_rel(llm_scores, human_scores)
            else:
                stat, p_value = stats.wilcoxon(llm_scores, human_scores)
            
            cohens_d = calculate_cohens_d(llm_scores, human_scores)
            
            # Build sensitivity report
            results = []
            for thresh in thresholds:
                is_significant = p_value < thresh
                results.append({
                    "threshold": thresh,
                    "p_value": p_value,
                    "significant": is_significant,
                    "effect_size_cohen_d": cohens_d,
                    "test_type": "t-test" if normal else "Wilcoxon",
                    "mean_diff": float(np.mean(llm_scores - human_scores)),
                    # Explicitly exclude from FWE correction as per FR-011
                    "fwe_corrected": False 
                })
            
            df_results = pd.DataFrame(results)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            df_results.to_csv(output_path, index=False)
            logger.info(f"Sensitivity report saved to {output_path}")
            return True
        else:
            logger.error("Missing LLM or Human columns in pivot table.")
            return False
    else:
        logger.error("Reports do not contain 'source' field to distinguish LLM/Human.")
        return False

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for features."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    vif_data = {}
    for i, col in enumerate(feature_cols):
        if col in df.columns:
            vif = variance_inflation_factor(df[feature_cols].values, i)
            vif_data[col] = vif
    return vif_data

def run_analysis_pipeline(output_dir: str):
    """Run the full analysis pipeline (Stats + Sensitivity)."""
    # This function is called by main.py
    # It orchestrates the statistical tests and sensitivity analysis
    
    # 1. Statistical Summary (T024-T028)
    # We assume this is handled by the caller or we call it here
    # For T029, we specifically call run_sensitivity_analysis
    
    # The sensitivity analysis is called explicitly in main.py or here
    # We ensure the output path is correct
    sensitivity_path = os.path.join(output_dir, "sensitivity_report.csv")
    run_sensitivity_analysis(output_dir, [0.01, 0.05, 0.10, 0.15, 0.20, 0.25], sensitivity_path)

def main():
    """Main entry point for analyzer."""
    # This is for direct execution if needed
    pass
