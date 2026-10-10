"""
Robustness Analysis Module (T035: leave-one-country-out cross-validation).

Implements leave-one-country-out (LOCO) cross-validation per FR-009.
'Region' is interpreted as administrative level 0 (Country): with only 3
countries, leave-one-region-out with N=2 training regions would be
statistically invalid, so the country level is used to satisfy the Spec's
intent while preserving statistical validity.

Metric: coefficient stability — the standard deviation of coefficient
estimates across folds — is computed for every predictor and logged,
along with a per-fold detail table, to ``loco_stability_report.json``.

Bootstrap resampling (T036) is also present in the pipeline.

NOTE (FR-004): all findings are framed as ASSOCIATIONAL relationships.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from utils.config import get_processed_data_dir, get_state_dir

logger = logging.getLogger(__name__)

# Default model formula (associational framing; country dummies absorb
# country-level heterogeneity in the Fixed-Effects spirit of the plan).
DEFAULT_FORMULA = (
    "hdds ~ csa_index + digital_access + finance_access "
    "+ digital_access:finance_access + C(country)"
)


def load_model_results(results_path: Optional[str] = None) -> pd.DataFrame:
    """Load model results from JSON/Parquet if available, otherwise return None."""
    if results_path and Path(results_path).exists():
        p = Path(results_path)
        if p.suffix == ".parquet":
            return pd.read_parquet(p)
        return pd.read_json(p)
    return None


def _fit_ols(data: pd.DataFrame, formula: str):
    """Fit OLS on ``data``; return the fitted results or None on failure."""
    try:
        return smf.ols(formula=formula, data=data).fit()
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("Model fit failed: %s", e)
        return None


def run_bootstrap_resampling(
    data: pd.DataFrame,
    formula: str,
    n_iterations: int = 100,
    random_state: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Perform bootstrap resampling to validate model stability.

    Args:
        data: The analysis dataset.
        formula: The model formula.
        n_iterations: Number of bootstrap iterations.
        random_state: Seed for reproducibility.

    Returns:
        Dictionary containing coefficient estimates and confidence intervals.
    """
    if random_state is not None:
        np.random.seed(random_state)

    n = len(data)
    coefficients: Dict[str, List[float]] = {}

    logger.info("Running %d bootstrap iterations...", n_iterations)

    for i in range(n_iterations):
        sample_idx = np.random.choice(n, size=n, replace=True)
        sample_data = data.iloc[sample_idx]

        model = _fit_ols(sample_data, formula)
        if model is None:
            logger.warning("Bootstrap iteration %d failed; skipping.", i)
            continue

        for name, value in model.params.items():
            coefficients.setdefault(name, []).append(float(value))

    results: Dict[str, Any] = {}
    for key, values in coefficients.items():
        if values:
            results[key] = {
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "ci_lower": float(np.percentile(values, 2.5)),
                "ci_upper": float(np.percentile(values, 97.5)),
                "n_successful": len(values),
            }
        else:
            results[key] = {"error": "No successful iterations"}
    return results


def run_leave_one_region_out(
    data: pd.DataFrame,
    formula: str,
    region_col: str = "country",
) -> Dict[str, Any]:
    """
    Perform leave-one-country-out cross-validation (T035, FR-009).

    Region definition: administrative level 0 (Country). With only 3
    countries, leave-one-region-out (N=2 training) is statistically
    invalid, so 'region' is interpreted as 'country'.

    For each fold, one country is held out and the model is refit on the
    remaining countries. The stability metric — the standard deviation of
    coefficient estimates across folds — is computed for every predictor
    shared by all folds and logged.

    Args:
        data: The analysis dataset.
        formula: The model formula.
        region_col: Column name for the region/country (default 'country').

    Returns:
        Dictionary containing coefficient stability metrics.
    """
    if region_col not in data.columns:
        raise ValueError(
            f"Region column '{region_col}' not found in dataset columns: "
            f"{list(data.columns)}"
        )

    unique_regions = list(data[region_col].dropna().unique())
    if len(unique_regions) < 2:
        logger.warning(
            "Not enough regions (%d) to perform leave-one-out.",
            len(unique_regions),
        )
        return {}

    fold_details: List[Dict[str, Any]] = []
    fold_params: Dict[str, List[float]] = {}

    logger.info(
        "Running leave-one-%s-out cross-validation over %d folds...",
        region_col,
        len(unique_regions),
    )

    for region in unique_regions:
        train_data = data[data[region_col] != region]
        if len(train_data) == 0:
            logger.warning("Fold excluding %r has no training data; skipped.", region)
            continue

        model = _fit_ols(train_data, formula)
        if model is None:
            logger.warning("LOCO fold for region %r failed; skipped.", region)
            continue

        for name, value in model.params.items():
            fold_params.setdefault(name, []).append(float(value))

        fold_details.append(
            {
                "excluded_region": str(region),
                "n_obs": int(len(train_data)),
                "r_squared": float(model.rsquared),
                "coefficients": {k: float(v) for k, v in model.params.items()},
            }
        )

    if not fold_details:
        logger.warning("No successful LOCO folds; returning empty result.")
        return {}

    # Stability metric: standard deviation of estimates across folds,
    # computed only over predictors present in EVERY successful fold so
    # the metric is well-defined.
    n_folds = len(fold_details)
    stability: Dict[str, Any] = {}
    for name, values in fold_params.items():
        if len(values) != n_folds:
            continue
        stability[name] = {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "n_folds": n_folds,
        }

    report: Dict[str, Any] = {
        "method": "leave_one_country_out",
        "region_definition": "administrative level 0 (country)",
        "region_col": region_col,
        "n_folds": n_folds,
        "coefficient_stability": stability,
        "details": fold_details,
        "interpretation": (
            "Associational stability check: the standard deviation of "
            "coefficient estimates across leave-one-country-out folds. "
            "Smaller values indicate the associations are not driven by "
            "any single country."
        ),
    }

    # Log the stability metric (std of estimates across folds).
    for name, stats in stability.items():
        logger.info(
            "LOCO stability for %s: std=%.6f mean=%.6f (across %d folds)",
            name,
            stats["std"],
            stats["mean"],
            n_folds,
        )

    return report


