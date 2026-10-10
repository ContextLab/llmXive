"""Generate an unlabeled audit sample for manual review.

This script implements the manual gate (T017a) by creating the required
`docs/reports/audit_sample_unlabeled.csv` file. The file lists a random
sample of PRs (identified by `pr_id`) along with the commit message and
a representative code snippet. Human reviewers are expected to fill in
the `human_label` column (enum: 'LLM' or 'Human') and save the result as
`docs/reports/audit_sample_labeled.csv`.

The script is deterministic: it uses the global random seed defined in
the project configuration (default 42) to ensure reproducibility across
runs. It can be re‑executed safely; if the output file already exists it
will be overwritten.

Expected input:
  - `data/processed/classified_prs.parquet` (produced by T014f)

Output:
  - `docs/reports/audit_sample_unlabeled.csv`
"""

import argparse
import logging
from pathlib import Path

import pandas as pd

from code.utils.config import set_global_seed, get_seed
from code.utils.logger import get_logger


def load_classified_data(input_path: Path) -> pd.DataFrame:
    """Load the classified PRs parquet file."""
    if not input_path.is_file():
        raise FileNotFoundError(f"Classified data not found at {input_path}")
    df = pd.read_parquet(input_path)
    return df


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

    # Ensure reproducibility
    sampled = df.sample(n=sample_size, random_state=seed)
    # Preserve order for easier human review
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
        default=Path("data/processed/classified_prs.parquet"),
        help="Path to the classified PRs parquet file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/reports/audit_sample_unlabeled.csv"),
        help="Path where the unlabeled audit CSV will be written.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=20,
        help="Number of PRs to include in the audit sample.",
    )
    args = parser.parse_args()

    # Initialise logging and seeds
    logger = get_logger(__name__)
    set_global_seed()
    seed = get_seed()

    logger.info("Loading classified PR data from %s", args.input)
    df = load_classified_data(args.input)

    logger.info(
        "Selecting %d PRs for the manual audit sample (seed=%d)", args.sample_size, seed
    )
    audit_df = select_audit_sample(df, args.sample_size, seed)

    logger.info("Writing unlabeled audit sample to %s", args.output)
    write_audit_csv(audit_df, args.output)

    logger.info("Audit sample generation complete.")


if __name__ == "__main__":
    main()
