"""Permutation robustness test (Task T006).

Performs block‑wise permutation of patient identifiers while preserving within‑patient
chronological order, re‑fits the mixed‑effects model for each taxon, and records empirical
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
import statsmodels.formula.api as smf
from llmxive_toolkit import paths

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

COVARIATE_COLUMNS = ["age", "sex", "levodopa_eq_dose"]
PSEUDOCOUNT = 1e-6  # Used when we need to compute CLR from raw counts.


def _load_data(
    clr_path: Optional[Path] = None,
    clinical_path: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load CLR‑transformed abundances and clinical metadata.

    If either file does not exist or is empty, an attempt is made to
    reconstruct the missing CLR data from the raw ASV CSV (if available).
    The function returns two DataFrames; if a DataFrame cannot be obtained,
    an empty DataFrame is returned.  The caller will handle the empty case
    by writing an empty results file, preserving the defensive behaviour
    required by the specification.
    """
    # Resolve default locations.
    clr_path = clr_path or paths.data("processed", "clr_abundances.parquet")
    clinical_path = clinical_path or _resolve_clinical_default()

    # Load clinical data – this is mandatory for the permutation test.
    if not clinical_path.is_file():
        logger.error("Clinical data file not found at %s", clinical_path)
        return pd.DataFrame(), pd.DataFrame()
    clinical = pd.read_parquet(clinical_path)
    clinical["visit_date"] = pd.to_datetime(clinical["visit_date"])

    # Load CLR data; if missing or empty, try to reconstruct from raw ASV.
    if clr_path.is_file():
        clr = pd.read_parquet(clr_path)
        if not clr.empty:
            clr["visit_date"] = pd.to_datetime(clr["visit_date"])
            return clr, clinical

    # Attempt reconstruction from raw ASV CSV in the same directory as the clinical file.
    logger.warning("CLR file missing or empty; attempting reconstruction from raw ASV CSV.")
    asv_path = _find_asv_csv_near(clinical_path)
    if asv_path is None or not asv_path.is_file():
        logger.error("Unable to locate raw ASV CSV to reconstruct CLR data.")
        return pd.DataFrame(), clinical

    asv = pd.read_csv(asv_path)
    # Basic validation – ensure required identifier columns exist.
    required_cols = {"sample_id", "patient_id", "visit_date"}
    if not required_cols.issubset(set(asv.columns)):
        logger.error("Raw ASV CSV missing required columns: %s", required_cols - set(asv.columns))
        return pd.DataFrame(), clinical

    # Identify taxon count columns.
    taxon_cols = [c for c in asv.columns if c not in required_cols]
    if not taxon_cols:
        logger.error("No taxon columns found in raw ASV CSV.")
        return pd.DataFrame(), clinical

    # CLR transformation.
    counts = asv[taxon_cols].astype(float) + PSEUDOCOUNT
    # Geometric mean per sample.
    gm = np.exp(np.log(counts).mean(axis=1))
    clr_vals = np.log(counts.div(gm, axis=0))
    clr = asv[["sample_id", "patient_id", "visit_date"]].copy()
    clr[taxon_cols] = clr_vals
    clr["visit_date"] = pd.to_datetime(clr["visit_date"])
    # Optionally write the reconstructed CLR file for downstream reuse.
    try:
        clr_path.parent.mkdir(parents=True, exist_ok=True)
        clr.to_parquet(clr_path)
        logger.info("Reconstructed CLR data written to %s", clr_path)
    except Exception as exc:
        logger.warning("Failed to write reconstructed CLR parquet: %s", exc)
    return clr, clinical


def _resolve_clinical_default() -> Path:
    """Return the default clinical parquet path (historic or open‑data)."""
    raw_dir = paths.data("raw")
    ppmi = raw_dir / "ppmi_clinical.parquet"
    openp = raw_dir / "open_clinical.parquet"
    if ppmi.is_file():
        return ppmi
    if openp.is_file():
        return openp
    # If neither exists, return a path that will trigger the missing‑file handling.
    return raw_dir / "clinical.parquet"


def _find_asv_csv_near(clinical_path: Path) -> Optional[Path]:
    """Search for an ASV CSV file in the same directory as the clinical file.

    The function looks for files ending with ``_asv.csv`` (e.g. ``ppmi_asv.csv``
    or ``open_asv.csv``).  Returns the first match or ``None`` if no file is found.
    """
    dir_ = clinical_path.parent
    for candidate in dir_.glob("*_asv.csv"):
        return candidate
    return None


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
    """Shuffle whole‑patient outcome series while keeping covariates.

    The permutation is performed by shuffling the ``patient_id`` column
    across rows, leaving the order of rows (and thus the temporal order
    within each original patient) untouched.  This guarantees that each
    patient’s internal visit chronology is preserved.
    """
    df = clinical_df.copy()
    unique_ids = df["patient_id"].unique()
    shuffled_ids = rng.permutation(unique_ids)
    mapping = dict(zip(unique_ids, shuffled_ids))
    df["patient_id"] = df["patient_id"].map(mapping)
    return df


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
    provided.  If the required input files are missing, an empty CSV with the
    correct header is written so that downstream pipeline stages can continue
    without raising uncaught exceptions.
    """
    start_time = time.time()
    np.random.seed(seed)
    rng = np.random.default_rng(seed)

    clr, clinical = _load_data(clr_path, clinical_path)

    # If either DataFrame is empty, write an empty results file and exit early.
    if clr.empty or clinical.empty:
        out_path = out_path or paths.results("permutation_pvalues.csv")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=["taxon_name", "empirical_p"]).to_csv(out_path, index=False)
        logger.info("Empty permutation results written to %s (missing input data)", out_path)
        return out_path

    # Prepare common columns.
    clr = _prepare_time(clr)
    clr = _encode_sex(clr)
    clinical = _prepare_time(clinical)
    clinical = _encode_sex(clinical)

    # Detect and drop zero‑variance covariates (both frames).
    zero_covs = _detect_zero_variance(clr)
    if zero_covs:
        clr = clr.drop(columns=zero_covs)
        clinical = clinical.drop(columns=zero_covs)

    taxon_columns = [
        c
        for c in clr.columns
        if c not in ("sample_id", "patient_id", "visit_date", "time_years", "sex")
    ]
    if not taxon_columns:
        logger.error("No taxon columns detected after preprocessing; aborting permutation.")
        out_path = out_path or paths.results("permutation_pvalues.csv")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=["taxon_name", "empirical_p"]).to_csv(out_path, index=False)
        return out_path

    empirical_counts = {taxon: 0 for taxon in taxon_columns}
    # Fit original model to obtain raw p‑values.
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

    # Compute empirical p‑values (add‑one smoothing).
    empirical = {
        taxon: (empirical_counts[taxon] + 1) / (iterations + 1) for taxon in taxon_columns
    }
    df_emp = pd.DataFrame(
        {"taxon_name": list(empirical.keys()), "empirical_p": list(empirical.values())}
    )

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
    parser.add_argument("--clr", type=Path, help="Path to the CLR‑transformed abundances Parquet file "
                                                 "(default: data/processed/clr_abundances.parquet)")
    parser.add_argument("--clinical", type=Path, help="Path to the clinical metadata Parquet file "
                                                     "(default: data/raw/ppmi_clinical.parquet or open_clinical.parquet)")
    parser.add_argument("--out", type=Path, help="Output CSV path (default: results/permutation_pvalues.csv)")
    parser.add_argument("--max_wall_seconds", type=int, default=4 * 60 * 60,
                        help="Maximum wall‑clock time for the whole permutation block (default: 4 hours)")
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