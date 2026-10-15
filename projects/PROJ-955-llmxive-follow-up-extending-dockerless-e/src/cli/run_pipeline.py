"""Run the LLM‑Xive static‑dynamic analysis pipeline.

This script now supports full pipeline execution. It parses command‑line
arguments for dataset URLs, an optional output directory, and a random
seed. When ``--dry-run`` is omitted, the ingestion step is run and the
required data artefacts are produced.

The full pipeline (graph extraction, feature engineering, model training,
etc.) will be added in later tasks.
"""
import argparse
import sys
import random
from pathlib import Path

import numpy as np
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Global reproducibility settings
# ----------------------------------------------------------------------
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

log = get_logger(__name__)
log.info("Random seed set to %d", SEED)

def ensure_project_dirs() -> None:
    """Create all top‑level directories required by the pipeline."""
    for dir_path in [
        paths.data(),
        paths.data("results"),
        paths.interim(),
        paths.features(),
        paths.models(),
        paths.reports(),
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Source code directories (ensure they exist for later phases)
    for src_dir in [
        Path("src/pipeline"),
        Path("src/cli"),
    ]:
        src_dir.mkdir(parents=True, exist_ok=True)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="LLM‑Xive static‑dynamic gap analysis pipeline."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Create project directories and a tiny sample CSV result.",
    )
    parser.add_argument(
        "--swe_gym_url",
        type=str,
        help="URL to the SWE‑Gym parquet file.",
    )
    parser.add_argument(
        "--multi_swe_rl_url",
        type=str,
        help="URL to the Multi‑SWE‑RL JSONL file.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=".",
        help="Directory where pipeline artefacts will be placed.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=SEED,
        help="Random seed for reproducibility.",
    )
    args = parser.parse_args(argv)

    # Apply seed if overridden
    random.seed(args.seed)
    np.random.seed(args.seed)

    # Ensure directory skeleton exists
    ensure_project_dirs()

    if args.dry_run:
        # Minimal demonstration – write a tiny CSV.
        sample_path = paths.data("results", "sample_run.csv")
        from src.cli.run_pipeline import write_sample_result  # noqa: E402
        write_sample_result(sample_path)
        print(f"Dry‑run completed. Sample result at: {sample_path}")
        return 0

    # Full pipeline execution (currently only ingestion is implemented)
    if not args.swe_gym_url or not args.multi_swe_rl_url:
        log.error("Dataset URLs must be provided for full pipeline execution.")
        parser.print_help()
        return 1

    # Run ingestion
    from src.pipeline.ingest import ingest  # noqa: E402
    ingest(args.swe_gym_url, args.multi_swe_rl_url)

    print("Pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
