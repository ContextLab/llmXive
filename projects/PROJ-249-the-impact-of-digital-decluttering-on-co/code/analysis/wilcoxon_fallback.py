"""
Fallback Wilcoxon Signed-Rank Test Implementation.

This module implements the fallback statistical test (Wilcoxon signed-rank)
to be used ONLY when the primary bootstrap confidence interval calculation
fails to converge (as detected by code/analysis/convergence_detector.py).

Per FR-006: This test is a fallback mechanism and must not be used if
the bootstrap method succeeds.
"""

import os
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from scipy import stats
import numpy as np

# Import project utilities
from utils.random_seed import get_seed
from config.env_config import get_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class WilcoxonResult:
    """
    Container for Wilcoxon signed-rank test results.

    Attributes:
        metric_name: Name of the metric being tested (e.g., 'SART_errors')
        statistic: The Wilcoxon W statistic
        pvalue: The p-value from the test
        z_score: The standardized z-score approximation (if available)
        n: Number of non-zero difference pairs
        alternative: The alternative hypothesis used ('two-sided')
        success: Boolean indicating if the test ran without error
        error_message: Error message if the test failed, None otherwise
    """
    metric_name: str
    statistic: float
    pvalue: float
    z_score: Optional[float]
    n: int
    alternative: str
    success: bool
    error_message: Optional[str] = None


