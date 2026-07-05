"""
Robustness validation module for statistical analysis.

This module implements permutation tests, sensitivity analyses,
and ICV-restricted analyses to validate the primary findings.
"""

import os
import logging
import json
import time
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from joblib import Parallel, delayed

from code.config import get_project_root, ensure_directories
from code.config_env import get_permutation_count, get_alpha_thresholds, get_max_workers
from code.analysis.modeling import fit_lmm_for_subfield, calculate_ca3_dg_ratio, run_primary_analysis

# Constants
PERMUTATION_COUNT = 5000
RANDOM_SEED = 42


def load_cleaned_data() -> pd.DataFrame:
    """
    Load the cleaned dataset from disk.

    Returns:
        The cleaned dataframe.
    """
    project_root = get_project_root()
    data_path = project_root / "data" / "processed" / "cleaned_dataset.csv"

    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned dataset not found at {data_path}")

    return pd.read_csv(data_path)


def subset_icv_within_1sd(df: pd.DataFrame) -> pd.DataFrame:
    """
    Subset the data to participants with ICV within 1 SD of the mean.

    Args:
        df: The full dataframe.

    Returns:
        The subsetted dataframe.
    """
    if "ICV" not in df.columns:
        logging.warning("ICV column not found, returning original data")
        return df

    mean_icv = df["ICV"].mean()
    std_icv = df["ICV"].std()

    lower_bound = mean_icv - std_icv
    upper_bound = mean_icv + std_icv

    subset = df[(df["ICV"] >= lower_bound) & (df["ICV"] <= upper_bound)]

    logging.info(f"Subset size: {len(subset)} (original: {len(df)})")

    return subset


def calculate_effect_size_change(original_beta: float, restricted_beta: float) -> float:
    """
    Calculate the percentage change in effect size.

    Args:
        original_beta: The beta coefficient from the full sample.
        restricted_beta: The beta coefficient from the restricted sample.

    Returns:
        The percentage change.
    """
    if original_beta == 0:
        return float('inf') if restricted_beta != 0 else 0.0

    return ((restricted_beta - original_beta) / original_beta) * 100


def run_permutation_test(
    df: pd.DataFrame,
    formula: str,
    subfield: str,
    n_permutations: int = PERMUTATION_COUNT,
    random_seed: int = RANDOM_SEED
) -> float:
    """
    Run a permutation test to assess the significance of the ACE effect.

    Args:
        df: The dataframe.
        formula: The model formula.
        subfield: The subfield column name.
        n_permutations: Number of permutations.
        random_seed: Random seed.

    Returns:
        The empirical p-value.
    """
    np.random.seed(random_seed)

    # Fit original model
    try:
        original_model = fit_lmm_for_subfield(df, subfield, formula)
        original_beta = original_model.beta_ace
        original_p = original_model.p_value
    except Exception:
        logging.error("Failed to fit original model")
        return 1.0

    if np.isnan(original_beta):
        return 1.0

    count_extreme = 0

    for i in range(n_permutations):
        # Permute ACE scores
        df_perm = df.copy()
        df_perm["ACE_score"] = np.random.permutation(df_perm["ACE_score"])

        try:
            perm_model = fit_lmm_for_subfield(df_perm, subfield, formula)
            perm_beta = perm_model.beta_ace

            if abs(perm_beta) >= abs(original_beta):
                count_extreme += 1
        except Exception:
            continue

    return count_extreme / n_permutations


def run_permutation_test_parallel(
    df: pd.DataFrame,
    formula: str,
    subfield: str,
    n_permutations: int = PERMUTATION_COUNT,
    n_jobs: int = 2
) -> float:
    """
    Run permutation test in parallel.

    Args:
        df: The dataframe.
        formula: The model formula.
        subfield: The subfield column name.
        n_permutations: Total number of permutations.
        n_jobs: Number of parallel workers.

    Returns:
        The empirical p-value.
    """
    # Split permutations across workers
    batch_size = n_permutations // n_jobs
    remaining = n_permutations % n_jobs

    def run_batch(batch_id: int, seed: int) -> Tuple[int, int]:
        """Run a batch of permutations and return (count_extreme, total)"""
        np.random.seed(seed)
        count = 0
        total = 0

        # Original model fit (could be cached, but doing it per batch for simplicity)
        try:
            original_model = fit_lmm_for_subfield(df, subfield, formula)
            original_beta = original_model.beta_ace
        except Exception:
            return 0, 0

        if np.isnan(original_beta):
            return 0, 0

        start = batch_id * batch_size
        end = start + batch_size + (1 if batch_id < remaining else 0)

        for i in range(start, end):
            df_perm = df.copy()
            df_perm["ACE_score"] = np.random.permutation(df_perm["ACE_score"])

            try:
                perm_model = fit_lmm_for_subfield(df_perm, subfield, formula)
                perm_beta = perm_model.beta_ace

                if abs(perm_beta) >= abs(original_beta):
                    count += 1
                total += 1
            except Exception:
                continue

        return count, total

    # Run in parallel
    seeds = np.random.randint(0, 2**31, n_jobs)
    results = Parallel(n_jobs=n_jobs)(
        delayed(run_batch)(i, seeds[i]) for i in range(n_jobs)
    )

    total_extreme = sum(r[0] for r in results)
    total_perm = sum(r[1] for r in results)

    return total_extreme / total_perm if total_perm > 0 else 1.0


