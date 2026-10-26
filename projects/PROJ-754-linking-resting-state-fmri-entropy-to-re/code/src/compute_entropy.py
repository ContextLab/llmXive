"""
compute_entropy.py
------------------
Reads the cleaned subject table, loads each subject's parcel‑wise
time‑series, computes multiscale sample entropy using the implementation
in ``src.analysis.entropy``, and writes two artefacts:

  * ``data/derived/entropy_matrix.parquet`` – long‑format table
    (subject_id, parcel_id, entropy, checksum)
  * ``data/derived/invalid_parcels.csv`` – parcels that could not be
    processed (written by ``src.analysis.entropy``).

The script processes parcels in batches (default ≤ 50) to keep peak RAM
below the 4 GB limit.
"""
import argparse
import hashlib
from pathlib import Path

import pandas as pd

from llmxive_toolkit import get_logger, paths
from src.analysis.entropy import multiscale_entropy

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper: batch iterator
# ----------------------------------------------------------------------
def _batch_iter(seq, batch_size):
    """Yield successive batches from *seq* of size *batch_size*."""
    for i in range(0, len(seq), batch_size):
        yield seq[i : i + batch_size]

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute multiscale entropy matrix for a cohort."
    )
    parser.add_argument(
        "--input",
        required=True,
        help=(
            "Path to the cleaned subjects parquet (data/derived/clean_subjects.parquet)."
        ),
    )
    parser.add_argument(
        "--output",
        required=True,
        help=(
            "Path to write the entropy matrix parquet "
            "(data/derived/entropy_matrix.parquet)."
        ),
    )
    parser.add_argument(
        "--scales",
        nargs="+",
        type=int,
        default=[1, 2, 3, 4, 5],
        help="Scale factors for multiscale entropy.",
    )
    parser.add_argument(
        "--m",
        type=int,
        default=2,
        help="Embedding dimension for sample entropy.",
    )
    parser.add_argument(
        "--r",
        type=float,
        default=0.15,
        help="Tolerance for sample entropy (fraction of std).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Maximum number of parcels processed simultaneously.",
    )
    args = parser.parse_args()

    logger = get_logger(__name__)

    # ------------------------------------------------------------------
    # Load cleaned subject metadata
    # ------------------------------------------------------------------
    clean_df = pd.read_parquet(args.input)
    subject_ids = clean_df["subject_id"].astype(str).tolist()
    logger.info("Computing entropy for %d subjects.", len(subject_ids))

    # ------------------------------------------------------------------
    # Determine parcel identifiers (assume Schaefer‑400)
    # ------------------------------------------------------------------
    parcel_ids = [f"parcel_{i}" for i in range(400)]

    # ------------------------------------------------------------------
    # Prepare container for long‑format rows
    # ------------------------------------------------------------------
    rows = []

    # ------------------------------------------------------------------
    # Process each subject individually
    # ------------------------------------------------------------------
    for subj in subject_ids:
        ts_path = paths.data("raw", "timeseries", f"subject_{subj}.parquet")
        if not ts_path.is_file():
            logger.error(
                "Timeseries file missing for subject %s: %s", subj, ts_path
            )
            raise FileNotFoundError(
                f"Timeseries file not found for subject {subj}"
            )

        ts_df = pd.read_parquet(ts_path)

        # Compute entropy for all parcels (batching to limit RAM)
        for batch in _batch_iter(parcel_ids, args.batch_size):
            batch_df = ts_df[batch]
            ent_series = multiscale_entropy(
                batch_df,
                scales=tuple(args.scales),
                m=args.m,
                r=args.r,
            )
            for parcel, entropy_val in ent_series.items():
                row = {
                    "subject_id": subj,
                    "parcel_id": parcel,
                    "entropy": float(entropy_val)
                    if not pd.isna(entropy_val)
                    else float("nan"),
                }
                # Compute checksum for the row (subject_id, parcel_id, entropy)
                checksum_series = pd.Series(row)
                row["checksum"] = hashlib.sha256(
                    "|".join(
                        [
                            str(checksum_series[col])
                            if pd.notna(checksum_series[col])
                            else "nan"
                            for col in checksum_series.index
                        ]
                    ).encode("utf-8")
                ).hexdigest()
                rows.append(row)

    # ------------------------------------------------------------------
    # Write the long‑format matrix
    # ------------------------------------------------------------------
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    matrix_df = pd.DataFrame(
        rows,
        columns=["subject_id", "parcel_id", "entropy", "checksum"],
    )
    matrix_df.to_parquet(out_path, index=False)
    logger.info("Entropy matrix written to %s", out_path)

    # The multiscale_entropy function already writes invalid_parcels.csv
    # (if any) to data/derived/invalid_parcels.csv, satisfying the task
    # requirement.

if __name__ == "__main__":
    main()
