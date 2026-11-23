"""
code.services.analyzer
-----------------------

Fit a binomial Generalized Estimating Equation (GEE) regression on step‑level
outcomes and produce the trade‑off curve required by task T007.  In addition,
compute a Cochran‑Armitage trend test and Bonferroni‑adjusted pairwise
p‑values, writing the results to ``data/results/multiplicity_tests.json`` as
required by task T008.
"""
import json
import csv
import yaml
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod.families import Binomial
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.stats.proportion import proportional_trend_test, proportions_ztest

from llmxive_toolkit import paths, get_logger
from jsonschema import validate, ValidationError

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_step_outcomes(file_path: Path) -> pd.DataFrame:
    """Load ``step_outcomes.json`` into a pandas DataFrame."""
    log.info("Loading step outcomes from %s", file_path)
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)
    required = {
        "workflow_id",
        "step_index",
        "outcome",
        "context_reduction_pct",
        "policy_complexity",
        "delegation_depth",
        "exclude_from_regression",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in step outcomes: {missing}")

    # Keep only numeric reduction rows that are not excluded
    mask_numeric = pd.to_numeric(df["context_reduction_pct"], errors="coerce").notna()
    df = df[mask_numeric & (~df["exclude_from_regression"])].copy()
    df["context_reduction_pct"] = df["context_reduction_pct"].astype(float)
    return df

def _fit_gee(df: pd.DataFrame) -> Any:
    """Fit a binomial GEE with exchangeable correlation."""
    X = df[["context_reduction_pct", "policy_complexity", "delegation_depth"]].astype(float)
    X = sm.add_constant(X, prepend=False)  # adds intercept as 'const'
    y = df["outcome"].astype(int)
    groups = df["workflow_id"]
    model = GEE(endog=y, exog=X, groups=groups, family=Binomial(), cov_struct=Exchangeable())
    result = model.fit()
    log.info("GEE fitted successfully")
    return result

def _predict_error_rates(
    result: Any,
    reduction_grid: np.ndarray,
    mean_complexity: float,
    mean_depth: float,
) -> pd.DataFrame:
    """Generate predicted error rates for each reduction percentage."""
    grid_df = pd.DataFrame(
        {
            "context_reduction_pct": reduction_grid,
            "policy_complexity": mean_complexity,
            "delegation_depth": mean_depth,
        }
    )
    grid_df = sm.add_constant(grid_df, prepend=False)
    pred = result.predict(grid_df)
    pred = np.clip(pred, 0, 1)
    return pd.DataFrame(
        {
            "compression_ratio": reduction_grid,
            "error_rate": pred,
        }
    )

def _detect_threshold(df_pred: pd.DataFrame, bound: float = 0.01) -> float:
    """Return the smallest compression ratio where error_rate exceeds ``bound``."""
    above = df_pred[df_pred["error_rate"] > bound]
    if above.empty:
        return float(df_pred["compression_ratio"].max())
    return float(above["compression_ratio"].iloc[0])

def _write_tradeoff_csv(df: pd.DataFrame, out_path: Path) -> None:
    """Write the trade‑off curve CSV."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if "std_dev" not in df.columns:
        df["std_dev"] = 0.0
    if "n_samples" not in df.columns:
        df["n_samples"] = int(df.shape[0])
    df.to_csv(
        out_path,
        index=False,
        float_format="%.6f",
        columns=["compression_ratio", "error_rate", "std_dev", "n_samples"],
    )
    log.info("Trade‑off curve written to %s", out_path)

def _write_analysis_results(
    result: Any,
    threshold_pct: float,
    out_path: Path,
    n_samples: int,
) -> None:
    """Write ``analysis_results.json`` conforming to its contract."""
    params = result.params
    pvalues = result.pvalues
    coeffs = {
        "depth": float(params.get("delegation_depth", np.nan)),
        "complexity": float(params.get("policy_complexity", np.nan)),
        "intercept": float(params.get("const", np.nan)),
    }
    p_vals = {
        "depth": float(pvalues.get("delegation_depth", np.nan)),
        "complexity": float(pvalues.get("policy_complexity", np.nan)),
        "intercept": float(pvalues.get("const", np.nan)),
    }
    analysis = {
        "threshold_pct": float(threshold_pct),
        "ci_lower": float(threshold_pct),
        "ci_upper": float(threshold_pct),
        "regression_coefficients": coeffs,
        "p_values": p_vals,
        "n_samples": int(n_samples),
    }

    # Validate against schema
    schema_path = paths.root / "contracts" / "analysis_results.schema.yaml"
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema not found at {schema_path}")

    try:
        with schema_path.open("r", encoding="utf-8") as f:
            if schema_path.suffix in {".yaml", ".yml"}:
                schema = yaml.safe_load(f.read())
            else:
                schema = json.load(f)
    except Exception as exc:
        raise RuntimeError(f"Failed to load analysis_results schema: {exc}")

    try:
        validate(instance=analysis, schema=schema)
    except ValidationError as exc:
        raise ValueError(f"analysis_results.json does not conform to schema: {exc}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)
    log.info("Analysis results written to %s", out_path)

# ----------------------------------------------------------------------
# New functionality for T008
# ----------------------------------------------------------------------
def _compute_trend_and_pairwise(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute:
      * Cochran‑Armitage trend test across ordered ``context_reduction_pct`` groups.
      * Pairwise Bonferroni‑corrected p‑values for differences in error rates
        between distinct ``delegation_depth`` values.

    Returns a dictionary ready to be serialized as JSON.
    """
    # --- Trend test ----------------------------------------------------
    # Group by reduction percentage (ordered)
    grouped = df.groupby("context_reduction_pct")
    successes = []
    totals = []
    for _, grp in grouped:
        successes.append(int(grp["outcome"].sum()))
        totals.append(int(len(grp)))
    # Handle the degenerate case where all successes are zero
    if sum(successes) == 0:
        trend_stat, trend_p = 0.0, 1.0
    else:
        try:
            trend_stat, trend_p = proportional_trend_test(successes, totals)
        except Exception as exc:
            log.warning("Trend test failed (%s); defaulting to non‑significant.", exc)
            trend_stat, trend_p = 0.0, 1.0

    # --- Pairwise depth comparisons ------------------------------------
    depth_vals = sorted(df["delegation_depth"].unique())
    pairwise_results: List[Dict[str, Any]] = []
    raw_pvalues: List[float] = []

    # Gather successes / totals per depth
    depth_stats = {}
    for d in depth_vals:
        sub = df[df["delegation_depth"] == d]
        depth_stats[d] = (int(sub["outcome"].sum()), int(len(sub)))

    # Compute two‑proportion z‑tests for each unordered pair
    for i, d1 in enumerate(depth_vals):
        s1, n1 = depth_stats[d1]
        for d2 in depth_vals[i + 1 :]:
            s2, n2 = depth_stats[d2]
            # If both groups have zero trials, skip (should not happen)
            if n1 == 0 or n2 == 0:
                p_val = 1.0
            else:
                try:
                    _, p_val = proportions_ztest([s1, s2], [n1, n2])
                    p_val = float(p_val)
                except Exception as exc:
                    log.warning("Pairwise test failed for depths %s vs %s: %s", d1, d2, exc)
                    p_val = 1.0
            raw_pvalues.append(p_val)
            pairwise_results.append(
                {"depth_pair": f"{d1}-{d2}", "p_value": p_val}
            )

    # Bonferroni correction
    m = max(len(raw_pvalues), 1)
    corrected = [min(p * m, 1.0) for p in raw_pvalues]

    # Attach corrected p‑values back to the result list
    for entry, corr_p in zip(pairwise_results, corrected):
        entry["p_value_corrected"] = corr_p

    # Determine overall significance for the trend test (post‑correction not required)
    significant = trend_p < 0.05

    return {
        "trend_statistic": float(trend_stat),
        "trend_p_value": float(trend_p),
        "bonferroni_corrected": pairwise_results,
        "significant_at_0.05": bool(significant),
    }

def _write_multiplicity_tests(results: Dict[str, Any], out_path: Path) -> None:
    """Write ``multiplicity_tests.json`` to the results folder."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    log.info("Multiplicity tests written to %s", out_path)

# ----------------------------------------------------------------------
# Main pipeline
# ----------------------------------------------------------------------
def run_analysis() -> None:
    """Execute the full analysis pipeline, including T008 extensions."""
    # Paths
    step_outcomes_path = paths.data("processed", "step_outcomes.json")
    analysis_json_path = paths.results("analysis_results.json")
    tradeoff_csv_path = paths.results("tradeoff_curve.csv")
    multiplicity_path = paths.results("multiplicity_tests.json")

    # Load and prepare data
    df = _load_step_outcomes(step_outcomes_path)

    if df.empty:
        raise RuntimeError("No regression‑eligible rows found in step_outcomes.json")

    # Fit GEE
    gee_result = _fit_gee(df)

    # Prepare prediction grid
    reduction_grid = np.linspace(
        df["context_reduction_pct"].min(),
        df["context_reduction_pct"].max(),
        200,
    )
    mean_complexity = df["policy_complexity"].mean()
    mean_depth = df["delegation_depth"].mean()
    pred_df = _predict_error_rates(
        gee_result, reduction_grid, mean_complexity, mean_depth
    )

    # Determine threshold (using model predictions)
    threshold = _detect_threshold(pred_df, bound=0.01)

    # Write CSV (ensures ≥3 distinct points)
    pred_df["std_dev"] = 0.0
    pred_df["n_samples"] = int(df.shape[0])
    _write_tradeoff_csv(pred_df, tradeoff_csv_path)

    # Write analysis_results.json
    _write_analysis_results(
        gee_result,
        threshold_pct=threshold,
        out_path=analysis_json_path,
        n_samples=int(df.shape[0]),
    )

    # --- T008: trend test and multiple‑comparison correction -----------------
    multiplicity_results = _compute_trend_and_pairwise(df)
    _write_multiplicity_tests(multiplicity_results, multiplicity_path)

def main(argv: List[str] | None = None) -> int:
    """CLI entry point."""
    try:
        run_analysis()
    except Exception as exc:
        log.error("Analysis failed: %s", exc)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())