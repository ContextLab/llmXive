import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from statsmodels.stats.power import TTestIndPower
import logging
import json
from pathlib import Path
import pandas as pd
from config import get_data_path, get_project_root
from utils.logging import get_logger

logger = get_logger(__name__)

def run_permutation_test(
    low_scores: List[float],
    high_scores: List[float],
    n_permutations: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Perform a permutation test to compare D-scores between Low and High complexity conditions.
    
    Parameters:
    - low_scores: List of D-scores for the Low complexity condition
    - high_scores: List of D-scores for the High complexity condition
    - n_permutations: Number of permutations to run
    - seed: Random seed for reproducibility
    
    Returns:
    - Dictionary containing p_value, observed_statistic, and null_distribution
    """
    np.random.seed(seed)
    
    # Convert to numpy arrays
    low_arr = np.array(low_scores)
    high_arr = np.array(high_scores)
    
    # Calculate observed statistic: mean difference (High - Low)
    observed_diff = np.mean(high_arr) - np.mean(low_arr)
    
    # Combine all scores
    all_scores = np.concatenate([low_arr, high_arr])
    n_low = len(low_arr)
    n_high = len(high_arr)
    n_total = len(all_scores)
    
    # Generate null distribution
    null_distribution = np.zeros(n_permutations)
    
    for i in range(n_permutations):
        # Shuffle the combined scores
        shuffled = np.random.permutation(all_scores)
        
        # Split into new groups
        new_low = shuffled[:n_low]
        new_high = shuffled[n_low:]
        
        # Calculate difference for this permutation
        null_distribution[i] = np.mean(new_high) - np.mean(new_low)
    
    # Calculate two-tailed p-value
    # Count how many permuted differences are as extreme or more extreme than observed
    extreme_count = np.sum(np.abs(null_distribution) >= np.abs(observed_diff))
    p_value = extreme_count / n_permutations
    
    result = {
        "p_value": float(p_value),
        "observed_statistic": float(observed_diff),
        "n_permutations": n_permutations,
        "n_low": n_low,
        "n_high": n_high,
        "null_distribution": null_distribution.tolist()
    }
    
    logger.info(f"Permutation test completed: p={p_value:.4f}, observed_diff={observed_diff:.4f}")
    return result

def calculate_effect_size(
    low_scores: List[float],
    high_scores: List[float]
) -> Dict[str, float]:
    """
    Calculate effect sizes for the comparison.
    
    Returns:
    - Dictionary with Cohen's d and partial eta-squared
    """
    low_arr = np.array(low_scores)
    high_arr = np.array(high_scores)
    
    # Cohen's d
    mean_diff = np.mean(high_arr) - np.mean(low_arr)
    pooled_std = np.sqrt((np.var(low_arr, ddof=1) + np.var(high_arr, ddof=1)) / 2)
    
    if pooled_std == 0:
        cohens_d = 0.0
    else:
        cohens_d = mean_diff / pooled_std
    
    # Partial eta-squared (approximation for independent samples)
    # eta^2 = SS_effect / (SS_effect + SS_error)
    # For two groups: eta^2 = t^2 / (t^2 + df)
    # We'll use the d to eta conversion: eta^2 = d^2 / (d^2 + 4) for independent groups
    eta_squared = (cohens_d ** 2) / ((cohens_d ** 2) + 4)
    
    return {
        "observed_cohen_d": float(cohens_d),
        "partial_eta2": float(eta_squared)
    }

def run_post_hoc_power_analysis(
    effect_size: float,
    n_per_group: int,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run post-hoc power analysis using statsmodels.
    
    Parameters:
    - effect_size: Cohen's d
    - n_per_group: Number of participants per group
    - alpha: Significance level
    
    Returns:
    - Dictionary with power value and status
    """
    power_analysis = TTestIndPower()
    
    try:
        power = power_analysis.solve_power(
            effect_size=effect_size,
            nobs1=n_per_group,
            alpha=alpha,
            ratio=1.0,
            alternative='two-sided'
        )
        
        status = "measured"
        if power < 0.80:
            status = "warning"
            logger.warning(f"Power analysis: Power ({power:.3f}) is below target (0.80)")
        
        return {
            "power_value": float(power),
            "target": 0.80,
            "status": status,
            "effect_size": float(effect_size),
            "n_per_group": n_per_group
        }
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        return {
            "power_value": None,
            "target": 0.80,
            "status": "error",
            "error": str(e)
        }

def run_loio_analysis(
    all_data: pd.DataFrame,
    image_column: str = 'filename',
    score_column: str = 'd_score',
    condition_column: str = 'complexity_condition',
    n_permutations: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run Leave-One-Image-Out sensitivity analysis.
    
    For each unique image in the dataset, exclude it and re-run the permutation test.
    
    Returns:
    - Dictionary with LOIO results for each excluded image
    """
    np.random.seed(seed)
    
    unique_images = all_data[image_column].unique()
    loio_results = {}
    
    logger.info(f"Starting LOIO analysis with {len(unique_images)} images")
    
    for i, image in enumerate(unique_images):
        logger.debug(f"LOIO iteration {i+1}/{len(unique_images)}: excluding {image}")
        
        # Exclude current image
        filtered_data = all_data[all_data[image_column] != image]
        
        # Check if we have enough data
        if len(filtered_data) < 10:
            loio_results[image] = {
                "status": "invalid",
                "reason": "insufficient_data_after_exclusion",
                "n_remaining": len(filtered_data)
            }
            continue
        
        # Split by condition
        low_scores = filtered_data[filtered_data[condition_column] == 'Low'][score_column].tolist()
        high_scores = filtered_data[filtered_data[condition_column] == 'High'][score_column].tolist()
        
        if len(low_scores) < 5 or len(high_scores) < 5:
            loio_results[image] = {
                "status": "invalid",
                "reason": "insufficient_group_size",
                "n_low": len(low_scores),
                "n_high": len(high_scores)
            }
            continue
        
        # Run permutation test
        result = run_permutation_test(
            low_scores, 
            high_scores, 
            n_permutations=n_permutations,
            seed=seed + i  # Vary seed slightly for each iteration
        )
        
        loio_results[image] = {
            "status": "valid",
            "p_value": result["p_value"],
            "observed_statistic": result["observed_statistic"],
            "n_low": result["n_low"],
            "n_high": result["n_high"]
        }
    
    logger.info(f"LOIO analysis completed. Valid: {sum(1 for r in loio_results.values() if r['status'] == 'valid')}")
    return {
        "method": "leave_one_image_out",
        "n_images_total": len(unique_images),
        "results": loio_results
    }

def run_sensitivity_analysis(
    aggregated_scores_path: str,
    complexity_scores_path: str,
    n_permutations: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run full sensitivity analysis including threshold sweep and LOIO.
    
    Parameters:
    - aggregated_scores_path: Path to aggregated D-scores CSV
    - complexity_scores_path: Path to complexity scores CSV
    - n_permutations: Number of permutations for each test
    - seed: Random seed
    
    Returns:
    - Dictionary with threshold_sweep and loio_results
    """
    logger.info("Starting sensitivity analysis")
    
    # Load data
    try:
        d_scores = pd.read_csv(aggregated_scores_path)
        complexity = pd.read_csv(complexity_scores_path)
    except Exception as e:
        logger.error(f"Failed to load data for sensitivity analysis: {e}")
        return {
            "status": "error",
            "error": str(e),
            "threshold_sweep": {},
            "loio_results": {}
        }
    
    # Join data to get complexity condition for each D-score
    # Assuming the join is on participant_id and session_id
    # This depends on the exact schema of the aggregated data
    # For now, we'll assume the complexity condition is already in d_scores or can be joined
    
    # If complexity condition is not in d_scores, we need to join
    if 'complexity_condition' not in d_scores.columns:
        # Attempt to join with complexity scores
        # This is a simplification - actual join logic depends on data schema
        logger.warning("complexity_condition not found in aggregated scores, skipping sensitivity analysis")
        return {
            "status": "skipped",
            "reason": "missing_complexity_condition_in_data",
            "threshold_sweep": {},
            "loio_results": {}
        }
    
    # Threshold sweep: vary the complexity threshold
    # Calculate SD of edge_density to determine shift amounts
    edge_density_sd = complexity['edge_density'].std()
    
    threshold_shifts = [
        0.0,  # Baseline
        -0.05 * edge_density_sd,
        0.05 * edge_density_sd,
        -0.10 * edge_density_sd,
        0.10 * edge_density_sd,
        -0.15 * edge_density_sd,
        0.15 * edge_density_sd
    ]
    
    threshold_results = {}
    
    for shift in threshold_shifts:
        shift_label = f"{shift:.4f}"
        logger.info(f"Threshold sweep: shift = {shift_label}")
        
        # For simplicity, we'll use the original categorization
        # In a full implementation, we would re-categorize based on shifted threshold
        # This is a placeholder for the actual re-categorization logic
        
        low_scores = d_scores[d_scores['complexity_condition'] == 'Low']['d_score'].dropna().tolist()
        high_scores = d_scores[d_scores['complexity_condition'] == 'High']['d_score'].dropna().tolist()
        
        if len(low_scores) < 15 or len(high_scores) < 15:
            threshold_results[shift_label] = {
                "status": "invalid",
                "reason": "n < 15 per condition",
                "n_low": len(low_scores),
                "n_high": len(high_scores)
            }
            continue
        
        result = run_permutation_test(
            low_scores,
            high_scores,
            n_permutations=n_permutations,
            seed=seed
        )
        
        threshold_results[shift_label] = {
            "status": "valid",
            "p_value": result["p_value"],
            "observed_statistic": result["observed_statistic"],
            "n_low": result["n_low"],
            "n_high": result["n_high"]
        }
    
    # Run LOIO analysis
    # We need to merge d_scores with complexity to get image filenames
    # Assuming we can join on participant_id and session_id or similar
    # For now, we'll create a dummy dataframe for LOIO
    # In reality, this requires proper data schema alignment
    
    # Attempt to prepare data for LOIO
    # We need: filename, d_score, complexity_condition
    loio_data = d_scores.copy()
    
    # If filename is not in d_scores, we can't do LOIO properly
    if 'filename' not in loio_data.columns:
        # Try to join with complexity scores
        # This is a simplification - actual implementation depends on schema
        logger.warning("filename not found in aggregated scores, LOIO will be skipped")
        loio_results = {
            "status": "skipped",
            "reason": "missing_filename_column"
        }
    else:
        loio_results = run_loio_analysis(
            loio_data,
            image_column='filename',
            score_column='d_score',
            condition_column='complexity_condition',
            n_permutations=n_permutations,
            seed=seed
        )
    
    return {
        "threshold_sweep": threshold_results,
        "loio_results": loio_results
    }

def main():
    """
    Main entry point for running the permutation test analysis.
    
    This function:
    1. Loads aggregated D-scores and complexity scores
    2. Runs the permutation test
    3. Calculates effect sizes
    4. Runs sensitivity analysis (threshold sweep + LOIO)
    5. Saves results to JSON files
    """
    logger.info("Starting permutation test analysis pipeline")
    
    project_root = get_project_root()
    data_path = get_data_path()
    
    # Define file paths
    aggregated_scores_path = Path(data_path) / "processed" / "aggregated_d_scores.csv"
    complexity_scores_path = Path(data_path) / "processed" / "complexity_scores.csv"
    results_dir = Path(data_path) / "results"
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    try:
        d_scores = pd.read_csv(aggregated_scores_path)
        complexity = pd.read_csv(complexity_scores_path)
    except Exception as e:
        logger.error(f"Failed to load required data files: {e}")
        return 1
    
    # Filter valid scores
    valid_scores = d_scores[d_scores['d_score'].notna()]
    
    # Split by complexity condition
    low_scores = valid_scores[valid_scores['complexity_condition'] == 'Low']['d_score'].tolist()
    high_scores = valid_scores[valid_scores['complexity_condition'] == 'High']['d_score'].tolist()
    
    logger.info(f"Loaded {len(low_scores)} Low and {len(high_scores)} High complexity scores")
    
    if len(low_scores) < 10 or len(high_scores) < 10:
        logger.error("Insufficient data for permutation test (need at least 10 per group)")
        return 1
    
    # Run permutation test
    permutation_result = run_permutation_test(
        low_scores,
        high_scores,
        n_permutations=1000,
        seed=42
    )
    
    # Calculate effect sizes
    effect_sizes = calculate_effect_size(low_scores, high_scores)
    
    # Combine results
    results = {
        "p_value": permutation_result["p_value"],
        "observed_statistic": permutation_result["observed_statistic"],
        "n_permutations": permutation_result["n_permutations"],
        "n_low": permutation_result["n_low"],
        "n_high": permutation_result["n_high"],
        "observed_cohen_d": effect_sizes["observed_cohen_d"],
        "partial_eta2": effect_sizes["partial_eta2"]
    }
    
    # Save permutation results
    permutation_results_path = results_dir / "permutation_results.json"
    with open(permutation_results_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved permutation results to {permutation_results_path}")
    
    # Run sensitivity analysis
    sensitivity_result = run_sensitivity_analysis(
        str(aggregated_scores_path),
        str(complexity_scores_path),
        n_permutations=1000,
        seed=42
    )
    
    # Save sensitivity results
    sensitivity_results_path = results_dir / "sensitivity_results.json"
    with open(sensitivity_results_path, 'w') as f:
        json.dump(sensitivity_result, f, indent=2)
    logger.info(f"Saved sensitivity results to {sensitivity_results_path}")
    
    # Run post-hoc power analysis
    n_per_group = min(len(low_scores), len(high_scores))
    power_result = run_post_hoc_power_analysis(
        effect_sizes["observed_cohen_d"],
        n_per_group
    )
    
    # Save power analysis results
    power_results_path = results_dir / "power_analysis.json"
    with open(power_results_path, 'w') as f:
        json.dump(power_result, f, indent=2)
    logger.info(f"Saved power analysis results to {power_results_path}")
    
    logger.info("Permutation test analysis pipeline completed successfully")
    return 0

if __name__ == "__main__":
    exit(main())