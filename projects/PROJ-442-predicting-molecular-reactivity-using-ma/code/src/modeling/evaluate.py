"""
Evaluation module for molecular reactivity prediction.
Implements Spearman correlation, permutation testing, and report generation.
"""
import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from scipy.stats import spearmanr

from src.utils.logging import setup_logger, get_logger
from src.utils.state_manager import update_stage_status, register_artifact
from src.modeling.config import load_config

# Constants
DEFAULT_PERMUTATION_ITERATIONS = 1000
SIGNIFICANCE_THRESHOLD = 0.01
MIN_SAMPLE_SIZE = 1000


def load_cv_results(input_path: str) -> pd.DataFrame:
    """
    Load cross-validation results from a CSV file.

    Args:
        input_path: Path to the CSV file containing CV results.

    Returns:
        DataFrame with columns: reaction_type, predicted, observed, fold (optional).
    """
    logger = get_logger(__name__)
    logger.info(f"Loading CV results from {input_path}")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"CV results file not found: {input_path}")

    df = pd.read_csv(input_path)

    # Validate required columns
    required_cols = ['reaction_type', 'predicted', 'observed']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in CV results: {missing_cols}")

    logger.info(f"Loaded {len(df)} records with columns: {list(df.columns)}")
    return df


def compute_spearman_correlation(df: pd.DataFrame, reaction_type: str) -> Optional[float]:
    """
    Compute Spearman rank correlation (ρ) for a specific reaction type.

    Args:
        df: DataFrame with 'reaction_type', 'predicted', and 'observed' columns.
        reaction_type: The specific reaction type to filter and compute correlation for.

    Returns:
        Spearman correlation coefficient, or None if insufficient data.
    """
    logger = get_logger(__name__)
    subset = df[df['reaction_type'] == reaction_type]

    if len(subset) < 3:
        logger.warning(f"Insufficient data for {reaction_type} (n={len(subset)}). Skipping correlation.")
        return None

    try:
        rho, p_value = spearmanr(subset['predicted'], subset['observed'])
        logger.info(f"Spearman ρ for {reaction_type}: {rho:.4f} (p={p_value:.4f}, n={len(subset)})")
        return rho
    except Exception as e:
        logger.error(f"Error computing Spearman correlation for {reaction_type}: {e}")
        return None


def run_permutation_test(
    df: pd.DataFrame,
    reaction_type: str,
    n_iterations: int = DEFAULT_PERMUTATION_ITERATIONS,
    seed: int = 42
) -> Tuple[float, float]:
    """
    Run a permutation test to assess the significance of the Spearman correlation.

    Null hypothesis: The correlation between predicted and observed is zero.
    We shuffle the 'observed' values within the class and recompute ρ.

    Args:
        df: DataFrame with 'reaction_type', 'predicted', and 'observed'.
        reaction_type: The class to test.
        n_iterations: Number of permutation iterations.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (observed_rho, p_value).
    """
    logger = get_logger(__name__)
    logger.info(f"Running permutation test for {reaction_type} with {n_iterations} iterations...")

    subset = df[df['reaction_type'] == reaction_type]
    if len(subset) < 3:
        raise ValueError(f"Insufficient data for permutation test in {reaction_type} (n={len(subset)})")

    observed_pred = subset['predicted'].values
    observed_obs = subset['observed'].values

    # Compute observed correlation
    observed_rho, _ = spearmanr(observed_pred, observed_obs)

    np.random.seed(seed)
    count_extreme = 0

    for i in range(n_iterations):
        # Shuffle observed values within the class
        shuffled_obs = observed_obs.copy()
        np.random.shuffle(shuffled_obs)

        # Compute correlation on shuffled data
        try:
            rho_shuffled, _ = spearmanr(observed_pred, shuffled_obs)
            # Two-tailed test: count if absolute value is >= observed absolute value
            if abs(rho_shuffled) >= abs(observed_rho):
                count_extreme += 1
        except Exception:
            # If correlation fails (e.g., constant values), treat as non-extreme
            continue

    p_value = (count_extreme + 1) / (n_iterations + 1)
    logger.info(f"Permutation test for {reaction_type}: p-value = {p_value:.4f}")

    return observed_rho, p_value


