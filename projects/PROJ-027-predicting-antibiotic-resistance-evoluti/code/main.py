"""
Main entry point for the antibiotic resistance prediction pipeline.

This script orchestrates the pipeline stages:
  1. Ingestion
  2. Modeling (training)
  3. Validation (permutation test + sensitivity analysis)
  4. Visualization
  5. Contract validation (pytest) – executed **after** all data‑producing stages
  6. Versioning / state finalization (hash artifacts)

It records runtime statistics (start/end timestamps, duration,
and peak RSS memory usage) and writes them to
`data/processed/pipeline_runtime.json`.  If any stage fails, the
script exits with a non‑zero code; contract validation aborts the
pipeline with a dedicated exit code (E001 → 1).
"""

import argparse
import subprocess
import sys
import json
import datetime
from pathlib import Path

import psutil

# llmxive toolkit helpers for path creation
from llmxive_toolkit import paths

# Initialize pipeline-wide logging
from utils.logging import init_pipeline_logging, get_logger

logger = init_pipeline_logging()

# Constants for exit codes
EXIT_CONTRACT_FAILED = 1  # E001 as per spec (mapped to 1)
EXIT_INSUFFICIENT_DATA = 4  # E004 (not used directly here)


def run_subprocess(command: list, description: str) -> int:
    """
    Helper to run a subprocess command, log its output, and return the exit code.
    """
    logger.info(f"Running stage: {description}")
    logger.debug(f"Command: {' '.join(command)}")
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    logger.debug(result.stdout)
    if result.returncode != 0:
        logger.error(
            f"Stage '{description}' failed with exit code {result.returncode}"
        )
    else:
        logger.info(f"Stage '{description}' completed successfully")
    return result.returncode


# Global variables for runtime measurement
_START_TIME = datetime.datetime.now(datetime.timezone.utc)
_PEAK_MEMORY = psutil.Process().memory_info().rss  # bytes


def _update_peak_memory() -> None:
    """Update the global peak memory measurement if current usage is higher."""
    global _PEAK_MEMORY
    try:
        current = psutil.Process().memory_info().rss
        if current > _PEAK_MEMORY:
            _PEAK_MEMORY = current
    except Exception as e:
        logger.warning(f"Unable to update peak memory: {e}")


def stage_ingest(args: argparse.Namespace) -> int:
    """
    Ingestion stage:
      - download_ncbi.py
      - ingest_metadata.py
      - build_feature_matrix.py
    """
    # 1. Download NCBI assemblies
    cmd_download = [
        sys.executable,
        "code/01_ingest/download_ncbi.py",
        f"--bio_project={args.bio_project}",
        f"--max-isolates={args.n_isolates}",
    ]
    rc = run_subprocess(cmd_download, "download_ncbi")
    _update_peak_memory()
    if rc != 0:
        return rc

    # 2. Process metadata
    cmd_metadata = [
        sys.executable,
        "code/01_ingest/ingest_metadata.py",
    ]
    rc = run_subprocess(cmd_metadata, "ingest_metadata")
    _update_peak_memory()
    if rc != 0:
        return rc

    # 3. Build feature matrix
    cmd_feature = [
        sys.executable,
        "code/02_process/build_feature_matrix.py",
    ]
    rc = run_subprocess(cmd_feature, "build_feature_matrix")
    _update_peak_memory()
    return rc


def stage_train(args: argparse.Namespace) -> int:
    """
    Model training stage.
    Calls train_models.py with the specified antibiotic class.
    """
    cmd = [
        sys.executable,
        "code/03_model/train_models.py",
        f"--antibiotic={args.antibiotic}",
    ]
    rc = run_subprocess(cmd, "train_models")
    _update_peak_memory()
    return rc


def stage_validate(args: argparse.Namespace) -> int:
    """
    Validation stage:
      - phylo_permutation.py
      - sensitivity_analysis.py
    """
    # Ensure permutations is an integer; the quickstart guide sometimes
    # uses the placeholder "[sufficient_permutations]".
    try:
        perms = int(args.permutations)
    except (ValueError, TypeError):
        logger.warning(
            f"Invalid permutations argument '{args.permutations}'. "
            "Falling back to default 1000."
        )
        perms = 1000

    # Permutation test
    cmd_perm = [
        sys.executable,
        "code/04_validate/phylo_permutation.py",
        f"--antibiotic={args.antibiotic}",
        f"--permutations={perms}",
    ]
    rc = run_subprocess(cmd_perm, "phylo_permutation")
    _update_peak_memory()
    if rc != 0:
        return rc

    # Sensitivity analysis
    cmd_sens = [
        sys.executable,
        "code/04_validate/sensitivity_analysis.py",
        f"--antibiotic={args.antibiotic}",
    ]
    rc = run_subprocess(cmd_sens, "sensitivity_analysis")
    _update_peak_memory()
    return rc


