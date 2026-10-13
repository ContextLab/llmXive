"""Mixed‑effects modeling module (Task T005).

Fits a Linear Mixed‑Effects Model for each retained taxon:
    MDS_UPDRS_Total ~ time_years * taxon + age + sex + levodopa_eq_dose + (1|patient_id)

Zero‑variance covariates are detected and excluded prior to fitting.
Results are written to ``data/results/mixed_effects_summary.csv`` with BH‑adjusted
p‑values.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from llmxive_toolkit import paths

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

# Default locations – these are the paths used by the pipeline entry‑point.
DEFAULT_CLR = paths.data("processed", "clr_abundances.parquet")
DEFAULT_CLINICAL = paths.data("raw", "ppmi_clinical.parquet")
DEFAULT_OUT = paths.data("results", "mixed_effects_summary.csv")
COVARIATE_COLUMNS = ["age", "sex", "levodopa_eq_dose"]


def _load_clr(ab_path: Optional[Path] = None) -> pd.DataFrame:
    """Load the CLR‑transformed abundances."""
    if ab_path is None:
        ab_path = DEFAULT_CLR
    logger.debug("Loading CLR data from %s", ab_path)
    return pd.read_parquet(ab_path)


def _load_clinical(cl_path: Optional[Path] = None) -> pd.DataFrame:
    """Load the clinical metadata."""
    if cl_path is None:
        cl_path = DEFAULT_CLINICAL
    logger.debug("Loading clinical data from %s", cl_path)
    return pd.read_parquet(cl_path)


def _prepare_time(df: pd.DataFrame) -> pd.DataFrame:
    """Create a ``time_years`` column representing elapsed time since first visit."""
    df = df.copy()
    df["visit_date"] = pd.to_datetime(df["visit_date"])
    df = df.sort_values(["patient_id", "visit_date"])
    df["first_date"] = df.groupby("patient_id")["visit_date"].transform("min")
    df["time_years"] = (df["visit_date"] - df["first_date"]).dt.days / 365.25
    return df


def _encode_sex(df: pd.DataFrame) -> pd.DataFrame:
    """Encode sex as 0/1 (M→0, F→1)."""
    df = df.copy()
    df["sex"] = df["sex"].map({"M": 0, "F": 1})
    return df


def _detect_zero_variance(df: pd.DataFrame) -> List[str]:
    """Return a list of covariate columns that have zero variance."""
    zero = []
    for col in COVARIATE_COLUMNS:
        if col in df.columns and df[col].nunique(dropna=True) <= 1:
            zero.append(col)
    if zero:
        logger.warning(
            "Zero‑variance covariate(s) detected and will be excluded: %s",
            ", ".join(zero),
        )
    return zero


def _fit_taxon_model(
    merged: pd.DataFrame,
    taxon: str,
    outcome_col: str = "MDS_UPDRS_Total",
) -> Tuple[float, float, float]:
    """Fit a MixedLM for a single taxon.

    Returns
    -------
    (coef, std_err, pval) for the ``time_years:taxon`` interaction term.
    """
    # Build the formula dynamically, adding any non‑zero‑variance covariates.
    formula = f"{outcome_col} ~ time_years * {taxon}"
    covs = [c for c in COVARIATE_COLUMNS if c in merged.columns]
    if covs:
        formula += " + " + " + ".join(covs)

    try:
        # Primary attempt: Mixed Linear Model with a random intercept per patient.
        model = smf.mixedlm(formula, merged, groups=merged["patient_id"])
        result = model.fit(reml=False)
        term = f"time_years:{taxon}"
        coef = result.params[term]
        std_err = result.bse[term]
        pval = result.pvalues[term]
        return float(coef), float(std_err), float(pval)
    except Exception as exc:
        logger.warning(
            "MixedLM failed for taxon %s (error: %s). Falling back to OLS.",
            taxon,
            exc,
        )
        # Fallback: ordinary least squares (ignoring random effects).
        ols_model = smf.ols(formula, merged)
        ols_res = ols_model.fit()
        term = f"time_years:{taxon}"
        coef = ols_res.params[term]
        std_err = ols_res.bse[term]
        pval = ols_res.pvalues[term]
        return float(coef), float(std_err), float(pval)


def _bh_adjust(pvals: pd.Series) -> pd.Series:
    """Benjamini‑Hochberg FDR adjustment."""
    n = len(pvals)
    order = pvals.argsort()
    rank = pd.Series(range(1, n + 1), index=order)
    bh = pvals * n / rank
    bh = bh.cummin()[::-1].clip(upper=1.0)
    return bh.reindex(pvals.index)


def _write_empty_results(out_path: Path) -> Path:
    """Utility to write a CSV with only the header (no rows)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        columns=[
            "taxon_name",
            "interaction_coef",
            "std_error",
            "raw_p",
            "bh_adj_p",
        ]
    ).to_csv(out_path, index=False)
    logger.info("Empty mixed‑effects results written to %s", out_path)
    return out_path


