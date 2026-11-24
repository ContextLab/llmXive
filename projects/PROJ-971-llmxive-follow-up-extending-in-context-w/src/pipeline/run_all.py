"""
run_all.py

Minimal end‑to‑end pipeline for the Auto‑ICWM project.
Generates a reproducible set of interaction clips, extracts the three
latent statistical descriptors, writes the full descriptor table,
creates a subset CSV (default 50 rows), prints a concise summary table
to stdout and logs it to ``logs/run_end_to_end.log``.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

from llmxive_toolkit import paths, get_logger
from src.pipeline.generate_clips import generate_clips
from src.pipeline.extract_descriptors import extract_all_descriptors

log = get_logger(__name__)

def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the minimal end‑to‑end Auto‑ICWM pipeline."
    )
    parser.add_argument(
        "--subset",
        type=int,
        default=50,
        help="Number of clips (and descriptor rows) to generate and summarise.",
    )
    return parser.parse_args(argv)

def main(argv=None):
    args = _parse_args(argv)

    # ------------------------------------------------------------------
    # 1. Generate reproducible interaction clips
    # ------------------------------------------------------------------
    raw_dir = paths.data("raw")
    log.info("Generating %d clips in %s", args.subset, raw_dir)
    generate_clips(num_clips=args.subset, out_dir=raw_dir)

    # ------------------------------------------------------------------
    # 2. Extract latent descriptors for all generated clips
    # ------------------------------------------------------------------
    descriptors_path = paths.data("processed", "descriptors.csv")
    log.info("Extracting descriptors to %s", descriptors_path)
    extract_all_descriptors(raw_dir, descriptors_path)

    # ------------------------------------------------------------------
    # 3. Write the subset CSV (first N rows)
    # ------------------------------------------------------------------
    subset_path = paths.data("processed", "descriptors_subset.csv")
    log.info("Writing first %d rows to %s", args.subset, subset_path)

    df_full = pd.read_csv(descriptors_path)
    if len(df_full) < args.subset:
        raise RuntimeError(
            f"Requested subset of {args.subset} rows but only "
            f"{len(df_full)} rows are available in {descriptors_path}"
        )
    df_subset = df_full.head(args.subset)
    df_subset.to_csv(subset_path, index=False)

    # ------------------------------------------------------------------
    # 4. Print and log the summary table
    # ------------------------------------------------------------------
    table_str = df_subset.to_string(index=False)
    print(table_str)

    # Log the same table – the logger writes to a file under the project
    # ``logs`` directory via the llmxive_toolkit logger configuration.
    log_file = paths.path("logs", "run_end_to_end.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(table_str + "\n")
    log.info("Summary table written to %s", log_file)

    return 0

if __name__ == "__main__":
    sys.exit(main())
