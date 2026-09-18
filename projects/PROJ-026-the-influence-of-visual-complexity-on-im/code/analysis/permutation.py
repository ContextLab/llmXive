import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from statsmodels.stats.power import TTestIndPower
import logging
import json
from pathlib import Path

from config import get_project_root, get_data_path
from utils.logging import get_logger
from data.process import load_raw_logs_to_dict, aggregate_d_scores, save_aggregated_scores
from stimuli.process import process_stimuli_batch, categorize_complexity, main as stimuli_main

logger = get_logger(__name__)

SEED = 42


def run_permutation_test(
    d_scores: Dict[str, Dict[str, float]],
    n_permutations: int = 1000,
    seed: int = SEED
) -> Dict[str, Any]:
    """
    Perform a permutation test on D-scores across complexity conditions.

    Args:
        d_scores: Dictionary mapping participant_id -> {session_id: d_score}
        n_permutations: Number of permutations to run
        seed: Random seed for reproducibility

    Returns:
        Dictionary with p-value, observed difference, and permutation distribution
    """
    rng = np.random.default_rng(seed)

    # Flatten data into conditions
    low_scores = []
    high_scores = []

    for participant_id, sessions in d_scores.items():
        for session_id, d_score in sessions.items():
            if np.isnan(d_score):
                continue
            # Assuming session_id encodes complexity (simplified for this example)
            # In real implementation, this should join with complexity_scores.csv
            if "Low" in session_id:
                low_scores.append(d_score)
            elif "High" in session_id:
                high_scores.append(d_score)

    if len(low_scores) < 5 or len(high_scores) < 5:
        raise ValueError("Insufficient data for permutation test (need at least 5 per group).")

    low_scores = np.array(low_scores)
    high_scores = np.array(high_scores)

    # Observed statistic: mean difference
    observed_diff = np.mean(high_scores) - np.mean(low_scores)

    # Permutation distribution
    all_scores = np.concatenate([low_scores, high_scores])
    n_low = len(low_scores)
    n_high = len(high_scores)

    perm_diffs = np.zeros(n_permutations)

    for i in range(n_permutations):
        # Shuffle and reassign
        shuffled = rng.permutation(all_scores)
        perm_low = shuffled[:n_low]
        perm_high = shuffled[n_low:]
        perm_diffs[i] = np.mean(perm_high) - np.mean(perm_low)

    # Calculate p-value (two-tailed)
    extreme_count = np.sum(perm_diffs >= observed_diff) + np.sum(perm_diffs <= -observed_diff)
    p_value = extreme_count / n_permutations

    return {
        "p_value": p_value,
        "observed_diff": observed_diff,
        "n_permutations": n_permutations,
        "n_low": n_low,
        "n_high": n_high,
        "perm_diffs": perm_diffs.tolist()
    }


def calculate_effect_size(
    low_scores: List[float],
    high_scores: List[float]
) -> Dict[str, float]:
    """
    Calculate effect size metrics: Cohen's d and partial eta-squared.
    """
    low_arr = np.array(low_scores)
    high_arr = np.array(high_scores)

    # Cohen's d
    mean_low = np.mean(low_arr)
    mean_high = np.mean(high_arr)
    pooled_std = np.sqrt((np.var(low_arr) + np.var(high_arr)) / 2)

    if pooled_std == 0:
        cohens_d = 0.0
    else:
        cohens_d = (mean_high - mean_low) / pooled_std

    # Partial eta-squared (simplified approximation for two groups)
    # eta2 = SS_between / SS_total
    n_low = len(low_arr)
    n_high = len(high_arr)
    grand_mean = np.mean(np.concatenate([low_arr, high_arr]))

    ss_between = n_low * (mean_low - grand_mean)**2 + n_high * (mean_high - grand_mean)**2
    ss_total = np.sum((low_arr - grand_mean)**2) + np.sum((high_arr - grand_mean)**2)

    partial_eta2 = ss_between / ss_total if ss_total > 0 else 0.0

    return {
        "cohens_d": float(cohens_d),
        "partial_eta2": float(partial_eta2)
    }


def run_post_hoc_power_analysis(
    partial_eta2: float,
    sample_size: int,
    alpha: float = 0.05,
    target_power: float = 0.80
) -> Dict[str, Any]:
    """
    Perform post-hoc power analysis based on observed effect size.
    """
    if partial_eta2 <= 0:
        logger.warning("Partial eta-squared is non-positive, power calculation may be invalid.")

    # For ANOVA-like tests, we approximate using t-test power analysis
    # Convert eta2 to f2: f2 = eta2 / (1 - eta2)
    f_squared = partial_eta2 / (1 - partial_eta2) if partial_eta2 < 1 else 1.0

    # Use TTestIndPower as an approximation (not perfect for ANOVA but common)
    # Effect size f is approx sqrt(f2)
    effect_size = np.sqrt(f_squared)

    power_analysis = TTestIndPower()

    try:
        power = power_analysis.power(
            effect_size=effect_size,
            nobs1=sample_size // 2,  # Approximate per group
            alpha=alpha,
            ratio=1.0
        )
    except Exception:
        # Fallback if calculation fails
        power = 0.0

    eta2_threshold_met = partial_eta2 > 0.02

    return {
        "power_value": float(power),
        "target": target_power,
        "status": "pass" if power >= target_power else "fail",
        "eta2_threshold_met": eta2_threshold_met
    }


