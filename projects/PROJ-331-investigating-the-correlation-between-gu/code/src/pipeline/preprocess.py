"""Filtering and CLR transformation of PPMI ASV + clinical data (Task T002).

Loads the researcher‑supplied raw inputs from ``data/raw/``, merges the ASV
and clinical tables on ``patient_id`` + ``visit_date``, retains PD patients
with >= 2 visits (FR‑002, logging the excluded‑subject count), drops
all‑zero taxa with a warning, adds a pseudocount of 1e‑6 and applies the
centered log‑ratio (CLR) transformation via **scikit‑bio** (FR‑003), detects zero‑variance
covariates and logs a warning (they are flagged for exclusion downstream),
and subsamples to the top 100 most abundant taxa if the modeling feature
set would exceed 7 GB of RAM (FR‑010).

Outputs:
  data/processed/filtered_samples.parquet  -- merged, filtered long table
  data/processed/clr_abundances.parquet    -- CLR‑transformed taxa table
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# scikit‑bio provides a robust CLR implementation that respects compositional
# data principles. It raises clear errors if non‑positive values are passed,
# so we add a small pseudocount beforehand.
try:
    from skbio.stats.composition import clr as sbio_clr
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "scikit‑bio is required for CLR transformation. Install it via "
        "`pip install scikit-bio`."
    ) from exc

# Allow both `python -m code.src.pipeline.preprocess` and package imports.
try:
    from code.src.pipeline import ingest  # noqa: F401  (provenance of raw files)
except ImportError:  # pragma: no cover - direct‑script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from code.src.pipeline import ingest  # noqa: F401

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

METADATA_COLUMNS = [
    "patient_id",
    "visit_date",
    "age",
    "sex",
    "levodopa_eq_dose",
    "MDS_UPDRS_Total",
]
COVARIATE_COLUMNS = ["age", "sex", "levodopa_eq_dose"]
PSEUDOCOUNT = 1e-6
RAM_BUDGET_BYTES = 7 * 1024**3
MAX_TAXA = 100


def _project_root() -> Path:
    """Return the project root (directory containing ``data/``)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "data" / "raw").is_dir():
            return parent
    # Fall back to the repository layout convention.
    return here.parents[3]


