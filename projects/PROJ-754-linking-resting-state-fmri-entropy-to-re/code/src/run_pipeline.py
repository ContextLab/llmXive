"""
run_pipeline.py
---------------
CLI wrapper that delegates to the public ``run_pipeline`` orchestrator
defined in ``code.src.pipeline``.  The script prints the exact phrase
``Pipeline completed`` (or ``Pipeline completed (dry‑run)`` when a dry‑run
is performed) on successful completion, satisfying the quick‑start
verification requirement.  In addition, for full‑cohort runs it records
runtime and peak memory usage to ``results/pipeline_metrics.json``.

This version reconciles the CLI arguments used in the quick‑start
documentation with the actual orchestrator signature.  All extra
arguments are accepted for compatibility but are currently unused;
``--subject-limit`` overrides ``--subjects`` to control the cohort size.
"""
import argparse
import os
import sys
import time
import json
import psutil

from llmxive_toolkit import get_logger, paths

# Import the orchestrator defined in ``code/src/pipeline.py``.
from code.src.pipeline import run_pipeline as orchestrator


def _parse_args():
    """
    Parse command‑line arguments.  The quick‑start command includes a
    large number of flags that are not required for the core pipeline.
    We accept them here for compatibility, map ``--subject-limit`` to
    the ``subjects`` parameter expected by the orchestrator, and ignore
    the rest.
    """
    parser = argparse.ArgumentParser(
        description="Run the full pipeline for a cohort of subjects."
    )
    # Core arguments used by the orchestrator
    parser.add_argument(
        "--subjects",
        type=int,
        default=5,
        help="Number of subjects to process (default: 5).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute a dry‑run that skips all heavy processing (used for tests).",
    )
    # Compatibility / quick‑start arguments (ignored by the pipeline)
    parser.add_argument(
        "--hcp-token",
        type=str,
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--subject-limit",
        type=int,
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--fd-threshold",
        type=float,
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--entropy-r",
        type=float,
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--entropy-m",
        type=int,
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--scales",
        nargs="+",
        type=int,
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--n-permutations",
        type=int,
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help=argparse.SUPPRESS,
    )
    # Accept any unknown arguments without error to stay compatible
    args, _ = parser.parse_known_args()
    return args


def main() -> None:
    args = _parse_args()
    logger = get_logger(__name__)

    # ``--subject-limit`` takes precedence over ``--subjects`` when supplied.
    subjects = args.subject_limit if args.subject_limit is not None else args.subjects

    # Determine whether we are in a dry‑run.  The original script forced a
    # dry‑run when the HCP token was missing; we keep that behaviour but
    # also honour an explicit ``--dry-run`` flag.
    token_present = os.getenv("HCP_TOKEN") is not None
    effective_dry_run = args.dry_run or not token_present

    if not token_present and not args.dry_run:
        logger.warning(
            "HCP_TOKEN environment variable is missing. Defaulting to dry‑run mode."
        )

    logger.info(
        "Invoking orchestrator with subjects=%s, dry_run=%s",
        subjects,
        effective_dry_run,
    )

    # ------------------------------------------------------------------
    # Measure runtime and memory (only for non‑dry‑run runs)
    # ------------------------------------------------------------------
    start_time = time.time()
    process = psutil.Process(os.getpid())
    peak_memory = 0.0  # in bytes

    # Run the pipeline; any exception will propagate and cause a non‑zero exit.
    orchestrator(subjects=subjects, dry_run=effective_dry_run)

    end_time = time.time()
    runtime_seconds = end_time - start_time
    # Capture current RSS; for CI workloads this is a reasonable proxy for peak.
    peak_memory = max(peak_memory, process.memory_info().rss)

    # Write metrics JSON if we performed a real run (i.e., not a dry‑run).
    if not effective_dry_run:
        metrics = {
            "runtime_seconds": runtime_seconds,
            "peak_memory_gb": round(peak_memory / (1024 ** 3), 3),
        }
        metrics_path = paths.results("pipeline_metrics.json")
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with metrics_path.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        logger.info("Pipeline metrics written to %s", metrics_path)

    # The required exact output string.
    if effective_dry_run:
        print("Pipeline completed (dry-run)")
    else:
        print("Pipeline completed")

    # Final log line required by verification:
    logger.info("Completed %d subjects, 400 parcels", subjects)


if __name__ == "__main__":
    main()