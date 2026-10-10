"""Generate an unlabeled audit sample for manual review.

This script implements the manual gate (T017a) by creating the required
`docs/reports/audit_sample_unlabeled.csv` file. The file lists a random
sample of PRs (identified by `pr_id`) along with the commit message and
a representative code snippet. Human reviewers are expected to fill in
the `human_label` column (enum: 'LLM' or 'Human') and save the result as
`docs/reports/audit_sample_labeled.csv`.

The script first attempts to load the classified PRs parquet file
(`data/processed/classified_prs.parquet`). If the file does not exist,
it will:

1. Fetch a subset of the raw GitHub PR dataset from HuggingFace.
2. Run the keyword‑based classification pipeline.
3. Persist the classified DataFrame as parquet at the expected location.

This fallback ensures the script can run end‑to‑end without requiring a
separate preprocessing step, while still operating on **real data**.

The script is deterministic: it uses the global random seed defined in
the project configuration (default 42) to ensure reproducibility across
runs. It can be re‑executed safely; if the output file already exists it
will be overwritten.
"""

import argparse
import logging
from pathlib import Path

import pandas as pd

from code.utils.config import set_global_seed, get_seed
from code.utils.logger import get_logger
from code.data.fetch import fetch_dataset
from code.labeling.classify import classify_dataset

DEFAULT_CLASSIFIED_PATH = Path("data/processed/classified_prs.parquet")
DEFAULT_OUTPUT_PATH = Path("docs/reports/audit_sample_unlabeled.csv")
SAMPLE_SIZE_DEFAULT = 20
FETCH_MAX_RECORDS = 5000  # Fetch a reasonable subset to keep runtime low


def load_classified_data(input_path: Path) -> pd.DataFrame:
    """Load the classified PRs parquet file.

    Raises:
        FileNotFoundError: If the parquet file does not exist.
    """
    if not input_path.is_file():
        raise FileNotFoundError(f"Classified data not found at {input_path}")
    return pd.read_parquet(input_path)


def create_classified_parquet(path: Path) -> pd.DataFrame:
    """Fetch raw data, run classification, and write parquet.

    This function is used as a fallback when the expected classified
    parquet does not exist. It fetches a subset of the dataset,
    classifies it, and writes the result to `path`.

    Returns:
        The classified DataFrame.
    """
    logger = get_logger(__name__)

    logger.info(
        "Classified parquet not found. Fetching raw dataset (max %d records)...",
        FETCH_MAX_RECORDS,
    )
    # Fetch a subset of the dataset; streaming=True ensures low memory use.
    raw_df = fetch_dataset(
        dataset_name="codeparliament/github-code-search",
        split="train",
        streaming=True,
        max_records=FETCH_MAX_RECORDS,
    )
    if raw_df is None or raw_df.empty:
        raise RuntimeError("Failed to fetch any records from the dataset.")

    logger.info("Running keyword‑based classification on fetched data.")
    classified_df = classify_dataset(raw_df)

    # Ensure the target directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    classified_df.to_parquet(path, index=False)
    logger.info("Classified data written to %s", path)

    return classified_df


def select_audit_sample(
    df: pd.DataFrame,
    sample_size: int,
    seed: int,
) -> pd.DataFrame:
    """Select a random sample of PRs for manual audit.

    The returned DataFrame contains only the columns required for the
    manual audit CSV: `pr_id`, `commit_message`, and `code_snippet`.
    """
    required_cols = {"pr_id", "commit_message", "code_snippet"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"Input data is missing required columns for audit sample: {missing}"
        )

    # Reproducible sampling
    sampled = df.sample(n=sample_size, random_state=seed)
    sampled = sampled.sort_values("pr_id")
    return sampled[["pr_id", "commit_message", "code_snippet"]]


def write_audit_csv(df: pd.DataFrame, output_path: Path) -> None:
    """Write the audit sample CSV with the required schema."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, line_terminator="\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate unlabeled audit sample for manual labeling."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_CLASSIFIED_PATH,
        help="Path to the classified PRs parquet file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Path where the unlabeled audit CSV will be written.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=SAMPLE_SIZE_DEFAULT,
        help="Number of PRs to include in the audit sample.",
    )
    args = parser.parse_args()

    # Initialise logging and seeds
    logger = get_logger(__name__)
    set_global_seed()
    seed = get_seed()

    logger.info("Attempting to load classified PR data from %s", args.input)
    try:
        df = load_classified_data(args.input)
    except FileNotFoundError as e:
        logger.warning(str(e))
        # Fall back to fetching & classifying a subset of the raw dataset
        df = create_classified_parquet(args.input)

    logger.info(
        "Selecting %d PRs for the manual audit sample (seed=%d)",
        args.sample_size,
        seed,
    )
    audit_df = select_audit_sample(df, args.sample_size, seed)

    logger.info("Writing unlabeled audit sample to %s", args.output)
    write_audit_csv(audit_df, args.output)

    logger.info("Audit sample generation complete.")


if __name__ == "__main__":
    main()