def run_icv_restricted_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run the primary analysis on the ICV-restricted subset.

    Args:
        df: The full dataframe.

    Returns:
        A dictionary containing the restricted results and effect size changes.
    """
    subset_df = subset_icv_within_1sd(df)

    if len(subset_df) < 10:
        logging.warning("ICV subset too small, returning empty results")
        return {}

    # Run primary analysis on subset
    restricted_results = run_primary_analysis(subset_df)

    # Get original results
    original_results = run_primary_analysis(df)

    effect_changes = {}
    for subfield, restricted_model in restricted_results.items():
        if subfield in original_results:
            original_beta = original_results[subfield].beta_ace
            restricted_beta = restricted_model.beta_ace
            change = calculate_effect_size_change(original_beta, restricted_beta)
            effect_changes[subfield] = change

    return {
        "n_obs": len(subset_df),
        "results": {k: v.to_dict() for k, v in restricted_results.items()},
        "effect_size_changes": effect_changes
    }


def run_sensitivity_analysis(
    df: pd.DataFrame,
    alpha_thresholds: List[float] = None
) -> pd.DataFrame:
    """
    Run sensitivity analysis across different alpha thresholds.

    Args:
        df: The dataframe.
        alpha_thresholds: List of alpha thresholds to test.

    Returns:
        A dataframe summarizing the sensitivity analysis.
    """
    if alpha_thresholds is None:
        alpha_thresholds = get_alpha_thresholds()

    subfields = ["CA3", "DG", "Subiculum"]
    results = []

    for threshold in alpha_thresholds:
        significant_count = 0
        for subfield in subfields:
            try:
                # Fit model
                formula = "vol ~ ACE_score + age + sex + scanner_site + (1|family_id)"
                col = f"{subfield}_norm" if f"{subfield}_norm" in df.columns else subfield
                model = fit_lmm_for_subfield(df, col, formula)

                if model.p_value < threshold:
                    significant_count += 1
            except Exception:
                continue

        results.append({
            "alpha_threshold": threshold,
            "significant_count": significant_count
        })

    return pd.DataFrame(results)


def main() -> None:
    """
    Main entry point for robustness validation.
    Runs permutation tests, sensitivity analysis, and ICV restriction.
    """
    project_root = get_project_root()
    ensure_directories()

    # Load data
    df = load_cleaned_data()
    logging.info(f"Loaded {len(df)} participants")

    # 1. Run Permutation Tests
    logging.info("Running permutation tests...")
    permutation_results = {}
    formula = "vol ~ ACE_score + age + sex + scanner_site + (1|family_id)"
    subfields = ["CA3", "DG", "Subiculum"]

    for subfield in subfields:
        col = f"{subfield}_norm" if f"{subfield}_norm" in df.columns else subfield
        if col in df.columns:
            start_time = time.time()
            p_perm = run_permutation_test_parallel(
                df, formula, col,
                n_permutations=get_permutation_count(),
                n_jobs=get_max_workers()
            )
            duration = time.time() - start_time
            logging.info(f"Permutation test for {subfield} completed in {duration:.2f}s")
            permutation_results[subfield] = {"p_permutation": p_perm}

    # 2. Run Sensitivity Analysis
    logging.info("Running sensitivity analysis...")
    sensitivity_df = run_sensitivity_analysis(df)
    sensitivity_path = project_root / "data" / "processed" / "sensitivity_report.csv"
    sensitivity_df.to_csv(sensitivity_path, index=False)
    logging.info(f"Sensitivity report saved to {sensitivity_path}")

    # 3. Run ICV Restricted Analysis
    logging.info("Running ICV restricted analysis...")
    icv_results = run_icv_restricted_analysis(df)
    icv_path = project_root / "data" / "processed" / "icv_restricted_results.json"
    with open(icv_path, 'w') as f:
        json.dump(icv_results, f, indent=2)
    logging.info(f"ICV restricted results saved to {icv_path}")

    # 4. Aggregate Robustness Report
    logging.info("Aggregating robustness report...")
    robustness_report = {
        "permutation_tests": permutation_results,
        "sensitivity_summary": sensitivity_df.to_dict(orient='records'),
        "icv_restricted": icv_results,
        "metadata": {
            "n_permutations": get_permutation_count(),
            "n_workers": get_max_workers(),
            "alpha_thresholds": get_alpha_thresholds()
        }
    }

    robustness_path = project_root / "data" / "processed" / "robustness_report.json"
    with open(robustness_path, 'w') as f:
        json.dump(robustness_report, f, indent=2)
    logging.info(f"Robustness report saved to {robustness_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
