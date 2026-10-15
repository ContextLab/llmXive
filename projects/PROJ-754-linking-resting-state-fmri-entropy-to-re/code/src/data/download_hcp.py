"""
download_hcp.py
----------------
Downloads minimally preprocessed 4 mm Schaefer‑400 resting‑state fMRI time series
for a deterministic subset of HCP subjects and extracts the Domain‑Specific
Risk‑Taking (DSRT) scores together with required covariates.

The script is invoked via ``src.download_data`` which forwards the appropriate
CLI arguments.  All outputs are written under the ``data/`` directory using the
``llmxive_toolkit.paths`` helpers.
"""
import argparse
import logging
from pathlib import Path
from typing import List

import pandas as pd
from nilearn import datasets
from nilearn.input_data import NiftiLabelsMasker

from llmxive_toolkit import paths, get_logger
from src.config.env_manager import (
    get_hcp_token,
    validate_hcp_credentials,
)

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _select_subjects(phenotypic_df: pd.DataFrame, limit: int) -> List[str]:
    """
    Deterministically select ``limit`` subject IDs.

    The IDs are sorted alphabetically, the random generator is seeded with
    ``42`` and the first ``limit`` IDs are returned.
    """
    sorted_ids = sorted(phenotypic_df["subject_id"].astype(str).unique())
    # Seed the Python RNG for reproducibility
    import random

    random.seed(42)
    return sorted_ids[:limit]

def _find_dsrt_column(df: pd.DataFrame) -> str:
    """
    Locate the column that contains DSRT scores.

    The function performs a case‑insensitive search for the substring
    ``dsrt``.  If multiple matches are found, the first one is returned.
    """
    matches = [c for c in df.columns if "dsrt" in c.lower()]
    if not matches:
        raise ValueError("No DSRT column found in behavioural data.")
    return matches[0]

def _extract_timeseries(nifti_path: Path, masker: NiftiLabelsMasker) -> pd.DataFrame:
    """
    Load a NIfTI file, apply the Schaefer‑400 masker and return a
    ``timepoints × parcels`` DataFrame.
    """
    ts = masker.fit_transform(str(nifti_path))
    # Columns are labelled ``parcel_0`` … ``parcel_399`` for consistency
    parcel_names = [f"parcel_{i}" for i in range(ts.shape[1])]
    return pd.DataFrame(ts, columns=parcel_names)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download HCP minimally preprocessed 4 mm Schaefer‑400 time series "
        "and behavioural DSRT scores."
    )
    parser.add_argument(
        "--subject-limit",
        type=int,
        default=200,
        help="Maximum number of subjects to download (deterministic selection).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Base output directory (default: 'data').",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Validate HCP credentials
    # ------------------------------------------------------------------
    try:
        validate_hcp_credentials()
    except Exception as exc:
        logger.error("HCP credential validation failed: %s", exc)
        raise

    token = get_hcp_token()  # accessed only to ensure it exists; nilearn uses env var internally
    logger.debug("Using HCP token (length %d).", len(token))

    output_root = Path(args.output_dir)
    raw_timeseries_dir = paths.data("raw", "timeseries")
    raw_timeseries_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Download behavioural data (includes DSRT, age, sex, mean_fd)
    # ------------------------------------------------------------------
    logger.info("Fetching behavioural data for all available subjects.")
    # ``fetch_hcp_rest`` will use ``HCP_TOKEN`` from the environment.
    behavioural = datasets.fetch_hcp_rest(
        data_dir=str(output_root),
        subjects=None,          # fetch metadata for all subjects
        fetch_behavioral=True,
        fetch_confounds=False,
    )
    behavioural_df = behavioural["behavioural"]
    if not isinstance(behavioural_df, pd.DataFrame):
        raise RuntimeError("Failed to retrieve behavioural DataFrame from HCP.")

    # Ensure required columns exist
    required_cols = {"subject_id", "age", "sex", "mean_fd"}
    missing = required_cols.difference(behavioural_df.columns)
    if missing:
        raise ValueError(f"Missing required behavioural columns: {missing}")

    dsrt_col = _find_dsrt_column(behavioural_df)
    # Keep only the columns we need for downstream steps
    behavioural_df = behavioural_df.rename(columns={dsrt_col: "dsrt_score"})
    behavioural_df = behavioural_df[
        ["subject_id", "age", "sex", "mean_fd", "dsrt_score"]
    ]

    # ------------------------------------------------------------------
    # Deterministically select a subset of subjects
    # ------------------------------------------------------------------
    selected_subjects = _select_subjects(behavioural_df, args.subject_limit)
    logger.info("Selected %d subjects for download.", len(selected_subjects))

    # ------------------------------------------------------------------
    # Fetch the functional data for the selected subjects only
    # ------------------------------------------------------------------
    logger.info("Fetching functional data for selected subjects.")
    func_fetch = datasets.fetch_hcp_rest(
        data_dir=str(output_root),
        subjects=selected_subjects,
        fetch_behavioral=False,
        fetch_confounds=False,
    )
    func_paths = func_fetch["func"]  # list of NIfTI file paths, ordered as ``selected_subjects``

    # ------------------------------------------------------------------
    # Prepare the Schaefer‑400 atlas (4 mm resolution)
    # ------------------------------------------------------------------
    atlas = datasets.fetch_atlas_schaefer_2018(
        n_parcels=400,
        resolution_mm=4,
        yeo_networks=False,
    )
    masker = NiftiLabelsMasker(labels_img=atlas["maps"], standardize=True)

    # ------------------------------------------------------------------
    # Process each subject
    # ------------------------------------------------------------------
    for subj_id, nifti_path in zip(selected_subjects, func_paths):
        logger.info("Processing subject %s", subj_id)
        ts_df = _extract_timeseries(Path(nifti_path), masker)
        out_path = raw_timeseries_dir / f"{subj_id}.parquet"
        ts_df.to_parquet(out_path, index=False)
        logger.debug("Wrote time series parquet to %s", out_path)

    # ------------------------------------------------------------------
    # Write behavioural (DSRT) parquet
    # ------------------------------------------------------------------
    behavioural_out = paths.data("raw", "dsrt_scores.parquet")
    behavioural_out.parent.mkdir(parents=True, exist_ok=True)
    behavioural_df.to_parquet(behavioural_out, index=False)
    logger.info("Behavioural DSRT scores written to %s", behavioural_out)

    logger.info("HCP download step completed successfully.")

if __name__ == "__main__":
    main()
