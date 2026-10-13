"""Permutation robustness test (Task T006).

Implements FR-007: 1,000 iterations (configurable) of shuffling patient
identifiers while preserving the within‑patient temporal ordering of the
longitudinal ``MDS_UPDRS_Total`` scores. For each iteration the Linear Mixed
Effects model (identical to the one in ``mixed_effects.run_mixed_effects``)
is re‑fit and the interaction p‑values are collected. Empirical p‑values
per taxon are computed as the proportion of permuted p‑values that are
less than or equal to the observed (real‑data) p‑value.

The script respects a 4‑hour wall‑time budget; on breach it aborts
gracefully, writes whatever results have been accumulated, and logs the
breach.

Usage (as part of the pipeline entry point):
    python -m code.src.pipeline.permutation --iterations 1000 --seed 42
    --out data/results/permutation_pvalues.csv
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from llmxive_toolkit import get_logger, paths

# Import internal helpers from the mixed‑effects module.
from . import mixed_effects

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_data(
    clr_path: Path | None = None, clinical_path: Path | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load CLR‑transformed abundances and clinical metadata."""
    clr = mixed_effects._load_clr(clr_path)
    clinical = mixed_effects._load_clinical(clinical_path)
    return clr, clinical


def _permute_clinical(clinical_df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Shuffle whole per‑patient outcome series while keeping covariates.

    The function extracts the ``MDS_UPDRS_Total`` series for each patient,
    shuffles these series across patients, and then re‑attaches them to the
    original rows (preserving visit_date ordering). All other columns
    (age, sex, levodopa_eq_dose, etc.) stay with their original patient.
    """
    # Ensure visit_date is a datetime for correct sorting.
    if not pd.api.types.is_datetime64_any_dtype(clinical_df["visit_date"]):
        clinical_df = clinical_df.copy()
        clinical_df["visit_date"] = pd.to_datetime(clinical_df["visit_date"])

    # Sort for deterministic ordering.
    clinical_df = clinical_df.sort_values(["patient_id", "visit_date"]).reset_index(drop=True)

    # Group outcome series per patient.
    groups = list(clinical_df.groupby("patient_id"))
    outcome_series = [g["MDS_UPDRS_Total"].values for _, g in groups]

    # Shuffle the series.
    rng.shuffle(outcome_series)

    # Re‑assign shuffled series back to the rows.
    permuted = clinical_df.copy()
    for (pid, _), new_series in zip(groups, outcome_series):
        mask = permuted["patient_id"] == pid
        permuted.loc[mask, "MDS_UPDRS_Total"] = new_series

    return permuted


def _fit_interaction_pvalues(
    merged_df: pd.DataFrame, taxon_columns: List[str]
) -> Dict[str, float]:
    """Fit LME for each taxon on ``merged_df`` and return interaction p‑values."""
    pvals: Dict[str, float] = {}
    for taxon in taxon_columns:
        try:
            coef, std_err, pval = mixed_effects._fit_taxon_model(
                merged_df, taxon, outcome_col="MDS_UPDRS_Total"
            )
            pvals[taxon] = pval
        except Exception as exc:
            log.error("Failed to fit taxon %s: %s", taxon, exc)
            pvals[taxon] = float("nan")
    return pvals


# ----------------------------------------------------------------------
# Core permutation routine
# ----------------------------------------------------------------------


def run_permutation(
    iterations: int = 1000,
    seed: int = 42,
    clr_path: Path | None = None,
    clinical_path: Path | None = None,
    out_path: Path | None = None,
    max_wall_seconds: int = 4 * 60 * 60,
) -> Path:
    """Execute the permutation robustness test.

    Parameters
    ----------
    iterations : int
        Number of permutation iterations (default 1000).
    seed : int
        Random seed for reproducibility.
    clr_path, clinical_path : Path | None
        Paths to the CLR‑transformed abundances and clinical metadata.
        If ``None`` the default locations under ``data/processed`` and
        ``data/raw`` are used.
    out_path : Path | None
        Destination CSV file for empirical p‑values. If ``None`` the
        default ``data/results/permutation_pvalues.csv`` is used.
    max_wall_seconds : int
        Hard wall‑time budget for the permutation step (default 4 h).

    Returns
    -------
    Path
        Path to the written CSV file.
    """
    start_time = time.time()
    np_random = np.random.default_rng(seed)

    # Resolve default paths.
    if out_path is None:
        out_path = paths.results("permutation_pvalues.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Load data once.
    clr_df, clinical_df = _load_data(clr_path, clinical_path)

    # Identify taxon columns (those present in CLR data beyond metadata).
    taxon_cols = [
        c
        for c in clr_df.columns
        if c not in ("sample_id", "patient_id", "visit_date")
    ]

    # ------------------------------------------------------------------
    # 1) Compute real (observed) interaction p‑values – needed for empirical
    #    calculation.
    # ------------------------------------------------------------------
    merged_real = clr_df.merge(clinical_df, on=["patient_id", "visit_date"], how="inner")
    real_pvals = _fit_interaction_pvalues(merged_real, taxon_cols)

    # ------------------------------------------------------------------
    # 2) Permutation loop – collect p‑values per taxon.
    # ------------------------------------------------------------------
    permuted_pvals: Dict[str, List[float]] = {taxon: [] for taxon in taxon_cols}

    for i in range(iterations):
        elapsed = time.time() - start_time
        if elapsed > max_wall_seconds:
            log.warning(
                "Permutation wall‑time budget of %.2f seconds exceeded after %d "
                "iterations. Aborting early and writing partial results.",
                max_wall_seconds,
                i,
            )
            break

        # Permute outcome series.
        permuted_clinical = _permute_clinical(clinical_df, np_random)

        # Merge with CLR abundances.
        merged_perm = clr_df.merge(permuted_clinical, on=["patient_id", "visit_date"], how="inner")

        # Fit models for this permutation.
        perm_pvals = _fit_interaction_pvalues(merged_perm, taxon_cols)

        # Store.
        for taxon, pval in perm_pvals.items():
            permuted_pvals[taxon].append(pval)

        if (i + 1) % 50 == 0:
            log.info("Completed %d / %d permutation iterations", i + 1, iterations)

    # ------------------------------------------------------------------
    # 3) Compute empirical p‑values.
    # ------------------------------------------------------------------
    empirical_records = []
    for taxon in taxon_cols:
        perm_vals = np.array(permuted_pvals[taxon])
        # Guard against empty permutation set (e.g., early abort).
        if perm_vals.size == 0:
            emp_p = float("nan")
        else:
            # Proportion of permuted p‑values <= observed p‑value.
            emp_p = (np.sum(perm_vals <= real_pvals[taxon]) + 1) / (len(perm_vals) + 1)
        empirical_records.append({"taxon_name": taxon, "empirical_p": emp_p})

    emp_df = pd.DataFrame(empirical_records)
    emp_df.to_csv(out_path, index=False)

    total_elapsed = time.time() - start_time
    log.info(
        "Permutation test completed (iterations=%d, elapsed=%.2f s). "
        "Results written to %s",
        iterations,
        total_elapsed,
        out_path,
    )
    return out_path


# ----------------------------------------------------------------------
# CLI handling
# ----------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Permutation robustness test for taxon‑outcome associations."
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
        help="Number of permutation iterations (default: 1000).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Path to write empirical p‑values CSV (default: data/results/permutation_pvalues.csv).",
    )
    parser.add_argument(
        "--clr_path",
        type=Path,
        default=None,
        help="Path to CLR‑transformed abundances parquet (default: data/processed/clr_abundances.parquet).",
    )
    parser.add_argument(
        "--clinical_path",
        type=Path,
        default=None,
        help="Path to clinical metadata parquet (default: data/raw/ppmi_clinical.parquet).",
    )
    parser.add_argument(
        "--max_wall_seconds",
        type=int,
        default=4 * 60 * 60,
        help="Maximum wall‑time in seconds (default: 4 h).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        run_permutation(
            iterations=args.iterations,
            seed=args.seed,
            clr_path=args.clr_path,
            clinical_path=args.clinical_path,
            out_path=args.out,
            max_wall_seconds=args.max_wall_seconds,
        )
    except Exception as exc:
        log.error("Permutation test failed: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
