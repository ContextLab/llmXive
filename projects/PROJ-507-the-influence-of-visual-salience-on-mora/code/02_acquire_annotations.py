"""
02_acquire_annotations.py
-------------------------

This script handles the acquisition of human ambiguity annotations for
candidate scenarios. It provides two main modes of operation:

1. **Template generation** (``--generate`` flag):
   Given a CSV file that lists scenario identifiers (produced by
   ``01_ingest_and_filter.py``), it creates a template CSV for each
   requested annotator. The templates contain a ``scenario_id`` column
   that can be filled in by external crowd‑workers (e.g., via Prolific).

2. **Validation** (default mode):
   After the annotation files have been collected, the script checks that
   at least three annotator files exist and that each scenario has received
   at least three ratings in total. If these conditions are not met,
   an :class:`InsufficientAnnotatorsError` is raised.

The script is deliberately lightweight and does not perform any I/O
beyond the required CSV reads/writes. It uses the project's path helper
``llmxive_toolkit.paths`` to ensure that all files live inside the
``data/`` hierarchy.
"""

import argparse
import os
from pathlib import Path
from typing import List, Set

import pandas as pd

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Exceptions
# ----------------------------------------------------------------------
class InsufficientAnnotatorsError(Exception):
    """Raised when there are not enough annotation files or ratings per scenario."""
    pass

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_scenario_ids(csv_path: Path) -> List[str]:
    """Load the ``scenario_id`` column from the supplied CSV."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")
    df = pd.read_csv(csv_path, dtype=str)
    if "scenario_id" not in df.columns:
        raise ValueError("Input CSV must contain a 'scenario_id' column.")
    return df["scenario_id"].dropna().tolist()

def _write_template_csv(scenario_ids: List[str], output_path: Path) -> None:
    """Write a template CSV containing ``scenario_id`` for a single annotator."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    template_df = pd.DataFrame({"scenario_id": scenario_ids})
    template_df.to_csv(output_path, index=False)
    log.info(f"Template written for annotator: {output_path.name}")

def generate_templates(
    input_csv: Path,
    annotator_ids: List[str],
    output_dir: Path,
) -> None:
    """
    Generate a template CSV for each annotator.

    Parameters
    ----------
    input_csv: Path
        CSV produced by ``01_ingest_and_filter.py`` containing a
        ``scenario_id`` column.
    annotator_ids: List[str]
        List of annotator identifiers (e.g., ``['A1', 'A2', 'A3']``).
    output_dir: Path
        Directory where the template CSVs will be written.
    """
    scenario_ids = _load_scenario_ids(input_csv)

    for annotator_id in annotator_ids:
        filename = f"annotations_template_{annotator_id}.csv"
        output_path = output_dir / filename
        _write_template_csv(scenario_ids, output_path)

def _discover_annotation_files(folder: Path) -> List[Path]:
    """Return a list of all annotation CSV files in ``folder``."""
    return sorted(folder.glob("annotations_template_*.csv"))

def _load_all_annotations(files: List[Path]) -> pd.DataFrame:
    """Concatenate all annotation CSVs into a single DataFrame."""
    dfs = []
    for f in files:
        df = pd.read_csv(f, dtype=str)
        if "scenario_id" not in df.columns or "rating" not in df.columns:
            raise ValueError(
                f"Annotation file {f.name} must contain 'scenario_id' and 'rating' columns."
            )
        df["annotator_id"] = f.stem.replace("annotations_template_", "")
        dfs.append(df)
    if not dfs:
        return pd.DataFrame(columns=["scenario_id", "rating", "annotator_id"])
    return pd.concat(dfs, ignore_index=True)

def validate_annotations(
    annotation_dir: Path,
    min_annotators: int = 3,
    min_ratings_per_scenario: int = 3,
) -> None:
    """
    Validate that enough annotation files exist and that each scenario has
    enough ratings.

    Parameters
    ----------
    annotation_dir: Path
        Directory containing the collected annotation CSVs.
    min_annotators: int, default 3
        Minimum number of distinct annotator files required.
    min_ratings_per_scenario: int, default 3
        Minimum total number of ratings that each scenario must have.
    """
    files = _discover_annotation_files(annotation_dir)
    log.info(f"Found {len(files)} annotation files in {annotation_dir}")

    if len(files) < min_annotators:
        raise InsufficientAnnotatorsError(
            f"Expected at least {min_annotators} annotation files, found {len(files)}."
        )

    all_annotations = _load_all_annotations(files)

    # Count ratings per scenario across all annotators
    rating_counts = (
        all_annotations.groupby("scenario_id")["rating"]
        .count()
        .reset_index(name="rating_count")
    )

    insufficient = rating_counts[
        rating_counts["rating_count"] < min_ratings_per_scenario
    ]

    if not insufficient.empty:
        missing = ", ".join(insufficient["scenario_id"].tolist())
        raise InsufficientAnnotatorsError(
            f"The following scenarios have fewer than {min_ratings_per_scenario} ratings: {missing}"
        )

    log.info("All annotation validation checks passed.")

# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Acquire and validate human ambiguity annotations."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the CSV containing scenario IDs (output of 01_ingest_and_filter.py).",
    )
    parser.add_argument(
        "--annotators",
        nargs="+",
        default=["A1", "A2", "A3"],
        help="List of annotator identifiers for which to generate templates.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(paths.data("raw", "human_coding")),
        help="Directory where annotation templates will be written or read from for validation.",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate template CSVs for the annotators and exit.",
    )
    return parser

def main() -> None:
    args = _build_arg_parser().parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)

    if args.generate:
        # Generate template CSVs
        generate_templates(
            input_csv=input_path,
            annotator_ids=args.annotators,
            output_dir=output_dir,
        )
        log.info("Template generation completed.")
    else:
        # Validate existing annotation files
        try:
            validate_annotations(annotation_dir=output_dir)
            log.info("Annotation validation succeeded.")
        except InsufficientAnnotatorsError as e:
            log.error(str(e))
            raise

if __name__ == "__main__":
    main()
