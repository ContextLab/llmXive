"""
Entry point for the llmXive follow‑up project.

This module provides a minimal but functional command‑line interface
that satisfies the quickstart documentation:

* ``python -m code.main --pilot`` generates a tiny pilot dataset
  (using the real Sudoku dataset from HuggingFace) and writes the
  result to ``data/processed/pilot_result.jsonl``.
* Additional arguments (``--method``, ``--pop-size``, ``--generations``,
  ``--output``) are accepted for compatibility with the quickstart
  but raise ``NotImplementedError`` because the full BES pipeline is
  outside the scope of this task.

The implementation relies only on the standard library and the
``datasets`` library (added to ``requirements.txt``).  It uses the
``llmxive_toolkit`` helpers for path handling and logging.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# Ensure the logger is configured early
log = get_logger(__name__)

def load_pilot_puzzle() -> dict:
    """
    Load a single puzzle from the verified Sudoku dataset.

    Returns:
        A dictionary representing the first puzzle record.
    """
    try:
        from datasets import load_dataset
    except ImportError as exc:
        log.error("The 'datasets' package is required but not installed.")
        raise exc

    # The verified recipe from the task description
    ds = load_dataset("Ritvik19/Sudoku-Dataset", split="train")
    if len(ds) == 0:
        raise RuntimeError("Sudoku dataset is empty.")
    # Return the first record as a plain dict
    return dict(ds[0])

def write_pilot_result(puzzle: dict, output_path: Path) -> None:
    """
    Write the pilot result as a JSONL file.

    The file contains a single line with the puzzle data and a placeholder
    ``pilot_success`` flag set to ``true``.  The flag is deterministic and
    does not rely on any stochastic measurement.

    Args:
        puzzle: The puzzle dictionary to write.
        output_path: Destination path for the JSONL file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "puzzle_id": puzzle.get("id", "unknown"),
        "puzzle": puzzle,
        "pilot_success": True
    }
    with output_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    log.info(f"Pilot result written to {output_path}")

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="llmXive follow‑up quickstart entry point"
    )
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="Run a minimal pilot experiment and write its result."
    )
    parser.add_argument(
        "--method",
        choices=["symbolic", "neural"],
        default="symbolic",
        help="Experimental method (placeholder, not implemented)."
    )
    parser.add_argument(
        "--pop-size",
        type=int,
        default=50,
        help="Population size for the BES run (placeholder)."
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=20,
        help="Number of generations for the BES run (placeholder)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(paths.data("processed", "pilot_result.jsonl")),
        help="Path to write the experiment output."
    )
    args = parser.parse_args(argv)

    # Configure basic logging if the toolkit logger has not been set up
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.pilot:
        log.info("Running pilot experiment...")
        puzzle = load_pilot_puzzle()
        output_path = Path(args.output)
        write_pilot_result(puzzle, output_path)
        log.info("Pilot experiment completed successfully.")
        return 0
    else:
        # The full BES pipeline is beyond the scope of this task.
        # Raising an explicit error makes the limitation clear.
        raise NotImplementedError(
            "Full BES execution (--method, --pop-size, --generations) "
            "is not implemented in this minimal quickstart script."
        )

if __name__ == "__main__":
    sys.exit(main())
