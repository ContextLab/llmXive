import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

from entropy import compute_atom_entropy, compute_bond_entropy, compute_entropy_for_dataframe
from utils import (
    load_and_verify_dataset,
    save_dataframe,
    ensure_directory,
    validate_smiles_column,
    setup_logging,
    join_metadata_with_entropy,
)

logger = logging.getLogger(__name__)


def cmd_compute_entropy(args: argparse.Namespace) -> int:
    """
    Compute atom and bond entropy for molecules in a CSV file.

    Logic:
    1. Load and verify the input CSV (must have 'smiles' column).
    2. Compute atom_entropy and bond_entropy for each valid SMILES.
    3. Handle missing logS/logP values:
       - Rows with NaN in logS/logP are preserved in the output CSV.
       - Downstream modeling tasks (US2) will skip these rows.
    4. Write the enriched CSV to the specified output path.

    Returns:
        0 on success, non-zero on failure.
    """
    setup_logging(args.verbose)

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1

    ensure_directory(output_path.parent)

    logger.info(f"Loading dataset from {input_path}")
    try:
        df = load_and_verify_dataset(input_path, required_columns=["smiles"])
    except ValueError as e:
        logger.error(f"Dataset verification failed: {e}")
        return 1

    logger.info(f"Loaded {len(df)} rows. Computing entropy metrics...")

    # Compute entropy for the dataframe
    # This function handles the SMILES parsing and entropy calculation internally
    # and returns a DataFrame with the new columns added.
    df_enriched = compute_entropy_for_dataframe(df)

    # Save the result
    logger.info(f"Saving enriched dataset to {output_path}")
    save_dataframe(df_enriched, output_path)

    logger.info("Entropy computation complete.")
    return 0


def cmd_join_metadata(args: argparse.Namespace) -> int:
    """
    Join the entropy-enriched CSV with the original metadata CSV to produce
    the final dataset for downstream modeling (US2).

    Logic:
    1. Load the entropy-enriched CSV (output from T016).
    2. Load the original metadata CSV (containing logS/logP).
    3. Perform an inner join on the 'smiles' column.
    4. Save the final merged CSV to the specified output path.

    Returns:
        0 on success, non-zero on failure.
    """
    setup_logging(args.verbose)

    entropy_path = Path(args.entropy_input)
    metadata_path = Path(args.metadata_input)
    output_path = Path(args.output)

    if not entropy_path.exists():
        logger.error(f"Entropy file not found: {entropy_path}")
        return 1
    if not metadata_path.exists():
        logger.error(f"Metadata file not found: {metadata_path}")
        return 1

    ensure_directory(output_path.parent)

    try:
        join_metadata_with_entropy(
            entropy_path=str(entropy_path),
            metadata_path=str(metadata_path),
            output_path=str(output_path),
            smiles_col=args.smiles_col
        )
    except Exception as e:
        logger.error(f"Join operation failed: {e}")
        return 1

    logger.info("Metadata join complete.")
    return 0


def cmd_train_model(args: argparse.Namespace) -> int:
    """Placeholder for train_model command (to be implemented in US2)."""
    logger.info("train_model command invoked (placeholder).")
    return 0


def cmd_plot_correlation(args: argparse.Namespace) -> int:
    """Placeholder for plot_correlation command (to be implemented in US3)."""
    logger.info("plot_correlation command invoked (placeholder).")
    return 0


def ensure_dir(path: Path) -> None:
    """Ensure the directory for the given path exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="llmXive Molecular Complexity Pipeline CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # compute_entropy command
    parser_entropy = subparsers.add_parser(
        "compute_entropy",
        help="Compute atom and bond entropy for molecules in a CSV.",
    )
    parser_entropy.add_argument(
        "input", type=str, help="Path to input CSV with SMILES column"
    )
    parser_entropy.add_argument(
        "output", type=str, help="Path to output CSV with entropy columns"
    )
    parser_entropy.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    # join_metadata command (New for T017)
    parser_join = subparsers.add_parser(
        "join_metadata",
        help="Join entropy data with metadata to produce final dataset.",
    )
    parser_join.add_argument(
        "entropy_input", type=str, help="Path to entropy-enriched CSV"
    )
    parser_join.add_argument(
        "metadata_input", type=str, help="Path to original metadata CSV (with logS/logP)"
    )
    parser_join.add_argument(
        "output", type=str, help="Path to output final enriched CSV"
    )
    parser_join.add_argument(
        "--smiles-col", type=str, default="smiles", help="Column name for SMILES (default: smiles)"
    )
    parser_join.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    # train_model command
    parser_model = subparsers.add_parser(
        "train_model",
        help="Train Ridge Regression models on entropy data.",
    )
    parser_model.add_argument(
        "input", type=str, help="Path to input enriched CSV"
    )
    parser_model.add_argument(
        "output_dir", type=str, help="Directory to save models and reports"
    )

    # plot_correlation command
    parser_plot = subparsers.add_parser(
        "plot_correlation",
        help="Generate correlation plots.",
    )
    parser_plot.add_argument(
        "input", type=str, help="Path to input enriched CSV"
    )
    parser_plot.add_argument(
        "output_dir", type=str, help="Directory to save plots"
    )

    args = parser.parse_args()

    if args.command == "compute_entropy":
        return cmd_compute_entropy(args)
    elif args.command == "join_metadata":
        return cmd_join_metadata(args)
    elif args.command == "train_model":
        return cmd_train_model(args)
    elif args.command == "plot_correlation":
        return cmd_plot_correlation(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())