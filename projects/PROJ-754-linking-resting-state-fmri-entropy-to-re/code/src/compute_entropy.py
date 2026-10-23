"""
compute_entropy.py
------------------
Reads the cleaned subject table, loads each subject's parcel‑wise
time‑series, computes multiscale sample entropy using the implementation
in ``code.src.analysis.entropy``, and writes two artefacts:

  * ``results/entropy_matrix.parquet`` – subjects × parcels matrix
  * ``results/covariates.parquet`` – behavioural covariates for the same
    subjects (subject_id, age, sex, mean_fd, dsrt_score)

The script processes parcels in batches (default ≤ 50) to keep peak RAM
below the 4 GB limit.
"""
import argparse
import pandas as pd
from pathlib import Path
from llmxive_toolkit import paths, get_logger
from code.src.analysis.entropy import multiscale_entropy

def _batch_iter(seq, batch_size):
    """Yield successive batches from *seq* of size *batch_size*."""
    for i in range(0, len(seq), batch_size):
        yield seq[i : i + batch_size]

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute multiscale entropy matrix for a cohort."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the cleaned subjects parquet (data/derived/clean_subjects.parquet).",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write the entropy matrix parquet (results/entropy_matrix.parquet).",
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
    # Prepare container for entropy rows
    # ------------------------------------------------------------------
    entropy_rows = []

    # ------------------------------------------------------------------
    # Process each subject individually
    # ------------------------------------------------------------------
    for subj in subject_ids:
        ts_path = paths.data("raw", "timeseries", f"{subj}.parquet")
        ts_df = pd.read_parquet(ts_path)

        # Compute entropy for all parcels (batching to limit RAM)
        subj_entropy = {}
        for batch in _batch_iter(parcel_ids, args.batch_size):
            batch_df = ts_df[batch]
            ent_series = multiscale_entropy(
                batch_df,
                scales=tuple(args.scales),
                m=args.m,
                r=args.r,
            )
            subj_entropy.update(ent_series.to_dict())

        # Preserve order of parcels
        ordered_entropy = [subj_entropy.get(pid, float("nan")) for pid in parcel_ids]
        entropy_rows.append(ordered_entropy)

    # ------------------------------------------------------------------
    # Assemble matrix and write to disk
    # ------------------------------------------------------------------
    entropy_matrix = pd.DataFrame(entropy_rows, index=subject_ids, columns=parcel_ids)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    entropy_matrix.to_parquet(out_path)
    logger.info("Entropy matrix written to %s", out_path)

    # ------------------------------------------------------------------
    # Write covariates (behavioural table) to results
    # ------------------------------------------------------------------
    covariates = clean_df[["subject_id", "age", "sex", "mean_fd", "dsrt_score"]].copy()
    cov_path = paths.results("covariates.parquet")
    cov_path.parent.mkdir(parents=True, exist_ok=True)
    covariates.to_parquet(cov_path)
    logger.info("Covariates written to %s", cov_path)

if __name__ == "__main__":
    main()
