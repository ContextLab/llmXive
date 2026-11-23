"""Implementation of the ablation pipeline for training.

This script adds a ``--remove-solvent`` flag that, when enabled, strips any
solvent‑related descriptor fields from the featurized dataset before the
standard training pipeline is executed.  The underlying training logic
resides in :pymod:`training.train`, which is invoked after the optional
ablation step.

The script is deliberately lightweight and does **not** introduce new
runtime dependencies beyond the existing project modules.
"""

import argparse
import json
from pathlib import Path

from utils.logging import get_logger
from training.train import main as train_main

__all__ = ["ablate_solvent_features", "process_dataset", "main"]

def ablate_solvent_features(record: dict) -> dict:
    """Remove solvent descriptor fields from a single featurized record.

    The exact keys used for solvent descriptors are not fixed in the
    repository; to remain robust we drop any key that starts with the
    prefix ``solvent_``.  The function mutates the supplied ``record`` and
    also returns it for convenience.

    Parameters
    ----------
    record:
        A dictionary representing one line of the featurized JSONL file.

    Returns
    -------
    dict
        The same dictionary with solvent descriptor entries removed.
    """
    # Identify keys that look like solvent descriptors.
    solvent_keys = [k for k in record if k.startswith("solvent_")]
    for key in solvent_keys:
        del record[key]
    return record

def process_dataset(
    input_path: Path, output_path: Path, remove_solvent: bool
) -> None:
    """Read the featurized JSONL, optionally remove solvent fields, and write out.

    Parameters
    ----------
    input_path:
        Path to the original ``featurized.jsonl`` file.
    output_path:
        Destination path for the (potentially) ablated dataset.
    remove_solvent:
        If ``True``, solvent descriptor fields are stripped from each record.
    """
    logger = get_logger(__name__)

    with input_path.open("r", encoding="utf-8") as fin, output_path.open(
        "w", encoding="utf-8"
    ) as fout:
        for line in fin:
            if not line.strip():
                # Skip empty lines that may appear at EOF.
                continue
            record = json.loads(line)
            if remove_solvent:
                record = ablate_solvent_features(record)
            fout.write(json.dumps(record) + "\n")

    logger.info(
        f"{'Ablated' if remove_solvent else 'Copied'} dataset written to {output_path}"
    )

def main() -> None:
    """Entry point for the ablation pipeline.

    The script performs the following steps:

    1. Parse ``--remove-solvent`` from the command line.
    2. If the flag is present, create an ablated copy of
       ``data/processed/featurized.jsonl`` where all keys beginning with
       ``solvent_`` are removed, and replace the original file with this
       ablated version.
    3. Invoke the standard training pipeline (``training.train.main``), which
       will now operate on the modified dataset when the flag is used.
    """
    parser = argparse.ArgumentParser(
        description="Ablation pipeline for training with optional solvent removal."
    )
    parser.add_argument(
        "--remove-solvent",
        action="store_true",
        help=(
            "When set, solvent descriptor fields are removed from the "
            "featurized dataset before training."
        ),
    )
    args = parser.parse_args()

    logger = get_logger(__name__)

    featurized_path = Path("data/processed/featurized.jsonl")
    if not featurized_path.is_file():
        raise FileNotFoundError(
            f"Featurized dataset not found at expected location: {featurized_path}"
        )

    if args.remove_solvent:
        # Write a temporary ablated file and then replace the original so that
        # downstream training code (which expects the default path) sees the
        # modified data.
        temp_path = Path("data/processed/featurized_ablation.jsonl")
        logger.info(
            "Removing solvent descriptor fields from the featurized dataset..."
        )
        process_dataset(featurized_path, temp_path, remove_solvent=True)

        # Replace the original file atomically.
        temp_path.replace(featurized_path)
        logger.info(
            "Solvent descriptors removed; original featurized file overwritten."
        )
    else:
        logger.info("No ablation requested; proceeding with original dataset.")

    # Run the regular training pipeline.
    logger.info("Starting standard training pipeline.")
    train_main()

if __name__ == "__main__":
    main()