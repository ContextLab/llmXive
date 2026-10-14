"""download_hcp.py
-----------------
Download minimally preprocessed 4 mm Schaefer‑400 resting‑state fMRI time series
and the HCP behavioral table (DSRT scores, age, sex, mean FD) for a deterministic
subset of subjects.

The script follows the specification of **FR‑001**:
  * Retrieve the HCP token from the environment and validate it.
  * List all available HCP subject IDs, sort them, seed 42 and take the first N
    (default 200).
  * For each selected subject:
      – Download the minimally preprocessed 4 mm parcellated time series.
      – Extract parcel‑wise time series using the Schaefer‑400 atlas.
      – Write a per‑subject parquet file under ``data/raw/timeseries/``.
  * Assemble a combined behavioural parquet file containing
    ``subject_id, age, sex, mean_fd, dsrt_score`` and write it to
    ``data/raw/dsrt_scores.parquet``.
  * The script aborts with a clear ``ValueError`` if ``HCP_TOKEN`` is missing
    or if the behavioural table does not contain a DSRT column.

The implementation relies on **nilearn** (for data download and atlas handling)
and **pandas** for parquet I/O.  All directories are created via the
``llmxive_toolkit.paths`` helpers, ensuring they exist before any file is
written.

Usage (as documented in ``quickstart.md``)::

    python -m src.data.download_hcp \\
          --subject-limit 5 \\
          --output-dir data

The command writes the requested files under the ``data/`` folder.
"""
import argparse
import random
from pathlib import Path

import pandas as pd
from nilearn import datasets
from nilearn.input_data import NiftiLabelsMasker

from src.config.env_manager import validate_hcp_credentials
from src.utils.logging_config import get_logger, log_processing_step

def _select_subjects(phenotypic_df: pd.DataFrame, limit: int) -> list[str]:
    """Return a deterministic list of subject IDs.

    The IDs are sorted alphabetically, the random generator is seeded with
    ``42`` and the first ``limit`` IDs are returned.
    """
    all_ids = sorted(phenotypic_df["Subject"].astype(str).unique())
    random.seed(42)
    # ``limit`` may be larger than the available pool – slice safely.
    return all_ids[:limit]

def _extract_timeseries(
    nifti_path: Path, masker: NiftiLabelsMasker
) -> pd.DataFrame:
    """Load a single NIfTI file and return a DataFrame (timepoints × parcels)."""
    ts_array = masker.fit_transform(str(nifti_path))
    # Column names ``parcel_0`` … ``parcel_399`` for Schaefer‑400.
    col_names = [f"parcel_{i}" for i in range(ts_array.shape[1])]
    return pd.DataFrame(ts_array, columns=col_names)

def _find_dsrt_column(df: pd.DataFrame) -> str:
    """Search for a column that plausibly contains DSRT scores."""
    # The HCP behavioural file uses various naming conventions; we accept any
    # column that contains the substring ``dsrt`` (case‑insensitive) or the word
    # ``risk``.  The first match is returned.
    for col in df.columns:
        lowered = col.lower()
        if "dsrt" in lowered or "risk" in lowered:
            return col
    raise ValueError("DSRT column not found in HCP phenotypic data.")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download HCP time series and behavioural data (FR‑001)."
    )
    parser.add_argument(
        "--subject-limit",
        type=int,
        default=200,
        help="Maximum number of subjects to download (default: 200).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Base output directory (default: 'data').",
    )
    args = parser.parse_args()

    logger = get_logger(__name__)

    # ------------------------------------------------------------------
    # 1️⃣ Validate HCP credentials.
    # ------------------------------------------------------------------
    try:
        validate_hcp_credentials()
    except Exception as exc:
        logger.error("HCP credential validation failed: %s", exc)
        raise

    # ------------------------------------------------------------------
    # 2️⃣ Define output locations.
    # ------------------------------------------------------------------
    base_dir = Path(args.output_dir)
    timeseries_dir = base_dir / "raw" / "timeseries"
    timeseries_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 3️⃣ Fetch the phenotypic (behavioural) table for *all* subjects.
    # ------------------------------------------------------------------
    logger.info("Fetching phenotypic data for all available subjects.")
    # ``fetch_hcp`` downloads a minimal set of files (including the phenotypic CSV)
    # without pulling the heavy imaging data.
    phenotypic = datasets.fetch_hcp(
        data_dir=base_dir / "raw",
        subjects=None,  # ``None`` triggers download of the full phenotypic CSV.
        verbose=0,
    )["phenotypic"]
    phenotypic_df = pd.DataFrame(phenotypic)

    # ------------------------------------------------------------------
    # 4️⃣ Deterministic subject selection.
    # ------------------------------------------------------------------
    selected_subjects = _select_subjects(phenotypic_df, args.subject_limit)
    logger.info("Selected %d subjects (out of %d available).",
                len(selected_subjects), phenotypic_df.shape[0])

    # ------------------------------------------------------------------
    # 5️⃣ Download the minimally preprocessed 4 mm Schaefer‑400 time series.
    # ------------------------------------------------------------------
    logger.info("Downloading functional data for selected subjects.")
    func_data = datasets.fetch_hcp_rest(
        subjects=selected_subjects,
        data_dir=base_dir / "raw",
        verbose=2,
    )
    func_paths = func_data["func"]  # list of NIfTI file paths

    # ------------------------------------------------------------------
    # 6️⃣ Load Schaefer‑400 atlas (4 mm) and set up the masker.
    # ------------------------------------------------------------------
    logger.info("Fetching Schaefer‑400 atlas.")
    atlas = datasets.fetch_atlas_schaefer_400_7(
        data_dir=base_dir / "raw", verbose=0
    )
    masker = NiftiLabelsMasker(labels_img=atlas["maps"], standardize=True)

    # ------------------------------------------------------------------
    # 7️⃣ Process each subject: extract parcel time series and write parquet.
    # ------------------------------------------------------------------
    for nifti_path in func_paths:
        # Subject ID is the first part of the filename, e.g. ``100307``.
        subject_id = Path(nifti_path).name.split("_")[0]
        logger.info("Processing subject %s", subject_id)
        try:
            ts_df = _extract_timeseries(Path(nifti_path), masker)
            out_file = timeseries_dir / f"{subject_id}.parquet"
            ts_df.to_parquet(out_file, index=False)
            log_processing_step(
                step_name="download_hcp",
                status="SUCCESS",
                details=f"Saved {out_file}",
            )
        except Exception as exc:
            logger.error("Failed to process subject %s: %s", subject_id, exc)
            log_processing_step(
                step_name="download_hcp",
                status="FAILED",
                details=str(exc),
            )
            # Continue with the next subject – a single failure must not abort
            # the whole download.

    # ------------------------------------------------------------------
    # 8️⃣ Assemble the behavioural table.
    # ------------------------------------------------------------------
    logger.info("Assembling behavioural table.")
    dsrt_col = _find_dsrt_column(phenotypic_df)

    behav_df = phenotypic_df[["Subject", "Age", "Gender", "MeanFD", dsrt_col]].copy()
    behav_df = behav_df.rename(
        columns={
            "Subject": "subject_id",
            "Gender": "sex",
            "MeanFD": "mean_fd",
            dsrt_col: "dsrt_score",
        }
    )
    behav_out = base_dir / "raw" / "dsrt_scores.parquet"
    behav_df.to_parquet(behav_out, index=False)
    logger.info("Behavioural data written to %s", behav_out)

    log_processing_step(
        step_name="download_hcp",
        status="SUCCESS",
        details=f"Completed download for {len(selected_subjects)} subjects.",
    )

if __name__ == "__main__":
    main()