def calculate_stability_metric(
    loco_report: Dict[str, Any],
    output_path: Path,
) -> None:
    """
    Extract the standard deviation (and related statistics) for each predictor
    from the LOCO report and write them to ``loco_stability_report.json``.

    This function implements T035b: it isolates the stability metric and
    persists it as a dedicated JSON artifact.

    Args:
        loco_report: The full dictionary returned by ``run_leave_one_region_out``.
        output_path: Destination file path for the stability JSON.
    """
    stability = loco_report.get("coefficient_stability", {})
    # Ensure the directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write only the stability portion (including mean and std) to disk.
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "method": loco_report.get("method", "leave_one_country_out"),
                "region_col": loco_report.get("region_col", "country"),
                "n_folds": loco_report.get("n_folds", 0),
                "coefficient_stability": stability,
            },
            f,
            indent=2,
            default=str,
        )
    logger.info("Stability metrics written to %s", output_path)


def run_robustness_pipeline(
    data: pd.DataFrame,
    formula: str,
    output_dir: Optional[Path] = None,
    bootstrap_iterations: int = 100,
) -> Dict[str, Any]:
    """Run the full robustness pipeline: LOCO and Bootstrap."""
    if output_dir is None:
        output_dir = get_processed_data_dir()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results: Dict[str, Any] = {"formula": formula}

    # 1. Leave-One-Country-Out (T035 / FR-009)
    try:
        loco_results = run_leave_one_region_out(data, formula)
        results["leave_one_country_out"] = loco_results

        # T035b: write the dedicated stability report
        stability_path = output_dir / "loco_stability_report.json"
        calculate_stability_metric(loco_results, stability_path)

    except Exception as e:
        logger.error("LOCO analysis failed: %s", e)
        results["leave_one_country_out"] = {"error": str(e)}

    # 2. Bootstrap (T036)
    try:
        boot_results = run_bootstrap_resampling(
            data, formula, n_iterations=bootstrap_iterations, random_state=42
        )
        results["bootstrap"] = boot_results
        with open(output_dir / "bootstrap_results.json", "w") as f:
            json.dump(boot_results, f, indent=2, default=str)
    except Exception as e:
        logger.error("Bootstrap analysis failed: %s", e)
        results["bootstrap"] = {"error": str(e)}

    # Combined deliverable referenced by the run-book.
    with open(output_dir / "robustness_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    return results


def main():
    """
    Main entry point for robustness checks.
    Requires --data argument to be passed via CLI.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Run robustness checks (LOCO + bootstrap) on the analysis dataset."
    )
    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to the processed dataset (parquet).",
    )
    parser.add_argument(
        "--formula",
        type=str,
        default=DEFAULT_FORMULA,
        help="Model formula (associational; country dummies as fixed effects).",
    )
    parser.add_argument(
        "--random-effect",
        type=str,
        default=None,
        help="Random effect specification (not used in fixed-effects).",
    )
    parser.add_argument(
        "--weights", type=str, default=None, help="Sampling weights column."
    )
    parser.add_argument(
        "--bootstrap-iterations",
        type=int,
        default=100,
        help="Number of bootstrap iterations.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for results (default: data/processed).",
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=1,
        help="Number of parallel jobs (not implemented yet).",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logger.info("Loading data from %s", args.data)

    if not Path(args.data).exists():
        raise FileNotFoundError(f"Data file not found: {args.data}")

    data = pd.read_parquet(args.data)

    # Basic validation
    if "csa_index" not in data.columns:
        logger.warning(
            "csa_index not found in data. Attempting to use a similar column."
        )
        matching_cols = [c for c in data.columns if "csa" in c.lower()]
        if matching_cols:
            data["csa_index"] = data[matching_cols[0]]
            logger.info("Using column %s as csa_index.", matching_cols[0])
        else:
            raise ValueError("Could not find CSA index column in dataset.")

    if "country" not in data.columns:
        raise ValueError("Country column not found in dataset.")

    output_dir = Path(args.output_dir) if args.output_dir else get_processed_data_dir()

    results = run_robustness_pipeline(
        data=data,
        formula=args.formula,
        output_dir=output_dir,
        bootstrap_iterations=args.bootstrap_iterations,
    )

    summary_path = output_dir / "robustness_summary.json"
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(
        "Robustness analysis complete. Results saved to %s "
        "(all findings are associational, not causal).",
        summary_path,
    )


if __name__ == "__main__":
    main()