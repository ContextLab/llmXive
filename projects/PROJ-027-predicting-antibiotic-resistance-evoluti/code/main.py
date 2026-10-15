"""
Main entry point for the antibiotic resistance prediction pipeline.

This script orchestrates the pipeline stages in the order required by
task T101:
  1. Ingestion (download_ncbi, ingest_metadata, build_feature_matrix)
  2. Contract validation (pytest tests/contract/) - Aborts with E001 on failure
  3. Modeling (train_models)
  4. Validation (phylo_permutation, sensitivity_analysis)
  5. Visualization (generate_plots)
  6. Versioning / state finalization (hash_artifacts)

It records runtime statistics (start/end timestamps, duration,
peak RSS memory usage) and writes them to `data/processed/pipeline_runtime.json`.
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
EXIT_CONTRACT_FAILED = 1   # E001
EXIT_INSUFFICIENT_DATA = 4  # E004
EXIT_LIMIT_EXCEEDED = 5     # Exceeded runtime or memory limits

# Limits required by task T102
MAX_DURATION_SECONDS = 21600                # 6 hours
MAX_MEMORY_BYTES = 7 * 1024 ** 3            # 7 GB

def run_subprocess(command: list, description: str) -> int:
    """
    Helper to run a subprocess command, log its output, and return the exit code.
    """
    logger.info(f"Running stage: {description}")
    logger.debug(f"Command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False
        )
        logger.debug(result.stdout)
        if result.returncode != 0:
            logger.error(f"Stage '{description}' failed with exit code {result.returncode}")
        else:
            logger.info(f"Stage '{description}' completed successfully")
        return result.returncode
    except Exception as e:
        logger.error(f"Exception occurred while running '{description}': {e}")
        return 1

# Global variables for runtime measurement
_START_TIME = datetime.datetime.now(datetime.timezone.utc)
_PEAK_MEMORY = psutil.Process().memory_info().rss  # bytes

def _update_peak_memory() -> None:
    """Update the global peak memory measurement including child processes."""
    global _PEAK_MEMORY
    try:
        current = psutil.Process().memory_info().rss
        for child in psutil.Process().children(recursive=True):
            try:
                current += child.memory_info().rss
            except psutil.NoSuchProcess:
                pass
        if current > _PEAK_MEMORY:
            _PEAK_MEMORY = current
    except Exception as e:
        logger.warning(f"Unable to update peak memory: {e}")

def stage_ingest(args: argparse.Namespace) -> int:
    """Ingestion stage: download -> metadata -> feature matrix."""
    # 1. Download NCBI assemblies
    cmd_download = [
        sys.executable, "code/01_ingest/download_ncbi.py",
        f"--bio_project={args.bio_project}",
        f"--max-isolates={args.n_isolates}",
    ]
    rc = run_subprocess(cmd_download, "download_ncbi")
    _update_peak_memory()
    if rc != 0: return rc

    # 2. Process metadata
    cmd_metadata = [sys.executable, "code/01_ingest/ingest_metadata.py"]
    rc = run_subprocess(cmd_metadata, "ingest_metadata")
    _update_peak_memory()
    if rc != 0: return rc

    # 3. Build feature matrix
    cmd_feature = [sys.executable, "code/02_process/build_feature_matrix.py"]
    rc = run_subprocess(cmd_feature, "build_feature_matrix")
    _update_peak_memory()
    return rc

def stage_contract_validation() -> int:
    """Run pytest on the contract tests. Abort on failure with E001."""
    cmd = [sys.executable, "-m", "pytest", "tests/contract/"]
    rc = run_subprocess(cmd, "contract_validation")
    if rc != 0:
        logger.error("Contract validation failed – aborting pipeline (E001).")
        sys.exit(EXIT_CONTRACT_FAILED)
    _update_peak_memory()
    return rc

def stage_train(args: argparse.Namespace) -> int:
    """Model training stage."""
    cmd = [
        sys.executable, "code/03_model/train_models.py",
        f"--antibiotic={args.antibiotic}",
    ]
    rc = run_subprocess(cmd, "train_models")
    _update_peak_memory()
    return rc

def stage_validate(args: argparse.Namespace) -> int:
    """Validation stage: permutation test & sensitivity analysis."""
    try:
        perms = int(args.permutations)
    except (ValueError, TypeError):
        logger.warning(f"Invalid permutations argument '{args.permutations}'. Falling back to 1000.")
        perms = 1000

    # Permutation test
    cmd_perm = [
        sys.executable, "code/04_validate/phylo_permutation.py",
        f"--antibiotic={args.antibiotic}",
        f"--permutations={perms}",
    ]
    rc = run_subprocess(cmd_perm, "phylo_permutation")
    _update_peak_memory()
    if rc != 0: return rc

    # Sensitivity analysis
    cmd_sens = [
        sys.executable, "code/04_validate/sensitivity_analysis.py",
        f"--antibiotic={args.antibiotic}",
    ]
    rc = run_subprocess(cmd_sens, "sensitivity_analysis")
    _update_peak_memory()
    return rc

def stage_viz(args: argparse.Namespace) -> int:
    """Visualization stage: generate ROC and importance plots."""
    cmd = [
        sys.executable, "code/05_viz/generate_plots.py",
        f"--antibiotic={args.antibiotic}",
    ]
    rc = run_subprocess(cmd, "generate_plots")
    _update_peak_memory()
    return rc

def stage_hash_artifacts() -> int:
    """Final stage – compute SHA256 hashes for all data and code artifacts."""
    cmd = [sys.executable, "code/utils/hash_artifacts.py"]
    rc = run_subprocess(cmd, "hash_artifacts")
    _update_peak_memory()
    return rc

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Antibiotic resistance prediction pipeline orchestrator")
    parser.add_argument("--stage", choices=["ingest", "contract", "train", "validate", "viz", "hash", "full"],
                         default="full", help="Pipeline stage to execute")
    parser.add_argument("--n-isolates", type=int, default=1000, help="Number of isolates to download")
    parser.add_argument("--bio_project", type=str, default="PRJNA528852", help="NCBI BioProject identifier")
    parser.add_argument("--antibiotic", type=str, default="ciprofloxacin", help="Antibiotic class")
    parser.add_argument("--permutations", type=str, default="1000", help="Permutation count")
    return parser.parse_args()

def _write_runtime_report() -> None:
    """Write the runtime JSON report and enforce limits (T102)."""
    end_time = datetime.datetime.now(datetime.timezone.utc)
    duration = (end_time - _START_TIME).total_seconds()

    if duration > MAX_DURATION_SECONDS:
        logger.error(f"Pipeline duration {duration:.2f}s exceeds limit of {MAX_DURATION_SECONDS}s")
        sys.exit(EXIT_LIMIT_EXCEEDED)

    if _PEAK_MEMORY > MAX_MEMORY_BYTES:
        logger.error(f"Peak memory usage {_PEAK_MEMORY} bytes exceeds limit of {MAX_MEMORY_BYTES} bytes")
        sys.exit(EXIT_LIMIT_EXCEEDED)

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

    def run_and_report(stage_func, *stage_args):
        rc = stage_func(*stage_args)
        _write_runtime_report()
        return rc

    if args.stage == "ingest": return run_and_report(stage_ingest, args)
    if args.stage == "contract": return run_and_report(stage_contract_validation)
    if args.stage == "train": return run_and_report(stage_train, args)
    if args.stage == "validate": return run_and_report(stage_validate, args)
    if args.stage == "viz": return run_and_report(stage_viz, args)
    if args.stage == "hash": return run_and_report(stage_hash_artifacts)

    # Full pipeline execution sequence (T101)
    stages = [
        (stage_ingest, (args,)),
        (stage_contract_validation, ()),
        (stage_train, (args,)),
        (stage_validate, (args,)),
        (stage_viz, (args,)),
        (stage_hash_artifacts, ()),
    ]

    for func, func_args in stages:
        rc = func(*func_args)
        _update_peak_memory()
        if rc != 0:
            _write_runtime_report()
            return rc
    
    _write_runtime_report()
    return 0

if __name__ == "__main__":
    sys.exit(main())
