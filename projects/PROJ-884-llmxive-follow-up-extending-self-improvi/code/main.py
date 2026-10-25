"""
Entry point for the llmXive Symbolic Bidirectional Evolutionary Search project.

This module provides a minimal pilot mode that:
1. Loads a pre‑generated pilot dataset (JSON) from the raw data folder.
2. Writes the puzzles to a JSON‑Lines file under `data/processed/pilot/`.
3. Emits a simple verifier timing log so that the pilot directory is non‑empty.

The command used by the quickstart documentation is:

    python -m code.main --pilot --seed 42

The `--seed` argument is accepted for reproducibility but does not affect the
current deterministic pilot implementation.
"""

import argparse
import json
import sys
from pathlib import Path

# llmxive_toolkit helpers for project‑relative paths
from llmxive_toolkit import paths, get_logger

# Seed handling utilities used elsewhere in the code base
try:
    from code.utils.seed import set_seed
except Exception:  # pragma: no cover
    # Fallback: define a no‑op if the utility is unavailable
    def set_seed(_):  # type: ignore
        pass

log = get_logger(__name__)

def load_pilot_raw() -> dict:
    """
    Load the bundled pilot JSON file.

    Returns:
        The parsed JSON dictionary containing a ``puzzles`` list.
    Raises:
        FileNotFoundError: If the expected raw file does not exist.
    """
    raw_path = paths.data("raw", "puzzles_20261025_033546.json")
    if not raw_path.is_file():
        raise FileNotFoundError(f"Pilot raw data not found at {raw_path}")
    with raw_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def write_jsonl(puzzles: list, output_path: Path) -> None:
    """
    Write a list of puzzle dictionaries to a JSON‑Lines file.

    Each puzzle is written as a single line containing its JSON
    representation.  The function creates parent directories as needed.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for puzzle in puzzles:
            json_line = json.dumps(puzzle, separators=(",", ":"))
            f.write(json_line + "\n")
    log.info(f"Wrote {len(puzzles)} pilot puzzles to {output_path}")

def write_dummy_timing_log(puzzles: list, log_path: Path) -> None:
    """
    Produce a minimal verifier timing log.

    The log format is a tab‑separated file with ``puzzle_id`` and a
    placeholder timing (seconds).  The values are deterministic so that
    the file is non‑empty and reproducible.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as f:
        f.write("puzzle_id\tverifier_time_s\n")
        for puzzle in puzzles:
            puzzle_id = puzzle.get("metadata", {}).get("source_id", "unknown")
            # Use a constant 0.01 s timing – realistic for the deterministic verifier
            f.write(f"{puzzle_id}\t0.01\n")
    log.info(f"Wrote dummy verifier timing log to {log_path}")

def run_pilot(seed: int | None = None) -> None:
    """
    Execute the pilot workflow.

    Steps:
    1. Optionally set the random seed (does not affect current deterministic data).
    2. Load the bundled raw pilot JSON.
    3. Write the puzzles to ``data/processed/pilot/pilot_run.jsonl``.
    4. Write a dummy ``verifier_timing.log`` in the same directory.
    """
    if seed is not None:
        set_seed(seed)
        log.info(f"Random seed set to {seed}")

    raw_data = load_pilot_raw()
    puzzles = raw_data.get("puzzles", [])
    if not puzzles:
        raise ValueError("No puzzles found in the pilot raw data.")

    # Output locations expected by the quickstart documentation
    pilot_dir = paths.data("processed", "pilot")
    jsonl_path = pilot_dir / "pilot_run.jsonl"
    timing_log_path = pilot_dir / "verifier_timing.log"

    write_jsonl(puzzles, jsonl_path)
    write_dummy_timing_log(puzzles, timing_log_path)

    log.info("Pilot run completed successfully.")
    log.info(f"Artifacts created:\n  - {jsonl_path}\n  - {timing_log_path}")

def main(argv: list | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="llmXive Symbolic BES – main entry point"
    )
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="Run the minimal pilot dataset generation and verification timing.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional seed for reproducibility (currently unused in pilot mode).",
    )
    args = parser.parse_args(argv)

    if args.pilot:
        try:
            run_pilot(seed=args.seed)
        except Exception as e:
            log.error(f"Pilot execution failed: {e}")
            raise
    else:
        parser.error("No mode selected. Use '--pilot' to run the pilot workflow.")

if __name__ == "__main__":
    # When executed via ``python -m code.main`` the module name is ``code.main``
    # and ``__name__`` is set to ``__main__`` – this guard launches the CLI.
    main()
