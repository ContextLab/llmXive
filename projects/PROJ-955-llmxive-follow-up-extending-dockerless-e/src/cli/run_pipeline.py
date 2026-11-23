"""Run the LLM-Xive static-dynamic gap analysis pipeline.

Phase 0 (this file): create the project directory skeleton, pin the
global random seed, and provide a ``--dry-run`` mode that writes a
tiny result file ``data/results/sample_run.csv`` (4 rows) and prints
its path. Later tasks extend ``main`` with the full pipeline
(ingestion, graph extraction, feature engineering, model training,
error mining) behind the same CLI.
"""
import argparse
import csv
import random
import sys
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
    """Create all top-level directories required by the pipeline."""
    root = paths.root
    for dir_path in [
        paths.data(),
        paths.data("results"),
        root / "interim",
        root / "features",
        root / "models",
        root / "reports",
        root / "src" / "pipeline",
        root / "src" / "cli",
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)


def write_sample_result(path: Path) -> None:
    """Write the tiny dry-run result CSV (4 data rows, <= 10 rows)."""
    rows = [
        {"patch_id": "patch_001", "true_label": "pass",
         "predicted_label": "pass", "predicted_prob": 0.95},
        {"patch_id": "patch_002", "true_label": "fail",
         "predicted_label": "fail", "predicted_prob": 0.92},
        {"patch_id": "patch_003", "true_label": "pass",
         "predicted_label": "fail", "predicted_prob": 0.40},
        {"patch_id": "patch_004", "true_label": "fail",
         "predicted_label": "pass", "predicted_prob": 0.55},
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "patch_id", "true_label", "predicted_label",
                "predicted_prob",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="LLM-Xive static-dynamic gap analysis pipeline."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Create project directories and a tiny sample CSV result.",
    )
    parser.add_argument(
        "--swe_gym_url",
        type=str,
        help="URL to the SWE-Gym parquet file.",
    )
    parser.add_argument(
        "--multi_swe_rl_url",
        type=str,
        help="URL to the Multi-SWE-RL JSONL file.",
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
    parser.add_argument(
        "--sample_fraction",
        type=float,
        default=None,
        help="Fraction of the dataset to sample (0‑1). Ignored in this version.",
    )
    
    # Use parse_known_args to avoid failures from inline comments in shell scripts
    args, _ = parser.parse_known_args(argv)

    # Apply seed (also honors an overridden value)
    random.seed(args.seed)
    np.random.seed(args.seed)

    # Ensure directory skeleton exists
    ensure_project_dirs()

    if args.dry_run:
        sample_path = paths.data("results", "sample_run.csv")
        write_sample_result(sample_path)
        print(f"Dry-run completed. Sample result at: {sample_path}")
        return 0

    # Full pipeline execution (ingestion is implemented in a later
    # task; it is imported lazily so the dry-run needs no extra deps).
    if not args.swe_gym_url or not args.multi_swe_rl_url:
        log.error(
            "Dataset URLs must be provided for full pipeline execution."
        )
        parser.print_help()
        return 1

    from src.pipeline.ingest import ingest  # noqa: E402
    ingest(args.swe_gym_url, args.multi_swe_rl_url)

    print("Pipeline completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
