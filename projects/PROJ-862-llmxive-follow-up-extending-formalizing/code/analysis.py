import csv
import json
import logging
import math
import os
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
from scipy import stats

from config import load_config, PipelineConfig
from memory_monitor import get_peak_memory_mb, check_memory_limit

logger = logging.getLogger(__name__)

def calculate_pairwise_cosine_similarity(vectors: List[np.ndarray], pair_ids: List[int]) -> List[float]:
    """
    Calculate pairwise cosine similarity for a list of vectors.
    Returns a list of similarity scores corresponding to each pair.
    """
    if not vectors:
        return []
    
    similarities = []
    for i in range(0, len(vectors), 2):
        if i + 1 < len(vectors):
            v1 = vectors[i]
            v2 = vectors[i+1]
            
            # Ensure vectors are numpy arrays
            if not isinstance(v1, np.ndarray):
                v1 = np.array(v1)
            if not isinstance(v2, np.ndarray):
                v2 = np.array(v2)
            
            # Compute cosine similarity
            dot_product = np.dot(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            
            if norm_v1 == 0 or norm_v2 == 0:
                similarity = 0.0
            else:
                similarity = dot_product / (norm_v1 * norm_v2)
            
            similarities.append(similarity)
    
    return similarities

def run_hypothesis_test(baseline_similarities: List[float], perturbed_similarities: List[float]) -> Dict[str, Any]:
    """
    Run statistical hypothesis test to compare baseline and perturbed similarity distributions.
    Selects t-test or Wilcoxon based on normality check.
    """
    if not baseline_similarities or not perturbed_similarities:
        raise ValueError("Both similarity lists must be non-empty")
    
    # Check normality using Shapiro-Wilk test
    _, p_baseline = stats.shapiro(baseline_similarities)
    _, p_perturbed = stats.shapiro(perturbed_similarities)
    
    use_t_test = (p_baseline > 0.05) and (p_perturbed > 0.05)
    
    if use_t_test:
        # Independent samples t-test
        stat, p_value = stats.ttest_ind(baseline_similarities, perturbed_similarities)
        test_type = "t-test"
    else:
        # Wilcoxon rank-sum test (Mann-Whitney U)
        stat, p_value = stats.mannwhitneyu(baseline_similarities, perturbed_similarities, alternative='two-sided')
        test_type = "Wilcoxon"
    
    # Calculate effect size (Cohen's d for t-test, rank-biserial for Wilcoxon)
    mean_diff = np.mean(perturbed_similarities) - np.mean(baseline_similarities)
    
    # 95% Confidence Interval for mean difference
    combined = np.array(baseline_similarities + perturbed_similarities)
    n1, n2 = len(baseline_similarities), len(perturbed_similarities)
    pooled_std = np.sqrt(((n1 - 1) * np.var(baseline_similarities, ddof=1) + 
                         (n2 - 1) * np.var(perturbed_similarities, ddof=1)) / (n1 + n2 - 2))
    
    if pooled_std > 0:
        se = pooled_std * np.sqrt(1/n1 + 1/n2)
        ci_lower = mean_diff - 1.96 * se
        ci_upper = mean_diff + 1.96 * se
    else:
        ci_lower = ci_upper = mean_diff
    
    return {
        "test_type": test_type,
        "p_value": float(p_value),
        "mean_diff": float(mean_diff),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "statistic": float(stat)
    }

def generate_per_task_trade_off(task_results: Dict[str, Dict]) -> List[Dict]:
    """
    Generate trade-off curves for each task type.
    Consumes validity log data to map perturbation magnitude vs pass-rate.
    """
    trade_offs = []
    
    for task_type, results in task_results.items():
        if "validity_log" not in results:
            continue
        
        validity_log = results["validity_log"]
        
        for entry in validity_log:
            trade_offs.append({
                "task_type": task_type,
                "sigma": entry.get("sigma"),
                "pass_rate": entry.get("pass_rate"),
                "collapse_point": entry.get("collapse_point", False)
            })
    
    return trade_offs

def aggregate_global_results(task_results: Dict[str, Dict]) -> Dict[str, Any]:
    """
    Aggregate per-task results into global distribution and sensitivity report.
    """
    global_trade_offs = []
    collapse_points = []
    
    for task_type, results in task_results.items():
        if "validity_log" in results:
            for entry in results["validity_log"]:
                global_trade_offs.append({
                    "task_type": task_type,
                    "sigma": entry.get("sigma"),
                    "pass_rate": entry.get("pass_rate"),
                    "collapse_point": entry.get("collapse_point", False)
                })
                
                if entry.get("collapse_point", False):
                    collapse_points.append({
                        "task_type": task_type,
                        "sigma": entry.get("sigma")
                    })
    
    return {
        "global_trade_off_curve": global_trade_offs,
        "validity_collapse_distribution": collapse_points
    }

def generate_sensitivity_report(task_results: Dict[str, Dict], statistical_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate comprehensive sensitivity report combining statistical results and trade-off curves.
    """
    report = {
        "statistical_analysis": statistical_results,
        "trade_off_curves": generate_per_task_trade_off(task_results),
        "global_distribution": aggregate_global_results(task_results)
    }
    
    return report

def apply_family_wise_error_correction(p_values: List[float], method: str = "holm") -> List[float]:
    """
    Apply Bonferroni or Holm family-wise error correction to p-values.
    """
    if not p_values:
        return []
    
    n = len(p_values)
    
    if method == "bonferroni":
        corrected = [min(p * n, 1.0) for p in p_values]
    elif method == "holm":
        # Holm-Bonferroni method
        sorted_indices = np.argsort(p_values)
        sorted_p = [p_values[i] for i in sorted_indices]
        corrected_sorted = []
        
        for i, p in enumerate(sorted_p):
            corrected_p = min(p * (n - i), 1.0)
            corrected_sorted.append(corrected_p)
        
        # Reorder back to original indices
        corrected = [0.0] * n
        for idx, corr_val in zip(sorted_indices, corrected_sorted):
            corrected[idx] = corr_val
    else:
        raise ValueError(f"Unknown correction method: {method}")
    
    return corrected

def check_significant_separability_increase(p_value: float, alpha: float = 0.05) -> Tuple[bool, str]:
    """
    Check if there is a significant separability increase based on corrected p-value.
    
    Args:
        p_value: The corrected p-value from statistical testing
        alpha: Significance threshold (default 0.05)
    
    Returns:
        Tuple of (is_significant, flag_message)
    """
    is_significant = p_value < alpha
    
    if is_significant:
        flag_message = "Significant Separability Increase Detected"
    else:
        flag_message = "No Significant Separability Increase"
    
    return is_significant, flag_message

def load_filtered_vectors(config: PipelineConfig) -> Tuple[Dict[str, List[np.ndarray]], Dict[str, List[np.ndarray]]]:
    """
    Load filtered baseline and perturbed vectors from CSV files.
    Returns dictionaries keyed by task_type.
    """
    baseline_vectors = {}
    perturbed_vectors = {}
    
    # Load baseline vectors
    baseline_path = config.output_paths.baseline_vectors_path
    if os.path.exists(baseline_path):
        with open(baseline_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                task_type = row['task_type']
                pair_id = int(row['pair_id'])
                vector_base64 = row['vector_base64']
                
                # Decode base64 vector
                import base64
                vector_bytes = base64.b64decode(vector_base64)
                vector = np.frombuffer(vector_bytes, dtype=np.float32)
                
                if task_type not in baseline_vectors:
                    baseline_vectors[task_type] = []
                baseline_vectors[task_type].append(vector)
    
    # Load perturbed vectors
    perturbed_path = config.output_paths.perturbed_vectors_path
    if os.path.exists(perturbed_path):
        with open(perturbed_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                task_type = row['task_type']
                vector_base64 = row['vector_base64']
                
                # Decode base64 vector
                import base64
                vector_bytes = base64.b64decode(vector_base64)
                vector = np.frombuffer(vector_bytes, dtype=np.float32)
                
                if task_type not in perturbed_vectors:
                    perturbed_vectors[task_type] = []
                perturbed_vectors[task_type].append(vector)
    
    return baseline_vectors, perturbed_vectors

def run_analysis_orchestration(config: PipelineConfig) -> Dict[str, Any]:
    """
    Main orchestration function for statistical analysis.
    Performs hypothesis testing, error correction, and generates final report.
    """
    logger.info("Starting statistical analysis orchestration")
    
    # Load vectors
    baseline_vectors, perturbed_vectors = load_filtered_vectors(config)
    
    # Memory check
    peak_mem = get_peak_memory_mb()
    if not check_memory_limit(peak_mem, config.memory_config.max_rss_gb * 1024):
        raise MemoryError(f"Peak memory {peak_mem}MB exceeds limit {config.memory_config.max_rss_gb * 1024}MB")
    
    task_results = {}
    all_p_values = []
    statistical_results = {}
    
    # Process each task type
    for task_type in baseline_vectors.keys():
        logger.info(f"Processing task type: {task_type}")
        
        if task_type not in perturbed_vectors:
            logger.warning(f"No perturbed vectors found for {task_type}, skipping")
            continue
        
        # Calculate pairwise similarities
        baseline_sims = calculate_pairwise_cosine_similarity(
            baseline_vectors[task_type], 
            list(range(len(baseline_vectors[task_type])))
        )
        perturbed_sims = calculate_pairwise_cosine_similarity(
            perturbed_vectors[task_type], 
            list(range(len(perturbed_vectors[task_type])))
        )
        
        # Run hypothesis test
        test_result = run_hypothesis_test(baseline_sims, perturbed_sims)
        all_p_values.append(test_result["p_value"])
        
        # Load validity log for this task
        validity_log_path = config.output_paths.validity_log_path
        validity_log = []
        if os.path.exists(validity_log_path):
            with open(validity_log_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['task_type'] == task_type:
                        validity_log.append({
                            "sigma": float(row['sigma']),
                            "pass_rate": float(row['pass_rate']),
                            "collapse_point": row['collapse_point'].lower() == 'true'
                        })
        
        task_results[task_type] = {
            "test_result": test_result,
            "validity_log": validity_log,
            "baseline_similarities": baseline_sims,
            "perturbed_similarities": perturbed_sims
        }
        
        statistical_results[task_type] = test_result
    
    # Apply family-wise error correction
    if all_p_values:
        corrected_p_values = apply_family_wise_error_correction(all_p_values, method="holm")
        
        # Update statistical results with corrected p-values
        for i, task_type in enumerate(task_results.keys()):
            statistical_results[task_type]["corrected_p_value"] = corrected_p_values[i]
            
            # Check for significant separability increase (Task T032)
            is_significant, flag_message = check_significant_separability_increase(
                corrected_p_values[i], 
                alpha=0.05
            )
            statistical_results[task_type]["significant_separability"] = is_significant
            statistical_results[task_type]["flag_message"] = flag_message
    else:
        logger.warning("No p-values to correct")
    
    # Generate sensitivity report
    sensitivity_report = generate_sensitivity_report(task_results, statistical_results)
    
    # Save results
    output_path = config.output_paths.statistical_results_path
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(sensitivity_report, f, indent=2)
    
    logger.info(f"Statistical results saved to {output_path}")
    
    return sensitivity_report

def main():
    """Main entry point for analysis script."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        config = load_config()
        result = run_analysis_orchestration(config)
        print("Analysis completed successfully")
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()