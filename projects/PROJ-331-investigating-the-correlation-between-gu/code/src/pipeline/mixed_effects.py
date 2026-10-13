"""Linear Mixed‑Effects modeling for gut microbiome taxa (Task T005).

This module fits, for each retained taxon, a mixed‑effects model of the form:

    MDS_UPDRS_Total ~ Time * Taxon + Age + Sex + Levodopa_Dose + (1|Patient)

where:
  * ``Time`` is years since the first visit for each patient,
  * ``Taxon`` is the CLR‑transformed abundance at each timepoint,
  * ``Age``, ``Sex`` and ``Levodopa_Dose`` are covariates,
  * ``(1|Patient)`` denotes a random intercept per patient.

The interaction coefficient (Time × Taxon), its standard error and raw
p‑value are extracted, then Benjamini‑Hochberg FDR correction is applied
across all tested taxa. Results are written to
``data/results/mixed_effects_summary.csv`` with columns:

    taxon_name, interaction_coef, std_error, raw_p, bh_adj_p

If the outcome column ``MDS_UPDRS_Total`` is absent, the step is skipped,
a warning is logged, and an empty CSV (only header) is written.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
from llmxive_toolkit import get_logger, paths
from statsmodels.regression.mixed_linear_model import MixedLM
from statsmodels.stats.multitest import multipletests

log = get_logger(__name__)

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def _load_clr(ab_path: Path | None = None) -> pd.DataFrame:
    """Load the CLR‑transformed abundances (default location)."""
    if ab_path is None:
        ab_path = paths.data("processed", "clr_abundances.parquet")
    df = pd.read_parquet(ab_path)
    required = {"sample_id", "patient_id", "visit_date"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CLR file missing required columns: {missing}")
    return df

def _load_clinical(cl_path: Path | None = None) -> pd.DataFrame:
    """Load the clinical metadata (default location)."""
    if cl_path is None:
        cl_path = paths.data("raw", "ppmi_clinical.parquet")
    df = pd.read_parquet(cl_path)
    return df

def _prepare_time(df: pd.DataFrame) -> pd.DataFrame:
    """Add a ``time_years`` column representing years since first visit per patient."""
    df = df.copy()
    df["visit_date"] = pd.to_datetime(df["visit_date"])
    # Compute first visit per patient
    first = df.groupby("patient_id")["visit_date"].transform("min")
    df["time_years"] = (df["visit_date"] - first).dt.total_seconds() / (365.25 * 24 * 3600)
    return df

def _encode_sex(df: pd.DataFrame) -> pd.DataFrame:
    """Encode ``sex`` as a binary numeric variable (0/1)."""
    df = df.copy()
    if "sex" not in df.columns:
        raise ValueError("Clinical data must contain a 'sex' column.")
    # Simple encoding: male -> 0, female -> 1; any other value raises.
    mapping = {"M": 0, "F": 1}
    if not set(df["sex"]).issubset(mapping.keys()):
        raise ValueError(f"Unexpected values in 'sex' column: {set(df['sex'])}")
    df["sex_num"] = df["sex"].map(mapping)
    return df

# --------------------------------------------------------------------------- #
# Core modeling routine
# --------------------------------------------------------------------------- #
def _fit_taxon_model(
    merged: pd.DataFrame,
    taxon: str,
    outcome_col: str = "MDS_UPDRS_Total",
) -> Tuple[float, float, float]:
    """Fit a MixedLM for a single taxon and return (coef, std_err, pval)."""
    # Build design matrix
    df = merged.copy()
    df["interaction"] = df["time_years"] * df[taxon]

    # Fixed‑effects columns (include intercept automatically)
    exog_cols = [
        "time_years",
        taxon,
        "interaction",
        "age",
        "sex_num",
        "levodopa_eq_dose",
    ]
    exog = df[exog_cols]
    exog = sm.add_constant(exog, has_constant="add")  # type: ignore[attr-defined]

    endog = df[outcome_col]

    # Random intercept per patient
    groups = df["patient_id"]

    model = MixedLM(endog, exog, groups=groups, exog_re=None)
    try:
        result = model.fit(reml=False, method="lbfgs", disp=False)
    except Exception as exc:
        log.error("MixedLM failed for taxon %s: %s", taxon, exc)
        raise

    # Extract interaction term statistics
    coef = result.params["interaction"]
    std_err = result.bse["interaction"]
    t_stat = coef / std_err if std_err != 0 else np.nan
    # Two‑sided p‑value from t‑distribution with large df approximated by normal
    pval = 2 * (1 - stats.norm.cdf(abs(t_stat))) if not np.isnan(t_stat) else np.nan
    return float(coef), float(std_err), float(pval)

def _bh_adjust(pvals: pd.Series) -> pd.Series:
    """Benjamini‑Hochberg FDR adjustment."""
    _, adj_pvals, _, _ = multipletests(pvals, method="fdr_bh")
    return pd.Series(adj_pvals, index=pvals.index)

# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def run_mixed_effects(
    clr_path: Path | None = None,
    clinical_path: Path | None = None,
    out_path: Path | None = None,
) -> Path:
    """Execute the mixed‑effects phase and write the summary CSV.

    Parameters
    ----------
    clr_path, clinical_path, out_path : optional explicit paths.
        If omitted, the default project locations are used.

    Returns
    -------
    Path
        Path to the written CSV file.
    """
    # Load data
    clr_df = _load_clr(clr_path)
    clinical_df = _load_clinical(clinical_path)

    # Verify outcome presence
    outcome_present = "MDS_UPDRS_Total" in clinical_df.columns
    if not outcome_present:
        log.warning(
            "Outcome column 'MDS_UPDRS_Total' missing – LME step will be skipped."
        )
        out_path = out_path or paths.results("mixed_effects_summary.csv")
        # Write empty CSV with header
        pd.DataFrame(
            columns=[
                "taxon_name",
                "interaction_coef",
                "std_error",
                "raw_p",
                "bh_adj_p",
            ]
        ).to_csv(out_path, index=False)
        return out_path

    # Merge CLR abundances with clinical covariates + outcome
    merged = clr_df.merge(
        clinical_df,
        on=["patient_id", "visit_date"],
        how="inner",
    )
    # Prepare time and encode sex
    merged = _prepare_time(merged)
    merged = _encode_sex(merged)

    # Identify taxon columns (exclude known metadata)
    taxon_cols = [
        c
        for c in clr_df.columns
        if c not in {"sample_id", "patient_id", "visit_date"}
    ]

    # Fit model per taxon
    results = []
    for taxon in taxon_cols:
        try:
            coef, se, pval = _fit_taxon_model(merged, taxon)
            results.append(
                {
                    "taxon_name": taxon,
                    "interaction_coef": coef,
                    "std_error": se,
                    "raw_p": pval,
                }
            )
        except Exception as exc:
            log.error("Failed to fit taxon %s: %s", taxon, exc)
            continue

    if not results:
        log.warning("No taxon models were successfully fitted.")
        df_out = pd.DataFrame(
            columns=[
                "taxon_name",
                "interaction_coef",
                "std_error",
                "raw_p",
                "bh_adj_p",
            ]
        )
    else:
        df = pd.DataFrame(results)
        # BH correction across taxa
        df["bh_adj_p"] = _bh_adjust(df["raw_p"])
        # Ensure column order matches contract
        df_out = df[
            [
                "taxon_name",
                "interaction_coef",
                "std_error",
                "raw_p",
                "bh_adj_p",
            ]
        ]

    out_path = out_path or paths.results("mixed_effects_summary.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(out_path, index=False)
    log.info("Mixed‑effects summary written to %s", out_path)
    return out_path

def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    import argparse

    parser = argparse.ArgumentParser(
        description="Run Linear Mixed‑Effects modeling for each taxon."
    )
    parser.add_argument(
        "--clr",
        type=Path,
        help="Path to CLR‑transformed abundances parquet (default data/processed/clr_abundances.parquet).",
    )
    parser.add_argument(
        "--clinical",
        type=Path,
        help="Path to clinical parquet (default data/raw/ppmi_clinical.parquet).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Path to write the results CSV (default data/results/mixed_effects_summary.csv).",
    )
    return parser.parse_args(argv)

def main(argv: List[str] | None = None) -> int:
    """Entry point for ``python -m code.src.pipeline.mixed_effects``."""
    args = _parse_args(argv)
    run_mixed_effects(args.clr, args.clinical, args.out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
