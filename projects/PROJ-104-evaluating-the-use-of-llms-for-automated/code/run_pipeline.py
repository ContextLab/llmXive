"""Orchestrator for the LLM‑fidelity pipeline.

This orchestrator now supports a real 5‑sample quick‑start run. When the
``--sample`` flag is provided it:

1. Calls the data‑extraction script to fetch real commit‑pair data from the
   target repositories.
2. Truncates the resulting ``commit_pairs.csv`` to the requested number of
   samples (deterministically using the global seed).
3. Runs the generation stage (Task T006) which creates placeholder output
   files for each model.
4. Runs the intent‑entity extraction stage (Task T008) so that at least one
   JSON file appears under ``data/intermediate/intent_entities`` – a
   requirement of the quick‑start verification test.
5. Returns the exit code of the generation stage (0 on success).

The ``--full`` flag still runs only the stages that have been implemented
so far (generation and intent extraction). Future stages can be added here
without breaking the quick‑start flow.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths
from code.generation import main as generation_main
from code.entity_extraction_intent import run_extraction as intent_run_extraction
from code.data_extraction import main as data_extraction_main
from code.seeds import SEED

log = get_logger(__name__)

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the LLM fidelity pipeline")
    parser.add_argument(
        "--sample",
        type=int,
        help="Run a quick‑start with the given number of real samples (uses the data‑extraction stage).",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run the full pipeline (all implemented stages).",
    )
    return parser.parse_args(argv)

def _sample_commit_pairs(csv_path: Path, n_samples: int) -> None:
    """Truncate ``commit_pairs.csv`` to ``n_samples`` rows (deterministic)."""
    import pandas as pd

    df = pd.read_csv(csv_path, dtype=str)
    df = df.sample(n=n_samples, random_state=SEED).reset_index(drop=True)
    df.to_csv(csv_path, index=False)
    log.info("Sampled %d commit‑pair rows for quick‑start", n_samples)

def _ensure_real_data(sample: int | None) -> None:
    """
    When ``sample`` is provided we fetch real data via the extraction script
    and then keep only ``sample`` rows. This satisfies the quick‑start
    requirement of using a *real* 5‑sample subset.
    """
    csv_path = paths.data("raw", "commit_pairs.csv")
    if sample is None:
        return
    # Ensure the data extraction stage runs (it creates the CSV).
    rc = data_extraction_main()
    if rc != 0:
        log.error("Data extraction failed with exit code %d", rc)
        sys.exit(rc)

    if not csv_path.is_file():
        log.error("Data extraction did not produce %s", csv_path)
        sys.exit(1)

    _sample_commit_pairs(csv_path, sample)

def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    # Step 1: obtain real data if a sample size is requested.
    if args.sample:
        _ensure_real_data(args.sample)

    # Step 2: run generation (always runs, even for a full pipeline).
    gen_rc = generation_main()
    if gen_rc != 0:
        log.error("Generation stage failed")
        return gen_rc

    # Step 3: run intent‑entity extraction so that the quick‑start test sees
    # at least one JSON file under ``data/intermediate/intent_entities``.
    intent_rc = intent_run_extraction()
    if intent_rc != 0:
        log.error("Intent‑entity extraction failed")
        return intent_rc

    # Future stages (e.g., surface extraction, fidelity scoring, statistical
    # analysis, visualization) would be invoked here when they are ready.

    return 0

if __name__ == "__main__":
    raise SystemExit(main())