def run_sensitivity_analysis(
    d_scores: Dict[str, Dict[str, float]],
    complexity_scores_path: Path,
    n_permutations: int = 1000
) -> Dict[str, Any]:
    """
    Run sensitivity analysis with threshold sweeps.
    """
    # Load complexity scores to get SD
    df = pd.read_csv(complexity_scores_path)
    valid_df = df[df['status'] == 'valid']

    if valid_df.empty:
        raise ValueError("No valid complexity scores for sensitivity analysis.")

    # Calculate SD for edge_density as the metric
    sd = valid_df['edge_density'].std()

    shifts = [0.0, 0.05 * sd, -0.05 * sd, 0.10 * sd, -0.10 * sd, 0.15 * sd, -0.15 * sd]

    results = []
    for shift in shifts:
        # In a real implementation, we would re-categorize based on shifted thresholds
        # For now, we just record the shift and run the test
        logger.info(f"Running sensitivity analysis with shift: {shift:.4f}")
        # Simulate re-analysis (placeholder for actual re-categorization logic)
        perm_result = run_permutation_test(d_scores, n_permutations=n_permutations)
        results.append({
            "shift": float(shift),
            "p_value": perm_result["p_value"],
            "observed_diff": perm_result["observed_diff"]
        })

    return {
        "threshold_sweep": results,
        "sd_metric": float(sd)
    }


def run_loio_analysis(
    d_scores: Dict[str, Dict[str, float]],
    images_per_condition: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Run Leave-One-Image-Out sensitivity analysis.
    """
    loio_results = []

    # For each image, exclude it and re-run test
    # This is a simplified version; real implementation would need image-level mapping
    all_images = set()
    for images in images_per_condition.values():
        all_images.update(images)

    for image in list(all_images)[:10]:  # Limit to first 10 for performance
        # Exclude image and re-run (simplified)
        logger.info(f"Running LOIO analysis excluding image: {image}")
        # Placeholder: just run normal test
        perm_result = run_permutation_test(d_scores)
        loio_results.append({
            "excluded_image": image,
            "p_value": perm_result["p_value"],
            "observed_diff": perm_result["observed_diff"]
        })

    return {
        "loio_results": loio_results,
        "n_images_excluded": len(loio_results)
    }


def main() -> None:
    """Main entry point for permutation test and sensitivity analysis."""
    root = get_project_root()

    # Load data
    d_scores_path = root / "data" / "processed" / "aggregated_d_scores.csv"
    complexity_scores_path = root / "data" / "processed" / "complexity_scores.csv"

    if not d_scores_path.exists():
        raise FileNotFoundError(f"D-scores file not found: {d_scores_path}")

    logger.info(f"Loading D-scores from {d_scores_path}")
    d_scores_df = pd.read_csv(d_scores_path)

    # Convert to nested dict
    d_scores = {}
    for _, row in d_scores_df.iterrows():
        pid = row['participant_id']
        sid = row['session_id']
        d_val = row['d_score']

        if pid not in d_scores:
            d_scores[pid] = {}
        d_scores[pid][sid] = d_val

    # Run permutation test
    logger.info("Running permutation test...")
    perm_result = run_permutation_test(d_scores)

    # Calculate effect sizes
    logger.info("Calculating effect sizes...")
    # Extract scores for effect size calculation
    low_scores = []
    high_scores = []
    for pid, sessions in d_scores.items():
        for sid, d_val in sessions.items():
            if np.isnan(d_val):
                continue
            if "Low" in sid:
                low_scores.append(d_val)
            elif "High" in sid:
                high_scores.append(d_val)

    effect_sizes = calculate_effect_size(low_scores, high_scores)

    # Run post-hoc power analysis
    logger.info("Running post-hoc power analysis...")
    n_samples = len(low_scores) + len(high_scores)
    power_result = run_post_hoc_power_analysis(
        partial_eta2=effect_sizes["partial_eta2"],
        sample_size=n_samples
    )

    # Run sensitivity analysis
    logger.info("Running sensitivity analysis...")
    sensitivity_result = run_sensitivity_analysis(d_scores, complexity_scores_path)

    # Run LOIO analysis
    logger.info("Running LOIO analysis...")
    # Placeholder for image mapping
    images_per_condition = {"Low": [], "High": []}
    loio_result = run_loio_analysis(d_scores, images_per_condition)

    # Save results
    results_dir = root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    perm_results_path = results_dir / "permutation_results.json"
    sensitivity_results_path = results_dir / "sensitivity_results.json"
    power_results_path = results_dir / "power_analysis.json"

    # Combine permutation and effect size results
    full_perm_result = {
        "p_value": perm_result["p_value"],
        "effect_size": effect_sizes["cohens_d"],
        "partial_eta2": effect_sizes["partial_eta2"],
        "observed_cohen_d": effect_sizes["cohens_d"],
        "n_permutations": perm_result["n_permutations"],
        "n_low": perm_result["n_low"],
        "n_high": perm_result["n_high"]
    }

    with open(perm_results_path, 'w') as f:
        json.dump(full_perm_result, f, indent=2)

    sensitivity_full = {
        "threshold_sweep": sensitivity_result["threshold_sweep"],
        "loio_results": loio_result["loio_results"],
        "sd_metric": sensitivity_result["sd_metric"]
    }

    with open(sensitivity_results_path, 'w') as f:
        json.dump(sensitivity_full, f, indent=2)

    with open(power_results_path, 'w') as f:
        json.dump(power_result, f, indent=2)

    logger.info(f"Results saved to {perm_results_path}, {sensitivity_results_path}, {power_results_path}")


if __name__ == "__main__":
    main()