def load_merged_data_for_metric(
    metric_name: str,
    data_dir: Optional[Path] = None
) -> Tuple[List[float], List[float]]:
    """
    Load baseline and post-intervention data for a specific metric from the merged dataset.

    Args:
        metric_name: The name of the metric to extract (e.g., 'SART_errors', 'PSS10_total')
        data_dir: Optional override for the data directory path. Uses config if None.

    Returns:
        Tuple of (baseline_values, post_values) as lists of floats.

    Raises:
        FileNotFoundError: If the merged data file does not exist.
        ValueError: If the metric is not found in the dataset.
    """
    if data_dir is None:
        # Resolve path relative to project root
        project_root = Path(__file__).resolve().parent.parent.parent
        data_dir = project_root / "data" / "processed"

    merged_file = data_dir / "merged_baseline_post.csv"

    if not merged_file.exists():
        raise FileNotFoundError(f"Merged data file not found: {merged_file}")

    logger.info(f"Loading data for metric '{metric_name}' from {merged_file}")

    baseline_values = []
    post_values = []

    try:
        with open(merged_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Ensure we have the required columns
                if 'participant_id' not in row or 'metric_name' not in row:
                    continue

                if row['metric_name'] == metric_name:
                    try:
                        # Parse values, handling potential missing data
                        base_val = row.get('baseline_value')
                        post_val = row.get('post_value')

                        if base_val is not None and post_val is not None:
                            base_f = float(base_val)
                            post_f = float(post_val)

                            # Filter out non-numeric or infinite values if necessary
                            if np.isfinite(base_f) and np.isfinite(post_f):
                                baseline_values.append(base_f)
                                post_values.append(post_f)
                    except (ValueError, TypeError):
                        logger.warning(f"Skipping non-numeric row for {metric_name}: {row}")
                        continue

        if not baseline_values:
            raise ValueError(f"No valid data found for metric '{metric_name}'")

        logger.info(f"Loaded {len(baseline_values)} pairs for {metric_name}")
        return baseline_values, post_values

    except Exception as e:
        logger.error(f"Error reading merged data: {e}")
        raise


def run_wilcoxon_test(
    baseline_values: List[float],
    post_values: List[float],
    metric_name: str,
    alternative: str = 'two-sided'
) -> WilcoxonResult:
    """
    Perform the Wilcoxon signed-rank test on paired samples.

    This is the fallback test used when bootstrap CI fails.

    Args:
        baseline_values: List of baseline measurements.
        post_values: List of post-intervention measurements.
        metric_name: Name of the metric for the result object.
        alternative: Alternative hypothesis ('two-sided', 'less', 'greater').

    Returns:
        WilcoxonResult object containing test statistics.
    """
    if len(baseline_values) != len(post_values):
        return WilcoxonResult(
            metric_name=metric_name,
            statistic=0.0,
            pvalue=1.0,
            z_score=None,
            n=0,
            alternative=alternative,
            success=False,
            error_message="Baseline and post value lists must have equal length."
        )

    if len(baseline_values) < 2:
        return WilcoxonResult(
            metric_name=metric_name,
            statistic=0.0,
            pvalue=1.0,
            z_score=None,
            n=len(baseline_values),
            alternative=alternative,
            success=False,
            error_message="Insufficient sample size (n < 2) for Wilcoxon test."
        )

    try:
        # Convert to numpy arrays for scipy
        arr_baseline = np.array(baseline_values)
        arr_post = np.array(post_values)

        # scipy.stats.wilcoxon handles zero differences by default (zero_method='wilcox')
        # We use the default behavior which drops zero differences
        statistic, p_value = stats.wilcoxon(
            arr_baseline,
            arr_post,
            alternative=alternative
        )

        # Calculate z-score approximation if sample size is sufficient
        # scipy returns z-score if 'zero_method' is not 'wilcox' or if n is large enough,
        # but we can compute it manually if needed. For now, we rely on the returned stats.
        # Note: stats.wilcoxon does not return z directly in all versions, so we compute it.
        # However, for simplicity and robustness, we will rely on the p-value and statistic.
        # If z_score is required for reporting, we can approximate it.
        # Let's try to get z from the result object if available, otherwise None.
        # Since stats.wilcoxon returns (stat, p), we don't have z directly.
        # We will leave z_score as None unless we compute it manually.
        # Manual Z approx: (W - mean_W) / std_W
        # mean_W = n*(n+1)/4
        # std_W = sqrt(n*(n+1)*(2n+1)/24)
        # This is only valid for n > 10 usually.
        z_score = None
        n_nonzero = len(arr_baseline) # scipy drops zeros internally, but we passed filtered lists
        # Actually, scipy drops zeros. Let's trust the count from the function if we could,
        # but we just pass the lists.
        # Let's approximate Z for reporting if n > 10
        if n_nonzero > 10:
            mean_w = n_nonzero * (n_nonzero + 1) / 4.0
            std_w = np.sqrt(n_nonzero * (n_nonzero + 1) * (2 * n_nonzero + 1) / 24.0)
            # Adjust statistic for two-sided? Usually W is the smaller sum of ranks.
            # This approximation is rough but provides a Z-score for reporting.
            # Note: The exact definition of W in scipy depends on the method.
            # We will set z_score to None to be safe and avoid misinterpretation,
            # or calculate it if we are sure of the direction.
            # Let's skip manual Z to avoid confusion and rely on p-value.
            z_score = None

        return WilcoxonResult(
            metric_name=metric_name,
            statistic=float(statistic),
            pvalue=float(p_value),
            z_score=z_score,
            n=len(baseline_values),
            alternative=alternative,
            success=True
        )

    except Exception as e:
        logger.error(f"Wilcoxon test failed for {metric_name}: {e}")
        return WilcoxonResult(
            metric_name=metric_name,
            statistic=0.0,
            pvalue=1.0,
            z_score=None,
            n=len(baseline_values),
            alternative=alternative,
            success=False,
            error_message=str(e)
        )


def run_fallback_pipeline(
    metrics: Optional[List[str]] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the Wilcoxon fallback test for all specified metrics.

    This function is intended to be called by the main analysis pipeline
    ONLY when the bootstrap CI calculation has failed for these metrics.

    Args:
        metrics: List of metric names to test. If None, defaults to standard metrics.
        output_path: Path to write the JSON results. If None, writes to results/.

    Returns:
        Dictionary containing the results for all tested metrics.
    """
    if metrics is None:
        metrics = ['SART_errors', 'Ospan_score', 'PSS10_total', 'PANAS_positive', 'PANAS_negative']

    if output_path is None:
        project_root = Path(__file__).resolve().parent.parent.parent
        output_path = project_root / "results" / "wilcoxon_fallback_results.json"

    results = {
        "status": "fallback_executed",
        "trigger": "bootstrap_convergence_failure",
        "metrics_tested": [],
        "results": []
    }

    logger.info(f"Starting Wilcoxon fallback pipeline for {len(metrics)} metrics")

    for metric in metrics:
        logger.info(f"Processing metric: {metric}")
        try:
            baseline, post = load_merged_data_for_metric(metric)
            result = run_wilcoxon_test(baseline, post, metric)
            results["metrics_tested"].append(metric)
            results["results"].append(asdict(result))

            if result.success:
                logger.info(f"  -> Success: W={result.statistic:.2f}, p={result.pvalue:.4f}")
            else:
                logger.warning(f"  -> Failed: {result.error_message}")

        except FileNotFoundError as e:
            logger.error(f"Data not found for {metric}: {e}")
            results["results"].append({
                "metric_name": metric,
                "success": False,
                "error_message": f"Data missing: {str(e)}"
            })
        except Exception as e:
            logger.error(f"Unexpected error for {metric}: {e}")
            results["results"].append({
                "metric_name": metric,
                "success": False,
                "error_message": str(e)
            })

    # Write results to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Fallback results written to {output_path}")
    return results


def main():
    """
    Entry point for running the Wilcoxon fallback test directly.
    """
    logger.info("Running Wilcoxon Fallback Test (T037)")

    # Run for standard metrics
    run_fallback_pipeline()

    print("Wilcoxon fallback pipeline completed. Check results/wilcoxon_fallback_results.json")


if __name__ == "__main__":
    main()