def stage_viz(args: argparse.Namespace) -> int:
    """
    Visualization stage – generate plots for the specified antibiotic.
    """
    cmd = [
        sys.executable,
        "code/05_viz/generate_plots.py",
        f"--antibiotic={args.antibiotic}",
    ]
    rc = run_subprocess(cmd, "generate_plots")
    _update_peak_memory()
    return rc


def stage_contract_validation() -> int:
    """
    Run pytest on the contract tests. Abort on failure.
    """
    cmd = ["pytest", "tests/contract/"]
    rc = run_subprocess(cmd, "contract_validation")
    if rc != 0:
        logger.error("Contract validation failed – aborting pipeline.")
        sys.exit(EXIT_CONTRACT_FAILED)
    _update_peak_memory()
    return rc


def stage_hash_artifacts() -> int:
    """
    Final stage – compute SHA256 hashes for all data and code artifacts.
    """
    cmd = [
        sys.executable,
        "code/utils/hash_artifacts.py",
    ]
    rc = run_subprocess(cmd, "hash_artifacts")
    _update_peak_memory()
    return rc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Antibiotic resistance prediction pipeline orchestrator"
    )
    parser.add_argument(
        "--stage",
        choices=[
            "ingest",
            "train",
            "validate",
            "viz",
            "contract",
            "hash",
            "full",
        ],
        default="full",
        help="Pipeline stage to execute (default: full run)",
    )
    parser.add_argument(
        "--n-isolates",
        type=int,
        default=1000,
        help="Number of isolates to download during ingestion",
    )
    parser.add_argument(
        "--bio_project",
        type=str,
        default="PRJNA528852",
        help="NCBI BioProject identifier",
    )
    parser.add_argument(
        "--antibiotic",
        type=str,
        default="ciprofloxacin",
        help="Antibiotic class for training/validation/viz",
    )
    # Accept any string; we coerce to int later.
    parser.add_argument(
        "--permutations",
        type=str,
        default="1000",
        help="Number of permutations for the permutation test (integer)",
    )
    return parser.parse_args()


def _write_runtime_report() -> None:
    """
    Write the runtime JSON report to `data/processed/pipeline_runtime.json`.
    """
    end_time = datetime.datetime.now(datetime.timezone.utc)
    duration = (end_time - _START_TIME).total_seconds()

    runtime_path = paths.data("processed", "pipeline_runtime.json")
    runtime_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "start_time": _START_TIME.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": duration,
        "peak_memory_bytes": _PEAK_MEMORY,
    }

    try:
        with open(runtime_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Pipeline runtime written to {runtime_path}")
    except Exception as e:
        logger.error(f"Failed to write pipeline runtime report: {e}")


def main() -> int:
    args = parse_args()

    # Helper to run a stage and write the runtime report afterwards
    def run_and_report(stage_func, *stage_args):
        rc = stage_func(*stage_args)
        _write_runtime_report()
        return rc

    if args.stage == "ingest":
        return run_and_report(stage_ingest, args)

    if args.stage == "train":
        return run_and_report(stage_train, args)

    if args.stage == "validate":
        return run_and_report(stage_validate, args)

    if args.stage == "viz":
        return run_and_report(stage_viz, args)

    if args.stage == "contract":
        return run_and_report(stage_contract_validation)

    if args.stage == "hash":
        return run_and_report(stage_hash_artifacts)

    # Full pipeline execution – note the reordered contract validation
    rc = stage_ingest(args)
    if rc != 0:
        return rc

    rc = stage_train(args)
    if rc != 0:
        return rc

    rc = stage_validate(args)
    if rc != 0:
        return rc

    rc = stage_viz(args)
    if rc != 0:
        return rc

    # Contract validation **after** all data‑producing stages
    rc = stage_contract_validation()
    if rc != 0:
        return rc

    rc = stage_hash_artifacts()
    return rc


if __name__ == "__main__":
    sys.exit(main())