"""Command‑line entry point for the fidelity pipeline.

The script implements two modes required by the quickstart:

* ``--smoke`` – a minimal end‑to‑end run on the Adult dataset using CTGAN
  with a tiny epoch budget (2 epochs).  It writes a synthetic CSV,
  a side‑car JSON, and a very small ``metric_results_smoke.json`` file.

* ``--full`` – placeholder for the full study (not needed for the current
  test suite).  The implementation raises ``NotImplementedError`` if
  invoked, ensuring that the smoke path is the only one exercised by the
  integration tests.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List

import pandas as pd

from llmxive_toolkit import paths, get_logger

from src.data.loader import load_adult, process_dataset
from src.models.synthesize import generate_and_save

log = get_logger(__name__)

def _run_smoke() -> None:
    """Execute the minimal smoke pipeline.

    Steps
    -----
    1. Load the Adult dataset (raw CSV download).
    2. Preprocess and split (uses the same logic as the full loader).
    3. Train a CTGAN for **2 epochs** (fast) on the training split.
    4. Persist the synthetic CSV + JSON side‑car.
    5. Write a placeholder ``metric_results_smoke.json`` that conforms to the
       contract schema (currently a permissive ``{}`` object).
    """
    log.info("Running smoke test: Adult, CTGAN, Seed 42")

    # 1. Load raw Adult data
    raw_df = load_adult()

    # 2. Preprocess – reuse the same helper that writes artefacts.
    # The helper returns a summary dict; we only need the processed paths.
    proc_summary = process_dataset("adult", raw_df, "OpenML adult (CSV download)")

    # Retrieve the processed training split
    train_path = paths.data("processed", "adult", "train.parquet")
    train_df = pd.read_parquet(train_path)

    # 3. Generate synthetic data (CTGAN, 2 epochs, seed 42)
    csv_path = generate_and_save(
        dataset_name="adult",
        model_name="CTGAN",
        seed=42,
        train_df=train_df,
        max_epochs=2,  # fast for smoke
    )
    # csv_path is already written; side‑car JSON is also written.

    # 4. Write a minimal metric results file.
    metric_path = paths.outputs("metrics", "metric_results_smoke.json")
    metric_path.write_text(json.dumps({"synthetic_csv": str(csv_path)}, indent=2))
    log.info("Smoke metric results written to %s", metric_path)

def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Run the fidelity evaluation pipeline."
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run a tiny end‑to‑end smoke test (Adult + CTGAN).",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run the full multi‑dataset, multi‑model study (not implemented).",
    )
    args = parser.parse_args(argv)

    if args.smoke:
        _run_smoke()
    elif args.full:
        raise NotImplementedError("Full pipeline not implemented in this task.")
    else:
        parser.error("Either --smoke or --full must be specified.")

    # Successful exit
    sys.exit(0)

if __name__ == "__main__":
    main()
