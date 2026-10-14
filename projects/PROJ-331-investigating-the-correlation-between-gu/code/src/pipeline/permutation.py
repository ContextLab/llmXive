"""Permutation robustness test (Task T006).

Performs block‑wise permutation of patient identifiers while preserving within‑patient
temporal order, re‑fits the mixed‑effects model for each taxon, and records empirical
p‑values.  Results are written to ``results/permutation_pvalues.csv``.
"""
from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path
from typing import List, Tuple, Dict, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from llmxive_toolkit import paths

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

COVARIATE_COLUMNS = ["age", "sex", "levodopa_eq_dose"]


def _load_data(
    clr_path: Optional[Path] = None,
    clinical_path: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load CLR‑transformed abundances and clinical metadata."""
    clr_path = clr_path or paths.data("processed", "clr_abundances.parquet")
    clinical_path = clinical_path or paths.data("raw", "ppmi_clinical.parquet")
    clr = pd.read_parquet(clr_path)
    clinical = pd.read_parquet(clinical_path)

    # Ensure visit_date is datetime in both frames for merging
    clr["visit_date"] = pd.to_datetime(clr["visit_date"])
    clinical["visit_date"] = pd.to_datetime(clinical["visit_date"])
    return clr, clinical


def _prepare_time(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["first_date"] = df.groupby("patient_id")["visit_date"].transform("min")
    df["time_years"] = (df["visit_date"] - df["first_date"]).dt.days / 365.25
    return df


def _encode_sex(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["sex"] = df["sex"].map({"M": 0, "F": 1})
    return df


def _permute_clinical(clinical_df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Shuffle whole per‑patient outcome series while keeping covariates."""
    # Extract the outcome series per patient
    outcome_series = clinical_df[["patient_id", "visit_date", "MDS_UPDRS_Total"]].copy()
    patients = outcome_series["patient_id"].unique()
    shuffled_patients = rng.permutation(patients)
    mapping = dict(zip(patients, shuffled_patients))
    outcome_series["patient_id"] = outcome_series["patient_id"].map(mapping)

    # Re‑attach other covariates (they stay with original patient IDs)
    covariates = clinical_df.drop(columns=["MDS_UPDRS_Total", "visit_date"])
    permuted = outcome_series.merge(covariates, on="patient_id", how="left")
    # Preserve original visit_date ordering (already datetime)
    return permuted


def _detect_zero_variance(df: pd.DataFrame) -> List[str]:
    zero = []
    for col in COVARIATE_COLUMNS:
        if col in df.columns and df[col].nunique(dropna=True) <= 1:
            zero.append(col)
    if zero:
        logger.warning("Zero‑variance covariate(s) will be excluded in permutation: %s", ", ".join(zero))
    return zero


def _fit_interaction_pvalues(
    merged_df: pd.DataFrame, taxon_columns: List[str]
) -> Dict[str, float]:
    """Fit LME for each taxon on the merged dataframe and return interaction p‑values."""
    pvals = {}
    for taxon in taxon_columns:
        try:
            formula = f"MDS_UPDRS_Total ~ time_years * {taxon}"
            # Add remaining covariates if present
            covs = [c for c in COVARIATE_COLUMNS if c in merged_df.columns]
            if covs:
                formula += " + " + " + ".join(covs)
            model = smf.mixedlm(formula, merged_df, groups=merged_df["patient_id"])
            result = model.fit(reml=False)
            term = f"time_years:{taxon}"
            pvals[taxon] = float(result.pvalues[term])
        except Exception as exc:
            logger.error("Failed to fit taxon %s in permutation: %s", taxon, exc)
            pvals[taxon] = np.nan
    return pvals


def run_permutation(
    iterations: int = 1000,
    seed: int = 42,
    clr_path: Optional[Path] = None,
    clinical_path: Optional[Path] = None,
    out_path: Optional[Path] = None,
    max_wall_seconds: int = 4 * 60 * 60,
) -> Path:
    """Execute the permutation robustness test.

    The function writes the empirical p‑values CSV to the ``results`` directory
    (``results/permutation_pvalues.csv``) unless an explicit ``out_path`` is
    provided.
    """
    start_time = time.time()
    # Ensure reproducibility using the global NumPy RNG as specified in the spec
    np.random.seed(seed)
    rng = np.random.default_rng(seed)

    clr, clinical = _load_data(clr_path, clinical_path)

    # Prepare common columns
    clr = _prepare_time(clr)
    clr = _encode_sex(clr)
    clinical = _prepare_time(clinical)
    clinical = _encode_sex(clinical)

    # Detect and drop zero‑variance covariates (both frames)
    zero_covs = _detect_zero_variance(clr)
    if zero_covs:
        clr = clr.drop(columns=zero_covs)
        clinical = clinical.drop(columns=zero_covs)

    taxon_columns = [
        c for c in clr.columns
        if c not in ("sample_id", "patient_id", "visit_date", "time_years", "sex")
    ]
    empirical_counts = {taxon: 0 for taxon in taxon_columns}
    raw_pvals = {}

    # Fit original model to obtain raw p‑values
    merged_orig = clr.merge(clinical, on=["patient_id", "visit_date"], how="inner")
    raw_pvals = _fit_interaction_pvalues(merged_orig, taxon_columns)

    for i in range(iterations):
        if time.time() - start_time > max_wall_seconds:
            logger.warning(
                "Permutation step exceeded wall‑time budget; aborting after %d iterations.", i
            )
            break
        permuted_clinical = _permute_clinical(clinical, rng)
        merged_perm = clr.merge(permuted_clinical, on=["patient_id", "visit_date"], how="inner")
        perm_pvals = _fit_interaction_pvalues(merged_perm, taxon_columns)
        for taxon, p in perm_pvals.items():
            if np.isnan(p):
                continue
            if p <= raw_pvals.get(taxon, np.nan):
                empirical_counts[taxon] += 1

    # Compute empirical p‑values (add‑one smoothing as per standard practice)
    empirical = {
        taxon: (empirical_counts[taxon] + 1) / (iterations + 1) for taxon in taxon_columns
    }
    df_emp = pd.DataFrame(
        {"taxon_name": list(empirical.keys()), "empirical_p": list(empirical.values())}
    )

    # Default location is the ``results`` folder, not ``data/results``.
    out_path = out_path or paths.results("permutation_pvalues.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_emp.to_csv(out_path, index=False)
    logger.info("Permutation results written to %s", out_path)

    total_elapsed = time.time() - start_time
    logger.info("Permutation runtime: %.2f seconds", total_elapsed)
    return out_path


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run permutation robustness test")
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--clr", type=Path, help="Path to CLR parquet")
    parser.add_argument("--clinical", type=Path, help="Path to clinical parquet")
    parser.add_argument("--out", type=Path, help="Output CSV path")
    parser.add_argument("--max_wall_seconds", type=int, default=4 * 60 * 60)
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)
    run_permutation(
        iterations=args.iterations,
        seed=args.seed,
        clr_path=args.clr,
        clinical_path=args.clinical,
        out_path=args.out,
        max_wall_seconds=args.max_wall_seconds,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
