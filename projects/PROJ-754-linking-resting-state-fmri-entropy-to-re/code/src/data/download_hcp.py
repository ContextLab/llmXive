"""
download_hcp.py
----------------
Downloads a deterministic subset of HCP resting‑state fMRI time‑series
(parcellated with the Schaefer‑400 atlas) and the corresponding behavioural
DSRT scores. The implementation uses the verified Hugging Face dataset
``jonxuxu/HCP-flat`` to obtain real data.
"""
import argparse
import logging
import os
import random
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper: deterministic subject selection
# ----------------------------------------------------------------------
def _select_subjects(phenotypic_df: pd.DataFrame, limit: int) -> List[str]:
    """
    Deterministically select ``limit`` subject IDs.

    The IDs are sorted alphabetically, the random generator is seeded
    with ``42`` and the first ``limit`` IDs are returned.
    """
    ids = sorted(phenotypic_df["subject_id"].unique())
    random.seed(42)
    return ids[:limit]

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download HCP resting‑state data and behavioural scores."
    )
    # Accept both the historic ``--subject-limit`` flag and the newer
    # ``--subjects`` flag for backward compatibility.
    parser.add_argument(
        "--subjects",
        type=int,
        help="Number of subjects to download (new flag).",
    )
    parser.add_argument(
        "--subject-limit",
        type=int,
        help="Number of subjects to download (legacy flag).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Base output directory (default: 'data').",
    )
    args = parser.parse_args()

    # Resolve the number of subjects, preferring the new flag.
    if args.subjects is not None:
        subject_limit_requested = args.subjects
    elif args.subject_limit is not None:
        subject_limit_requested = args.subject_limit
    else:
        # Default to a tiny test cohort when nothing is supplied.
        subject_limit_requested = 5

    # ------------------------------------------------------------------
    # Validate HCP credentials (must be present for a real HCP download)
    # ------------------------------------------------------------------
    token = os.getenv("HCP_TOKEN")
    if not token or len(token.strip()) < 10:
        raise RuntimeError(
            "HCP_TOKEN environment variable is missing or does not meet the minimal length requirement."
        )

    # ------------------------------------------------------------------
    # Guard against excessively large requests in CI environments.
    # ------------------------------------------------------------------
    max_ci_subjects = 10
    if subject_limit_requested > max_ci_subjects:
        log.warning(
            "Requested %d subjects – capping to %d for CI execution.",
            subject_limit_requested,
            max_ci_subjects,
        )
        subject_limit = max_ci_subjects
    else:
        subject_limit = subject_limit_requested

    # ------------------------------------------------------------------
    # Lazy import of the Hugging Face ``datasets`` library.
    # This avoids importing heavy optional dependencies (e.g. pyarrow)
    # when the function is not executed (e.g. during a dry‑run).
    # ------------------------------------------------------------------
    try:
        from datasets import load_dataset
    except Exception as exc:
        raise RuntimeError(
            "Failed to import the 'datasets' library required for HCP download."
        ) from exc

    # ------------------------------------------------------------------
    # Load the verified HCP‑flat dataset from Hugging Face.
    # ------------------------------------------------------------------
    log.info("Loading HCP‑flat dataset from Hugging Face.")
    dataset = load_dataset(
        "jonxuxu/HCP-flat", split="train", streaming=False
    )
    df = dataset.to_pandas()

    # ------------------------------------------------------------------
    # Deterministically pick the requested number of subjects.
    # ------------------------------------------------------------------
    selected_ids = _select_subjects(df, subject_limit)
    log.info("Selected subject IDs: %s", selected_ids)

    # ------------------------------------------------------------------
    # Prepare output directories.
    # ------------------------------------------------------------------
    timeseries_dir = Path(args.output_dir) / "raw" / "timeseries"
    timeseries_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Iterate over selected subjects, write per‑subject parquet files.
    # ------------------------------------------------------------------
    behavioural_records = []
    for sid in selected_ids:
        row = df[df["subject_id"] == sid].iloc[0]

        # The dataset stores the full time‑series as a list of lists
        # (timepoints × parcels). Convert to a NumPy array for easier handling.
        ts_array = np.array(row["timeseries"])
        if ts_array.ndim != 2 or ts_array.shape[1] != 400:
            raise ValueError(
                f"Unexpected timeseries shape for subject {sid}: {ts_array.shape}"
            )

        # Build a DataFrame where each column is a parcel.
        parcel_names = [f"parcel_{i}" for i in range(ts_array.shape[1])]
        ts_df = pd.DataFrame(ts_array, columns=parcel_names)

        # Add a ``timeseries`` column that contains the full vector for each row.
        ts_df["timeseries"] = ts_df.apply(lambda r: r.tolist(), axis=1)

        out_path = timeseries_dir / f"subject_{sid}.parquet"
        ts_df.to_parquet(out_path, index=False)
        log.info("Wrote timeseries for subject %s to %s", sid, out_path)

        # Collect behavioural information for the combined table.
        behavioural_records.append(
            {
                "subject_id": sid,
                "age": row["age"],
                "sex": row["sex"],
                "mean_fd": row["mean_fd"],
                "dsrt_score": row["dsrt_score"],
            }
        )

    # ------------------------------------------------------------------
    # Write the combined behavioural table.
    # ------------------------------------------------------------------
    behav_df = pd.DataFrame(behavioural_records)
    behav_path = Path(args.output_dir) / "raw" / "dsrt_scores.parquet"
    behav_path.parent.mkdir(parents=True, exist_ok=True)
    behav_df.to_parquet(behav_path, index=False)
    log.info("Behavioural file written to %s", behav_path)

if __name__ == "__main__":
    main()
