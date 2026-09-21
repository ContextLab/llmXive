"""
Correlation Analysis Module for Perovskite Thermal Conductivity Study.

Implements Pearson and Spearman correlation calculations with multiple-comparison
correction (Bonferroni or FDR) on stratified perovskite datasets.
"""
import sys
import logging
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from statsmodels.stats.multitest import multipletests

from src.utils.seed_manager import init_seed, get_seed, setup_logger_module as seed_setup_logger
from src.utils.validation import setup_logger


def setup_logger_module(name: str, level: int = logging.INFO) -> logging.Logger:
    """Initialize a module-specific logger."""
    return setup_logger(name, level)


def compute_correlation_matrix(
    df: pd.DataFrame,
    predictors: List[str],
    target: str = "thermal_conductivity",
    method: str = "pearson",
    seed: Optional[int] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute correlation matrix between predictors and target.

    Args:
        df: Input dataframe containing predictors and target.
        predictors: List of predictor column names.
        target: Target column name.
        method: Correlation method ('pearson' or 'spearman').
        seed: Random seed for reproducibility (not used in deterministic correlation).

    Returns:
        Tuple of (correlation_values_df, p_values_df)
    """
    if seed is not None:
        init_seed(seed)

    logger = setup_logger_module("correlation")
    logger.info(f"Computing {method} correlation for {len(predictors)} predictors")

    # Ensure all columns exist
    missing = [col for col in predictors + [target] if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in dataframe: {missing}")

    # Drop rows with NaN in relevant columns
    clean_df = df[predictors + [target]].dropna()

    if len(clean_df) == 0:
        raise ValueError("No valid data rows after dropping NaN values")

    correlations = []
    p_values = []

    for pred in predictors:
        if method == "pearson":
            corr, p_val = pearsonr(clean_df[pred], clean_df[target])
        elif method == "spearman":
            corr, p_val = spearmanr(clean_df[pred], clean_df[target])
        else:
            raise ValueError(f"Unknown correlation method: {method}")

        correlations.append(corr)
        p_values.append(p_val)

    corr_df = pd.DataFrame({
        "predictor": predictors,
        "correlation": correlations
    })
    p_df = pd.DataFrame({
        "predictor": predictors,
        "p_value": p_values
    })

    logger.info(f"Correlation computation complete. Min corr: {min(correlations):.4f}, Max corr: {max(correlations):.4f}")

    return corr_df, p_df


def apply_multiple_comparison_correction(
    p_values: List[float],
    method: str = "bonferroni",
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Apply multiple-comparison correction to p-values.

    Args:
        p_values: List of raw p-values.
        method: Correction method ('bonferroni' or 'fdr').
        alpha: Significance threshold.

    Returns:
        Dictionary with 'corrected_p_values', 'is_significant', 'method', and 'alpha'.
    """
    if not p_values:
        return {
            "corrected_p_values": [],
            "is_significant": [],
            "method": method,
            "alpha": alpha
        }

    p_array = np.array(p_values)

    if method == "bonferroni":
        corrected = multipletests(p_array, alpha=alpha, method='bonferroni')
    elif method == "fdr":
        corrected = multipletests(p_array, alpha=alpha, method='fdr_bh')
    else:
        raise ValueError(f"Unknown correction method: {method}. Use 'bonferroni' or 'fdr'.")

    # corrected[0]: reject, [1]: p-corrected, [2]: p-value (original), [3]: alpha-corrected
    return {
        "corrected_p_values": corrected[1].tolist(),
        "is_significant": corrected[0].tolist(),
        "method": method,
        "alpha": alpha
    }


def stratified_correlation_analysis(
    df: pd.DataFrame,
    stratify_column: str = "chemistry_class",
    predictors: List[str] = None,
    target: str = "thermal_conductivity",
    correlation_methods: List[str] = None,
    correction_method: str = "bonferroni",
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform correlation analysis stratified by a categorical column.

    Args:
        df: Input dataframe.
        stratify_column: Column to stratify by (e.g., 'chemistry_class').
        predictors: List of predictor columns. Defaults to numeric columns excluding target.
        target: Target variable column name.
        correlation_methods: List of methods to compute ('pearson', 'spearman').
        correction_method: Multiple comparison correction method.
        seed: Random seed.

    Returns:
        Dictionary containing stratified results and corrected p-values.
    """
    if seed is not None:
        init_seed(seed)

    logger = setup_logger_module("correlation")
    logger.info(f"Starting stratified analysis by '{stratify_column}'")

    if predictors is None:
        # Default: all numeric columns except target and stratify column
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        predictors = [c for c in numeric_cols if c != target and c != stratify_column]

    if correlation_methods is None:
        correlation_methods = ["pearson", "spearman"]

    results = {
        "stratified_results": {},
        "corrected_p_values": {},
        "metadata": {
            "stratify_column": stratify_column,
            "predictors": predictors,
            "target": target,
            "correlation_methods": correlation_methods,
            "correction_method": correction_method,
            "seed": seed
        }
    }

    groups = df[stratify_column].unique()
    logger.info(f"Found {len(groups)} strata: {groups}")

    for group in groups:
        group_df = df[df[stratify_column] == group]
        logger.info(f"Processing stratum: {group} (n={len(group_df)})")

        if len(group_df) < 5:
            logger.warning(f"Skipping stratum '{group}' with insufficient samples ({len(group_df)} < 5)")
            continue

        group_results = {}
        all_p_values = []

        for method in correlation_methods:
            corr_df, p_df = compute_correlation_matrix(
                group_df, predictors, target, method, seed
            )

            # Store correlations
            group_results[method] = {
                "correlations": corr_df.to_dict(orient="records"),
                "p_values": p_df["p_value"].tolist()
            }

            # Collect p-values for correction
            all_p_values.extend(p_df["p_value"].tolist())

        # Apply correction to all p-values in this stratum
        correction_result = apply_multiple_comparison_correction(
            all_p_values, correction_method
        )

        results["stratified_results"][str(group)] = group_results
        results["corrected_p_values"][str(group)] = correction_result

    logger.info("Stratified correlation analysis complete")
    return results


def save_correlation_results(
    results: Dict[str, Any],
    output_path: Union[str, Path]
) -> None:
    """Save correlation results to a JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logging.getLogger("correlation").info(f"Results saved to {output_path}")


def main():
    """CLI entry point for correlation analysis."""
    parser = argparse.ArgumentParser(
        description="Compute stratified correlations with multiple-comparison correction."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to stratified input CSV (output of T022 stratify.py)"
    )
    parser.add_argument(
        "--sensitivity-input",
        type=str,
        required=True,
        help="Path to sensitivity analysis JSON (output of T023b)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/correlation_matrix.json",
        help="Output path for correlation results JSON"
    )
    parser.add_argument(
        "--stratify-column",
        type=str,
        default="chemistry_class",
        help="Column to stratify by"
    )
    parser.add_argument(
        "--correction-method",
        type=str,
        default="bonferroni",
        choices=["bonferroni", "fdr"],
        help="Multiple comparison correction method"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--predictors",
        type=str,
        nargs="+",
        default=None,
        help="List of predictor columns (default: auto-detect numeric)"
    )

    args = parser.parse_args()

    # Initialize logger
    logger = setup_logger("correlation_main", logging.INFO)
    logger.info(f"Starting correlation analysis with args: {args}")

    # Validate sensitivity input exists (dependency T023b)
    sens_path = Path(args.sensitivity_input)
    if not sens_path.exists():
        logger.error(f"Sensitivity analysis file not found: {sens_path}")
        sys.exit(1)

    # Load sensitivity analysis to verify it ran (optional validation)
    try:
        with open(sens_path, 'r') as f:
            sens_data = json.load(f)
        logger.info(f"Loaded sensitivity analysis: {list(sens_data.keys())}")
    except Exception as e:
        logger.warning(f"Could not parse sensitivity file: {e}")

    # Load input data
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load input CSV: {e}")
        sys.exit(1)

    # Run analysis
    predictors = args.predictors
    if predictors:
        # Validate predictors exist
        missing = [p for p in predictors if p not in df.columns]
        if missing:
            logger.error(f"Predictors not found in data: {missing}")
            sys.exit(1)

    try:
        results = stratified_correlation_analysis(
            df=df,
            stratify_column=args.stratify_column,
            predictors=predictors,
            target="thermal_conductivity",
            correlation_methods=["pearson", "spearman"],
            correction_method=args.correction_method,
            seed=args.seed
        )
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        sys.exit(1)

    # Save results
    try:
        save_correlation_results(results, args.output)
        logger.info(f"Successfully wrote results to {args.output}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()