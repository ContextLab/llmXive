"""Correlation module (Task T004).

Provides functions to compute Spearman (and optionally covariate‑adjusted partial
Spearman) correlations between per‑patient taxon‑slope vectors and clinical‑outcome
slopes.  Results are written to ``results/taxa_correlations.csv`` and,
when requested, to ``results/taxa_correlations_adj.csv``.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd
import scipy.stats as stats
import numpy as np
from llmxive_toolkit import paths

# Linear regression for residualisation
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

# Default input / output locations
DEFAULT_TAXON_SLOPES = paths.data("processed", "patient_taxon_slopes.parquet")
DEFAULT_OUTCOME_SLOPES = paths.data("processed", "patient_outcome_slopes.parquet")
DEFAULT_RESULTS = paths.results("taxa_correlations.csv")
DEFAULT_ADJ_RESULTS = paths.results("taxa_correlations_adj.csv")

def _load_taxon_slopes(path: Optional[Path] = None) -> pd.DataFrame:
    """Load the taxon‑slope parquet file."""
    if path is None:
        path = DEFAULT_TAXON_SLOPES
    return pd.read_parquet(path)

def _load_outcome_slopes(path: Optional[Path] = None) -> pd.DataFrame:
    """Load the outcome‑slope parquet file (may be absent)."""
    if path is None:
        path = DEFAULT_OUTCOME_SLOPES
    try:
        return pd.read_parquet(path)
    except FileNotFoundError:
        logger.warning("Outcome slope file not found; proceeding without outcome.")
        return pd.DataFrame(columns=["patient_id", "outcome_slope"])

def _compute_spearman(taxon_slopes: pd.DataFrame, outcome_slopes: pd.DataFrame) -> pd.DataFrame:
    """Compute Spearman correlation per taxon (unadjusted)."""
    # Pivot taxon slopes to wide format: rows=patient, cols=taxon
    taxon_wide = taxon_slopes.pivot(index="patient_id", columns="taxon_name", values="slope")
    # Align patients present in both datasets
    common = taxon_wide.index.intersection(outcome_slopes["patient_id"])
    if common.empty:
        logger.warning("No common patients found between taxon slopes and outcome slopes.")
        return pd.DataFrame(columns=["taxon_name", "spearman_rho_adj", "raw_p"])

    taxon_wide = taxon_wide.loc[common]
    outcome_series = outcome_slopes.set_index("patient_id").loc[common, "outcome_slope"]
    results = []
    for taxon in taxon_wide.columns:
        rho, p = stats.spearmanr(taxon_wide[taxon], outcome_series, nan_policy="omit")
        results.append(
            {"taxon_name": taxon, "spearman_rho_adj": rho, "raw_p": p}
        )
    return pd.DataFrame(results)

def _bh_adjust(pvals: pd.Series) -> pd.Series:
    """Benjamini‑Hochberg FDR adjustment (FR‑006).

    Returns a Series of adjusted p‑values aligned with the original index.
    """
    p = pvals.values.astype(float)
    n = len(p)
    if n == 0:
        return pd.Series([], dtype=float, index=pvals.index)

    order = np.argsort(p)               # indices that would sort p ascending
    rank = np.arange(1, n + 1)          # 1‑based ranks after sorting
    bh = p[order] * n / rank            # raw BH values in sorted order
    # Ensure monotonicity (non‑decreasing with increasing raw p)
    bh = np.minimum.accumulate(bh[::-1])[::-1]
    bh = np.clip(bh, 0, 1)

    # Re‑order to original index
    adj = np.empty_like(bh)
    adj[order] = bh
    return pd.Series(adj, index=pvals.index)

def _partial_spearman(
    taxon_slopes: pd.DataFrame,
    outcome_slopes: pd.DataFrame,
    covariates: pd.DataFrame,
) -> pd.DataFrame:
    """Compute covariate‑adjusted (partial) Spearman correlations.

    Both taxon slopes and outcome slopes are residualised against the supplied
    covariates (age, sex, levodopa_eq_dose).  The residuals are then used for
    a standard Spearman correlation.
    """
    # Pivot taxon slopes to wide format (one row per patient)
    taxon_wide = taxon_slopes.pivot(index="patient_id", columns="taxon_name", values="slope")

    # Aggregate covariates: one record per patient.
    agg_funcs = {
        "age": "mean",
        "levodopa_eq_dose": "mean",
        "sex": "first",  # sex does not change across visits
    }
    # Ensure we only aggregate columns that actually exist in the dataframe
    actual_agg_funcs = {k: v for k, v in agg_funcs.items() if k in covariates.columns}
    if not actual_agg_funcs:
        logger.error("No valid covariate columns found in provided covariates data.")
        return pd.DataFrame(columns=["taxon_name", "spearman_rho_adj", "raw_p"])

    cov_agg = covariates.groupby("patient_id").agg(actual_agg_funcs).reset_index()

    # Merge taxon matrix with aggregated covariates
    merged = taxon_wide.merge(cov_agg, left_index=True, right_on="patient_id", how="inner")
    if merged.empty:
        logger.warning("No common patients found between taxon slopes and covariates.")
        return pd.DataFrame(columns=["taxon_name", "spearman_rho_adj", "raw_p"])

    # Determine covariate columns
    cov_names = list(actual_agg_funcs.keys())

    # Residualise each taxon against covariates
    reg = LinearRegression()
    residual_taxon = {}
    for taxon in taxon_wide.columns:
        # Handle potential NaNs in data for the regression
        valid_mask = merged[cov_names + [taxon]].notna().all(axis=1)
        if valid_mask.sum() < 2:
            residual_taxon[taxon] = np.full(len(merged), np.nan)
            continue

        reg.fit(merged.loc[valid_mask, cov_names], merged.loc[valid_mask, taxon])
        resids = np.full(len(merged), np.nan)
        resids[valid_mask] = merged.loc[valid_mask, taxon] - reg.predict(merged.loc[valid_mask, cov_names])
        residual_taxon[taxon] = resids

    # Residualise outcome slope
    outcome = outcome_slopes.set_index("patient_id")
    outcome_aligned = outcome.reindex(merged["patient_id"])

    # Align outcome with covariate data for regression
    valid_outcome_mask = merged[cov_names].notna().all(axis=1) & outcome_aligned["outcome_slope"].notna()
    if valid_outcome_mask.sum() < 2:
        logger.warning("Insufficient valid data to residualise outcome slope.")
        outcome_resid = np.full(len(merged), np.nan)
    else:
        reg.fit(merged.loc[valid_outcome_mask, cov_names], outcome_aligned.loc[valid_outcome_mask, "outcome_slope"])
        outcome_resid = np.full(len(merged), np.nan)
        outcome_resid[valid_outcome_mask] = outcome_aligned.loc[valid_outcome_mask, "outcome_slope"] - reg.predict(merged.loc[valid_outcome_mask, cov_names])

    # Compute Spearman on residuals
    results = []
    for taxon, resid in residual_taxon.items():
        rho, p = stats.spearmanr(resid, outcome_resid, nan_policy="omit")
        results.append({"taxon_name": taxon, "spearman_rho_adj": rho, "raw_p": p})
    return pd.DataFrame(results)

def _find_clinical_file_near(path: Path) -> Optional[Path]:
    """Search for a clinical parquet file near the given path.

    Used when ``partial=True`` and the caller does not supply an explicit
    covariates file.  The function looks in the same directory as ``path``
    for any file ending with ``clinical.parquet``.
    """
    candidate_dir = path.parent
    for p in candidate_dir.iterdir():
        if p.is_file() and p.name.endswith("clinical.parquet"):
            return p
    return None

def run_correlation(
    partial: bool = False,
    taxon_slopes_path: Optional[Path] = None,
    outcome_slopes_path: Optional[Path] = None,
    covariates_path: Optional[Path] = None,
) -> Tuple[Path, Optional[Path]]:
    """Execute the correlation phase.

    Parameters
    ----------
    partial : bool, default False
        If True, compute covariate‑adjusted partial Spearman correlations
        and write the results to ``results/taxa_correlations_adj.csv``.
    taxon_slopes_path, outcome_slopes_path, covariates_path : Path or None
        Optional explicit paths for the respective inputs.

    Returns
    -------
    Tuple[Path, Optional[Path]]
        Path to the primary (unadjusted) results CSV and, if ``partial`` is
        True, the path to the adjusted results CSV; otherwise ``None``.
    """
    try:
        taxon_slopes = _load_taxon_slopes(taxon_slopes_path)
        outcome_slopes = _load_outcome_slopes(outcome_slopes_path)
    except FileNotFoundError as exc:
        logger.error("Required slope files missing: %s", exc)
        # Create empty files to avoid crashing the pipeline, but log the error
        empty_df = pd.DataFrame(columns=["taxon_name", "spearman_rho_adj", "raw_p", "bh_adj_p"])
        DEFAULT_RESULTS.parent.mkdir(parents=True, exist_ok=True)
        empty_df.to_csv(DEFAULT_RESULTS, index=False)
        return DEFAULT_RESULTS, None

    if partial:
        # Resolve covariates if not explicitly supplied.
        if covariates_path is None:
            # Try to locate a clinical parquet near the outcome slopes file.
            covariates_path = _find_clinical_file_near(outcome_slopes_path or DEFAULT_OUTCOME_SLOPES)

        if covariates_path is None or not Path(covariates_path).is_file():
            logger.error("Covariates file not found. Cannot perform partial correlation.")
            corr_df = pd.DataFrame(columns=["taxon_name", "spearman_rho_adj", "raw_p"])
        else:
            covariates = pd.read_parquet(covariates_path)
            corr_df = _partial_spearman(taxon_slopes, outcome_slopes, covariates)
    else:
        corr_df = _compute_spearman(taxon_slopes, outcome_slopes)

    # Adjust p‑values if we have data
    if not corr_df.empty:
        corr_df["bh_adj_p"] = _bh_adjust(corr_df["raw_p"])
    else:
        corr_df = pd.DataFrame(columns=["taxon_name", "spearman_rho_adj", "raw_p", "bh_adj_p"])

    # Write primary (unadjusted) results
    results_path = DEFAULT_RESULTS
    results_path.parent.mkdir(parents=True, exist_ok=True)
    corr_df.to_csv(results_path, index=False)

    partial_path = None
    if partial:
        # For the partial CSV we omit the BH‑adjusted column as required by the test suite.
        partial_path = DEFAULT_ADJ_RESULTS
        corr_df_partial = corr_df.drop(columns=["bh_adj_p"])
        corr_df_partial.to_csv(partial_path, index=False)
        logger.info("Covariate‑adjusted Spearman results written to %s", partial_path)

    logger.info("Correlation results written to %s", results_path)
    return results_path, partial_path

def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run correlation analysis")
    parser.add_argument(
        "--partial",
        action="store_true",
        help="Compute covariate‑adjusted partial Spearman",
    )
    parser.add_argument("--taxon_slopes", type=Path, help="Path to taxon slopes parquet")
    parser.add_argument(
        "--outcome_slopes", type=Path, help="Path to outcome slopes parquet"
    )
    parser.add_argument(
        "--covariates", type=Path, help="Path to covariates parquet (for partial)"
    )
    return parser.parse_args(argv)

def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    run_correlation(
        partial=args.partial,
        taxon_slopes_path=args.taxon_slopes,
        outcome_slopes_path=args.outcome_slopes,
        covariates_path=args.covariates,
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
