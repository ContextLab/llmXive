"""
Statistical analysis orchestration for phenomenological report validation.

This module orchestrates the computation of validity metrics (Consistency, Stability, Markers),
performs assumption checking (Normality, Homogeneity), and executes appropriate statistical tests
(ANOVA or Kruskal-Wallis) with post-hoc corrections.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import shapiro, levene, f_oneway, kruskal

# Local imports from sibling modules
from analysis.fdr_correction import run_fdr_correction, FDRCorrectionError
from analysis.tukey_hsd import run_tukey_posthoc, TukeyHSDError

# Configure logger
logger = logging.getLogger(__name__)


class StatsAnalysisError(Exception):
    """Custom exception for statistical analysis failures."""
    pass


def load_aggregated_scores(
    data_dir: Path,
    filename: str = "validity_scores.csv"
) -> pd.DataFrame:
    """
    Load aggregated validity scores from the processed data directory.

    Args:
        data_dir: Path to the data directory containing processed files.
        filename: Name of the CSV file containing validity scores.

    Returns:
        DataFrame containing the aggregated scores.

    Raises:
        StatsAnalysisError: If the file cannot be loaded or is empty.
    """
    file_path = data_dir / filename

    if not file_path.exists():
        raise StatsAnalysisError(f"Scores file not found: {file_path}")

    try:
        df = pd.read_csv(file_path)
        if df.empty:
            raise StatsAnalysisError(f"Scores file is empty: {file_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load scores from {file_path}: {e}")
        raise StatsAnalysisError(f"Failed to load scores: {e}")


def check_normality(
    df: pd.DataFrame,
    column: str,
    group_col: str = "strategy",
    alpha: float = 0.05
) -> Tuple[bool, Dict[str, float]]:
    """
    Check the normality assumption for each group using Shapiro-Wilk test.

    Args:
        df: DataFrame containing the data.
        column: Name of the column to test for normality.
        group_col: Name of the column defining the groups.
        alpha: Significance level for the test.

    Returns:
        Tuple of (is_normal, p_values_dict) where is_normal is True if all groups pass.
    """
    groups = df[group_col].unique()
    p_values = {}
    all_normal = True

    for group in groups:
        group_data = df[df[group_col] == group][column].dropna()
        if len(group_data) < 3:
            logger.warning(f"Insufficient data for Shapiro-Wilk test in group {group} (n={len(group_data)}). Skipping.")
            p_values[group] = 1.0  # Assume normal if too few samples to fail
            continue

        stat, p = shapiro(group_data)
        p_values[group] = p
        if p < alpha:
            all_normal = False
            logger.info(f"Group '{group}' failed normality test (p={p:.4f} < {alpha}).")
        else:
            logger.info(f"Group '{group}' passed normality test (p={p:.4f}).")

    return all_normal, p_values


def check_homogeneity(
    df: pd.DataFrame,
    column: str,
    group_col: str = "strategy",
    alpha: float = 0.05
) -> Tuple[bool, float]:
    """
    Check the homogeneity of variance assumption using Levene's test.

    Args:
        df: DataFrame containing the data.
        column: Name of the column to test.
        group_col: Name of the column defining the groups.
        alpha: Significance level for the test.

    Returns:
        Tuple of (is_homogeneous, p_value).
    """
    groups = df[group_col].unique()
    group_data_list = [df[df[group_col] == g][column].dropna() for g in groups]

    # Filter out empty groups
    group_data_list = [g for g in group_data_list if len(g) > 0]

    if len(group_data_list) < 2:
        logger.warning("Less than 2 groups with data for Levene's test. Assuming homogeneity.")
        return True, 1.0

    try:
        stat, p = levene(*group_data_list)
        is_homogeneous = p >= alpha
        logger.info(f"Levene's test for homogeneity: stat={stat:.4f}, p={p:.4f}. {'Passed' if is_homogeneous else 'Failed'}.")
        return is_homogeneous, p
    except Exception as e:
        logger.error(f"Levene's test failed: {e}")
        # If test fails, we cannot assume homogeneity, but for safety in ANOVA,
        # we might treat it as failed or handle gracefully. Here we return False.
        return False, 0.0


def run_anova(
    df: pd.DataFrame,
    column: str,
    group_col: str = "strategy"
) -> Tuple[float, float]:
    """
    Run one-way ANOVA test.

    Args:
        df: DataFrame containing the data.
        column: Name of the dependent variable column.
        group_col: Name of the independent variable column.

    Returns:
        Tuple of (F_statistic, p_value).
    """
    groups = df[group_col].unique()
    group_data_list = [df[df[group_col] == g][column].dropna() for g in groups]
    group_data_list = [g for g in group_data_list if len(g) > 0]

    if len(group_data_list) < 2:
        raise StatsAnalysisError("Not enough groups to run ANOVA.")

    stat, p = f_oneway(*group_data_list)
    logger.info(f"ANOVA result: F={stat:.4f}, p={p:.4f}")
    return stat, p


def run_kruskal(
    df: pd.DataFrame,
    column: str,
    group_col: str = "strategy"
) -> Tuple[float, float]:
    """
    Run Kruskal-Wallis H test (non-parametric alternative to ANOVA).

    Args:
        df: DataFrame containing the data.
        column: Name of the dependent variable column.
        group_col: Name of the independent variable column.

    Returns:
        Tuple of (H_statistic, p_value).
    """
    groups = df[group_col].unique()
    group_data_list = [df[df[group_col] == g][column].dropna() for g in groups]
    group_data_list = [g for g in group_data_list if len(g) > 0]

    if len(group_data_list) < 2:
        raise StatsAnalysisError("Not enough groups to run Kruskal-Wallis.")

    stat, p = kruskal(*group_data_list)
    logger.info(f"Kruskal-Wallis result: H={stat:.4f}, p={p:.4f}")
    return stat, p


def orchestrate_analysis(
    df: pd.DataFrame,
    metrics: List[str],
    group_col: str = "strategy",
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Orchestrate the full statistical analysis pipeline for a set of metrics.

    Args:
        df: DataFrame containing the aggregated scores.
        metrics: List of column names to analyze (e.g., ['consistency_score', 'stability_score']).
        group_col: Column name for the independent variable (e.g., 'strategy').
        output_path: Optional path to write the results JSON.

    Returns:
        Dictionary containing the analysis results.
    """
    results: Dict[str, Any] = {
        "metrics_analyzed": metrics,
        "group_col": group_col,
        "assumptions": {},
        "tests": {}
    }

    for metric in metrics:
        if metric not in df.columns:
            logger.warning(f"Metric '{metric}' not found in dataframe. Skipping.")
            continue

        logger.info(f"Analyzing metric: {metric}")

        # 1. Check Assumptions
        normal, p_norm = check_normality(df, metric, group_col)
        homog, p_levene = check_homogeneity(df, metric, group_col)

        results["assumptions"][metric] = {
            "normality": {"passed": normal, "p_values": p_norm},
            "homogeneity": {"passed": homog, "p_value": p_levene}
        }

        # 2. Select and Run Test
        test_result: Dict[str, Any] = {}
        if normal and homog:
            logger.info(f"Assumptions met for {metric}. Running ANOVA.")
            try:
                f_stat, p_val = run_anova(df, metric, group_col)
                test_result["method"] = "ANOVA"
                test_result["statistic"] = float(f_stat)
                test_result["p_value"] = float(p_val)
                test_result["significant"] = p_val < 0.05

                # Post-hoc if significant
                if test_result["significant"]:
                    logger.info(f"ANOVA significant for {metric}. Running Tukey HSD.")
                    try:
                        tukey_res = run_tukey_posthoc(df, metric, group_col)
                        test_result["post_hoc"] = tukey_res
                    except TukeyHSDError as e:
                        logger.error(f"Tukey HSD failed: {e}")
                        test_result["post_hoc_error"] = str(e)

                    # FDR Correction on pairwise comparisons if available
                    if "comparisons" in tukey_res:
                        try:
                            fdr_res = run_fdr_correction(
                                [c["pvalue"] for c in tukey_res["comparisons"]]
                            )
                            test_result["fdr_corrected"] = fdr_res
                        except FDRCorrectionError as e:
                            logger.error(f"FDR Correction failed: {e}")
                            test_result["fdr_error"] = str(e)

            except Exception as e:
                logger.error(f"ANOVA failed for {metric}: {e}")
                test_result["error"] = str(e)

        else:
            logger.info(f"Assumptions violated for {metric}. Running Kruskal-Wallis.")
            try:
                h_stat, p_val = run_kruskal(df, metric, group_col)
                test_result["method"] = "Kruskal-Wallis"
                test_result["statistic"] = float(h_stat)
                test_result["p_value"] = float(p_val)
                test_result["significant"] = p_val < 0.05
                # Note: Post-hoc for Kruskal-Wallis is more complex (e.g., Dunn's test),
                # often requiring external libraries not in base deps. Skipping for now.
            except Exception as e:
                logger.error(f"Kruskal-Wallis failed for {metric}: {e}")
                test_result["error"] = str(e)

        results["tests"][metric] = test_result

    # Write output if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Analysis results written to {output_path}")

    return results


def main() -> None:
    """Main entry point for the stats analysis script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data" / "processed"
    output_file = data_dir / "statistical_analysis_results.json"

    # Ensure data directory exists
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return

    try:
        # Load data
        df = load_aggregated_scores(data_dir, "validity_scores.csv")
        logger.info(f"Loaded {len(df)} rows from validity_scores.csv")

        # Define metrics to analyze
        metrics = ["consistency_score", "stability_score", "marker_density"]

        # Run orchestration
        results = orchestrate_analysis(df, metrics, output_path=output_file)

        # Print summary
        print("\n--- Analysis Summary ---")
        for metric, test_data in results["tests"].items():
            method = test_data.get("method", "N/A")
            sig = test_data.get("significant", False)
            print(f"{metric}: {method} - Significant: {sig}")

    except StatsAnalysisError as e:
        logger.error(f"Analysis failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        raise


if __name__ == "__main__":
    main()