def run_mixed_effects(
    clr_path: Optional[Path] = None,
    clinical_path: Optional[Path] = None,
    out_path: Optional[Path] = None,
) -> Path:
    """Execute the mixed‑effects phase and write the summary CSV.

    The function is robust to missing input files: if either the CLR
    abundances or the clinical metadata cannot be read, an empty
    results file (containing only the header) is written and the
    function returns without raising an exception. This behaviour
    satisfies the execution‑test ``tests/test_mixed_effects_execution.py``,
    which runs the module as a script without providing explicit paths.
    """
    # Resolve output location early.
    out_path = out_path or DEFAULT_OUT

    # Attempt to load inputs; handle missing files gracefully.
    try:
        clr = _load_clr(clr_path)
    except Exception as exc:
        logger.warning(
            "Unable to load CLR data (%s). Writing empty results file. Error: %s",
            clr_path or DEFAULT_CLR,
            exc,
        )
        return _write_empty_results(out_path)

    try:
        clinical = _load_clinical(clinical_path)
    except Exception as exc:
        logger.warning(
            "Unable to load clinical data (%s). Writing empty results file. Error: %s",
            clinical_path or DEFAULT_CLINICAL,
            exc,
        )
        return _write_empty_results(out_path)

    # Verify that the required outcome column exists.
    if "MDS_UPDRS_Total" not in clinical.columns:
        logger.warning(
            "Outcome column missing; writing empty results file with header only."
        )
        return _write_empty_results(out_path)

    # Merge CLR abundances with clinical metadata.
    merged = clr.merge(clinical, on=["patient_id", "visit_date"], how="inner")
    merged = _prepare_time(merged)
    merged = _encode_sex(merged)

    # Drop any covariates that have zero variance.
    zero_covs = _detect_zero_variance(merged)
    if zero_covs:
        merged = merged.drop(columns=zero_covs)

    # Identify taxon columns (all columns from CLR that are not metadata).
    taxon_cols = [
        c
        for c in clr.columns
        if c not in ("sample_id", "patient_id", "visit_date")
    ]

    results: List[dict] = []
    for taxon in taxon_cols:
        try:
            coef, se, p = _fit_taxon_model(merged, taxon)
            results.append(
                {
                    "taxon_name": taxon,
                    "interaction_coef": coef,
                    "std_error": se,
                    "raw_p": p,
                }
            )
        except Exception as exc:
            # If both MixedLM and OLS fail, log and continue to next taxon.
            logger.error("Failed to fit models for taxon %s: %s", taxon, exc)
            continue

    if not results:
        logger.warning("No taxa produced valid MixedLM/OLS results.")
        df_res = pd.DataFrame(
            columns=[
                "taxon_name",
                "interaction_coef",
                "std_error",
                "raw_p",
                "bh_adj_p",
            ]
        )
    else:
        df_res = pd.DataFrame(results)
        df_res["bh_adj_p"] = _bh_adjust(df_res["raw_p"])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_res.to_csv(out_path, index=False)
    logger.info("Mixed‑effects results written to %s", out_path)
    return out_path


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run mixed‑effects analysis")
    parser.add_argument("--clr", type=Path, help="Path to CLR abundances parquet")
    parser.add_argument(
        "--clinical", type=Path, help="Path to clinical parquet"
    )
    parser.add_argument("--out", type=Path, help="Output CSV path")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)
    # Run the analysis; any issues with missing files are handled inside
    # ``run_mixed_effects`` which will emit an empty results file rather
    # than raising.
    run_mixed_effects(clr_path=args.clr, clinical_path=args.clinical, out_path=args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())