def load_exclusion_metadata(metadata_path: str) -> List[str]:
    """
    Load the list of excluded classes from the metadata file.

    Args:
        metadata_path: Path to class_exclusion_metadata.json.

    Returns:
        List of excluded class names.
    """
    logger = get_logger(__name__)
    if not os.path.exists(metadata_path):
        logger.warning(f"Exclusion metadata not found at {metadata_path}. Assuming no exclusions.")
        return []

    try:
        with open(metadata_path, 'r') as f:
            data = json.load(f)
        excluded = data.get('excluded_classes', [])
        logger.info(f"Loaded {len(excluded)} excluded classes from metadata.")
        return excluded
    except Exception as e:
        logger.error(f"Error loading exclusion metadata: {e}")
        return []


def generate_summary_report(
    df: pd.DataFrame,
    output_path: str,
    exclusion_metadata_path: Optional[str] = None,
    n_permutations: int = DEFAULT_PERMUTATION_ITERATIONS
) -> Dict[str, Any]:
    """
    Generate the final analysis report ranking reaction types by Spearman ρ with p-values.

    Args:
        df: DataFrame with CV results.
        output_path: Path to save the JSON report.
        exclusion_metadata_path: Path to class_exclusion_metadata.json (from T016).
        n_permutations: Number of permutation iterations.

    Returns:
        The generated report dictionary.
    """
    logger = get_logger(__name__)
    start_time = time.time()

    # Load excluded classes
    excluded_classes = []
    if exclusion_metadata_path:
        excluded_classes = load_exclusion_metadata(exclusion_metadata_path)

    # Identify unique reaction types in the data
    all_types = df['reaction_type'].unique().tolist()
    logger.info(f"Found reaction types in data: {all_types}")

    results = []

    for rtype in all_types:
        if rtype in excluded_classes:
            logger.info(f"Skipping excluded class: {rtype}")
            continue

        logger.info(f"Processing {rtype}...")

        # Compute Spearman correlation
        rho = compute_spearman_correlation(df, rtype)
        if rho is None:
            continue

        # Run permutation test
        try:
            _, p_value = run_permutation_test(df, rtype, n_iterations=n_permutations)
        except ValueError as e:
            logger.warning(f"Skipping permutation test for {rtype}: {e}")
            p_value = None

        # Determine significance
        is_significant = False
        if p_value is not None and p_value < SIGNIFICANCE_THRESHOLD:
            is_significant = True

        results.append({
            "reaction_type": rtype,
            "spearman_rho": rho,
            "p_value": p_value,
            "is_significant": is_significant,
            "sample_size": len(df[df['reaction_type'] == rtype])
        })

    # Sort by Spearman rho (descending)
    results.sort(key=lambda x: x['spearman_rho'] if x['spearman_rho'] is not None else 0, reverse=True)

    report = {
        "report_type": "molecular_reactivity_analysis",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "threshold_significance": SIGNIFICANCE_THRESHOLD,
        "permutation_iterations": n_permutations,
        "excluded_classes": excluded_classes,
        "results": results,
        "summary": {
            "total_classes_analyzed": len(results),
            "significant_classes": sum(1 for r in results if r['is_significant']),
            "top_performing_class": results[0]['reaction_type'] if results else None,
            "top_rho": results[0]['spearman_rho'] if results else None
        }
    }

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    elapsed = time.time() - start_time
    logger.info(f"Report generated in {elapsed:.2f}s and saved to {output_path}")

    return report


def main():
    """
    Main entry point for the evaluation script.
    Expects --input (CV results CSV) and --output (report JSON) arguments.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate molecular reactivity analysis report.")
    parser.add_argument("--input", required=True, help="Path to CV results CSV (e.g., data/results/cv_results.csv)")
    parser.add_argument("--output", required=True, help="Path to output report JSON (e.g., data/processed/analysis_report.json)")
    parser.add_argument("--config", default="code/src/modeling/config.yaml", help="Path to config file")
    parser.add_argument("--exclusion-metadata", default="code/data/processed/class_exclusion_metadata.json",
                        help="Path to class exclusion metadata JSON")
    parser.add_argument("--n-permutations", type=int, default=DEFAULT_PERMUTATION_ITERATIONS,
                        help="Number of permutation iterations")

    args = parser.parse_args()

    # Setup logging
    setup_logger(__name__)
    logger = get_logger(__name__)

    try:
        # Load config if needed (for potential overrides)
        config = load_config(args.config)

        # Load CV results
        df = load_cv_results(args.input)

        # Generate report
        report = generate_summary_report(
            df=df,
            output_path=args.output,
            exclusion_metadata_path=args.exclusion_metadata,
            n_permutations=args.n_permutations
        )

        # Update state
        update_stage_status("US3", "completed")
        register_artifact(args.output, "analysis_report")

        logger.info("Evaluation completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        raise


if __name__ == "__main__":
    main()