def load_raw_tables(
    asv_path: Optional[Path] = None,
    clinical_path: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """Load the raw ASV and clinical tables from ``data/raw/``.

    The function first tries the historic PPMI filenames
    ``ppmi_asv.csv`` / ``ppmi_clinical.parquet``.  If they are not
    present it falls back to the open‑dataset filenames
    ``open_asv.csv`` / ``open_clinical.parquet``.  A ``FileNotFoundError``
    is raised only when **neither** file exists.

    Returns (asv_df, clinical_df, taxon_columns). Raises
    ``FileNotFoundError`` with a descriptive message if both candidates
    are missing – never falls back to synthetic data.
    """
    root = _project_root()

    # Resolve ASV path
    if asv_path is None:
        primary = root / "data" / "raw" / "ppmi_asv.csv"
        alternate = root / "data" / "raw" / "open_asv.csv"
        if primary.is_file():
            asv_path = primary
        elif alternate.is_file():
            asv_path = alternate
        else:
            raise FileNotFoundError(
                f"Required ASV input not found: {primary} nor {alternate}. "
                "Supply a real ASV table (columns sample_id, patient_id, "
                "visit_date, taxon count columns)."
            )
    else:
        asv_path = Path(asv_path)

    # Resolve clinical path
    if clinical_path is None:
        primary = root / "data" / "raw" / "ppmi_clinical.parquet"
        alternate = root / "data" / "raw" / "open_clinical.parquet"
        if primary.is_file():
            clinical_path = primary
        elif alternate.is_file():
            clinical_path = alternate
        else:
            raise FileNotFoundError(
                f"Required clinical input not found: {primary} nor {alternate}. "
                "Supply a real clinical metadata file."
            )
    else:
        clinical_path = Path(clinical_path)

    # Load files
    asv_df = pd.read_csv(asv_path)
    clinical_df = pd.read_parquet(clinical_path)

    # Basic column validation
    for col in ("sample_id", "patient_id", "visit_date"):
        if col not in asv_df.columns:
            raise ValueError(f"ASV table is missing required column '{col}'.")
    for col in ("patient_id", "visit_date"):
        if col not in clinical_df.columns:
            raise ValueError(f"Clinical table is missing required column '{col}'.")

    taxon_columns = [
        c
        for c in asv_df.columns
        if c not in ("sample_id", "patient_id", "visit_date")
    ]
    if not taxon_columns:
        raise ValueError("ASV table contains no taxon count columns.")

    logger.info(
        "Loaded ASV table: %d rows, %d taxa; clinical table: %d rows, %d cols",
        len(asv_df),
        len(taxon_columns),
        len(clinical_df),
        clinical_df.shape[1],
    )
    return asv_df, clinical_df, taxon_columns


def merge_and_filter(
    asv_df: pd.DataFrame,
    clinical_df: pd.DataFrame,
    taxon_columns: List[str],
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """Merge on patient_id + visit_date and retain PD patients with >=2 visits.

    Returns (merged_df, stats) where stats records cohort counts for the
    pipeline log (FR‑002).
    """
    merged = asv_df.merge(clinical_df, on=["patient_id", "visit_date"], how="inner")
    n_merged = len(merged)
    visit_counts = merged.groupby("patient_id")["visit_date"].nunique()
    retained_patients = visit_counts[visit_counts >= 2].index
    excluded = visit_counts[visit_counts < 2]
    merged = merged[merged["patient_id"].isin(retained_patients)].reset_index(drop=True)
    stats = {
        "merged_rows": int(n_merged),
        "total_patients": int(visit_counts.shape[0]),
        "excluded_subjects": int(excluded.shape[0]),
        "retained_patients": int(len(retained_patients)),
        "retained_rows": int(len(merged)),
    }
    if excluded.shape[0] > 0:
        logger.warning(
            "FR-002: excluded %d subject(s) with fewer than 2 visits; "
            "%d patient(s) retained (%d sample rows)",
            stats["excluded_subjects"],
            stats["retained_patients"],
            stats["retained_rows"],
        )
    else:
        logger.info("FR-002: all %d patients have >=2 visits", stats["retained_patients"])
    return merged, stats


def drop_zero_taxa(
    merged: pd.DataFrame, taxon_columns: List[str]
) -> Tuple[pd.DataFrame, List[str]]:
    """Drop taxa whose counts are zero across all retained samples (warning)."""
    zero_taxa = [t for t in taxon_columns if (merged[t] == 0).all()]
    if zero_taxa:
        logger.warning(
            "Dropping %d all-zero taxon(a) prior to CLR: %s",
            len(zero_taxa),
            ", ".join(zero_taxa[:20]) + ("..." if len(zero_taxa) > 20 else ""),
        )
    kept = [t for t in taxon_columns if t not in zero_taxa]
    if not kept:
        raise ValueError("All taxa are all-zero after filtering; cannot proceed.")
    return merged, kept


def _cap_impl(
    merged: pd.DataFrame, taxon_columns: List[str], max_taxa: int
) -> List[str]:
    """Internal helper: select the top‑N most abundant taxa by total counts."""
    abundance = merged[taxon_columns].sum().sort_values(ascending=False)
    top = list(abundance.head(max_taxa).index)
    return top


def cap_taxa_by_memory(
    merged: pd.DataFrame, taxon_columns: List[str], max_taxa: int = MAX_TAXA
) -> List[str]:
    """Subsample to the top‑N most abundant taxa if RAM budget would be exceeded (FR‑010)."""
    n_rows = len(merged)
    estimated_bytes = n_rows * len(taxon_columns) * 8  # float64 modeling matrix
    if estimated_bytes <= RAM_BUDGET_BYTES:
        logger.info(
            "Feature set (%d rows x %d taxa, ~%.2f GB) within 7 GB budget; no subsampling",
            n_rows,
            len(taxon_columns),
            estimated_bytes / 1024**3,
        )
        return taxon_columns
    # Memory would be exceeded – select top taxa.
    top = _cap_impl(merged, taxon_columns, max_taxa)
    logger.warning(
        "FR-010: estimated %.2f GB exceeds 7 GB RAM budget; subsampling to the "
        "top %d most abundant taxa",
        estimated_bytes / 1024**3,
        len(top),
    )
    return top


def clr_transform(counts: pd.DataFrame, pseudocount: float = PSEUDOCOUNT) -> pd.DataFrame:
    """Apply the centered log‑ratio transformation using scikit‑bio.

    The function adds a small pseudocount to avoid log‑zero issues,
    then delegates to ``skbio.stats.composition.clr`` which computes
    ``log(x) - mean(log(x))`` row‑wise.  The returned DataFrame retains
    the original column names and index.
    """
    # Ensure we work with floating point numbers and add the pseudocount.
    counts_pc = counts.astype(float) + pseudocount
    # scikit‑bio operates on a NumPy array.
    transformed = sbio_clr(counts_pc.values)
    # Preserve the original DataFrame shape and column labels.
    return pd.DataFrame(transformed, index=counts.index, columns=counts.columns)


def detect_zero_variance_covariates(merged: pd.DataFrame) -> List[str]:
    """Detect zero‑variance covariates and log a warning; return them for exclusion."""
    zero_var = []
    for col in COVARIATE_COLUMNS:
        if col in merged.columns:
            if merged[col].dropna().nunique() <= 1:
                zero_var.append(col)
    if zero_var:
        logger.warning(
            "Zero‑variance covariate(s) detected and flagged for model exclusion: %s",
            ", ".join(zero_var),
        )
    return zero_var


def run_preprocess(
    asv_path: Optional[Path] = None,
    clinical_path: Optional[Path] = None,
    out_dir: Optional[Path] = None,
    max_taxa: int = MAX_TAXA,
) -> Dict[str, object]:
    """Execute the full preprocessing phase and write the processed parquet files."""
    asv_df, clinical_df, taxon_columns = load_raw_tables(asv_path, clinical_path)
    merged, stats = merge_and_filter(asv_df, clinical_df, taxon_columns)
    merged, taxon_columns = drop_zero_taxa(merged, taxon_columns)
    taxon_columns = cap_taxa_by_memory(merged, taxon_columns, max_taxa)
    zero_var_covariates = detect_zero_variance_covariates(merged)

    root = _project_root()
    out_dir = Path(out_dir) if out_dir else root / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)

    filtered_path = out_dir / "filtered_samples.parquet"
    clr_path = out_dir / "clr_abundances.parquet"

    # filtered_samples: metadata + retained raw taxon counts (one row per sample)
    meta_cols = [c for c in METADATA_COLUMNS if c in merged.columns]
    extra = [c for c in merged.columns if c not in meta_cols + taxon_columns]
    filtered = merged[meta_cols + extra + taxon_columns].copy()
    filtered.to_parquet(filtered_path, index=False)

    # clr_abundances: keys + CLR‑transformed taxa
    clr = clr_transform(merged[taxon_columns])
    clr_out = merged[["sample_id", "patient_id", "visit_date"]].copy()
    clr_out = pd.concat([clr_out, clr], axis=1)
    clr_out.to_parquet(clr_path, index=False)

    summary = {
        "filtered_samples_path": str(filtered_path),
        "clr_abundances_path": str(clr_path),
        "cohort_stats": stats,
        "n_taxa_retained": len(taxon_columns),
        "taxa_retained": taxon_columns,
        "zero_variance_covariates": zero_var_covariates,
        "outcome_present": "MDS_UPDRS_Total" in merged.columns,
        "clr_rows": int(len(clr_out)),
    }
    logger.info(
        "Preprocessing complete: %d retained samples, %d taxa, CLR rows=%d; "
        "outputs written to %s",
        stats["retained_rows"],
        len(taxon_columns),
        len(clr_out),
        out_dir,
    )
    return summary


def main() -> int:
    """Entry point for ``python -m code.src.pipeline.preprocess``."""
    summary = run_preprocess()
    stats = summary["cohort_stats"]
    logger.info(
        "Summary: merged_rows=%d excluded_subjects=%d retained_patients=%d "
        "retained_rows=%d n_taxa=%d zero_var_covariates=%s",
        stats["merged_rows"],
        stats["excluded_subjects"],
        stats["retained_patients"],
        stats["retained_rows"],
        summary["n_taxa_retained"],
        summary["zero_variance_covariates"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
