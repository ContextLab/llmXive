"""
Main entry point for the antibiotic resistance prediction pipeline.

This script orchestrates the pipeline stages in the order required by
task T101 and implements robust runtime and memory measurement as required
by task T102.

Runtime measurement:
  * start_time – ISO‑8601 timestamp when the pipeline starts
  * end_time   – ISO‑8601 timestamp when the pipeline finishes (or aborts)
  * duration_seconds – total elapsed time (float)
  * peak_memory_bytes – maximum RSS memory observed across the orchestrator
    process and any child processes spawned during subprocess calls.

If the duration exceeds 6 h (21600 s) or peak memory exceeds 7 GB,
the script exits with EXIT_LIMIT_EXCEEDED (code 5) after writing the
runtime report.
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

# Logging utilities
from utils.logging import init_pipeline_logging, get_logger

logger = init_pipeline_logging()

# ----------------------------------------------------------------------
# Exit‑code constants
# ----------------------------------------------------------------------
EXIT_SUCCESS = 0
EXIT_CONTRACT_FAILED = 1   # E001
EXIT_INSUFFICIENT_DATA = 4  # E004
EXIT_LIMIT_EXCEEDED = 5     # Exceeded runtime or memory limits

# Limits imposed by task T102
MAX_DURATION_SECONDS = 21600                # 6 hours
MAX_MEMORY_BYTES = 7 * 1024 ** 3            # 7 GB

# ----------------------------------------------------------------------
# Runtime tracking utilities
# ----------------------------------------------------------------------
class RuntimeTracker:
    """
    Tracks start/end timestamps and the maximum RSS memory observed.
    Memory is measured for the current process and any live child
    processes. The peak is updated after each stage (including after
    a subprocess finishes) to capture the highest value observed.
    """

    def __init__(self):
        self.start_time: datetime.datetime = datetime.datetime.now(
            datetime.timezone.utc
        )
        self.end_time: datetime.datetime | None = None
        self.peak_memory: int = self._current_rss()
        logger.debug(
            f"RuntimeTracker initialized – start_time={self.start_time.isoformat()}, "
            f"initial RSS={self.peak_memory} bytes"
        )

    def _current_rss(self) -> int:
        """
        Return the combined RSS of this process and any alive children.
        """
        try:
            proc = psutil.Process()
            rss = proc.memory_info().rss
            for child in proc.children(recursive=True):
                try:
                    rss += child.memory_info().rss
                except psutil.NoSuchProcess:
                    pass
            return rss
        except Exception as e:
            logger.warning(f"Unable to query RSS memory: {e}")
            return 0

    def update_peak(self) -> None:
        """Update the stored peak memory if the current RSS is higher."""
        current = self._current_rss()
        if current > self.peak_memory:
            logger.debug(
                f"New peak memory observed: {current} bytes (previous {self.peak_memory})"
            )
            self.peak_memory = current

    def finalize(self) -> None:
        """Record the end timestamp."""
        self.end_time = datetime.datetime.now(datetime.timezone.utc)

    def report(self) -> dict:
        """Return a dict suitable for JSON serialisation."""
        if self.end_time is None:
            self.finalize()
        duration = (self.end_time - self.start_time).total_seconds()
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": duration,
            "peak_memory_bytes": self.peak_memory,
        }

    def enforce_limits(self) -> None:
        """
        Abort the pipeline if either runtime or memory limits are exceeded.
        The function writes the runtime report before exiting.
        """
        report = self.report()
        duration = report["duration_seconds"]
        peak = report["peak_memory_bytes"]

        if duration > MAX_DURATION_SECONDS:
            logger.error(
                f"Pipeline duration {duration:.2f}s exceeds limit of {MAX_DURATION_SECONDS}s"
            )
            write_runtime_report(report)
            sys.exit(EXIT_LIMIT_EXCEEDED)

        if peak > MAX_MEMORY_BYTES:
            logger.error(
                f"Peak memory usage {peak} bytes exceeds limit of {MAX_MEMORY_BYTES} bytes"
            )
            write_runtime_report(report)
            sys.exit(EXIT_LIMIT_EXCEEDED)

# Global runtime tracker – instantiated once at script start
_runtime = RuntimeTracker()

# ----------------------------------------------------------------------
# Helper to run a subprocess and log its output
# ----------------------------------------------------------------------
def run_subprocess(command: list[str], description: str) -> int:
    """
    Execute *command* via subprocess.run, capture stdout/stderr,
    log the output, and return the exit code.
    """
    logger.info(f"Running stage: {description}")
    logger.debug(f"Command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        if result.stdout:
            logger.debug(result.stdout)
        if result.returncode != 0:
            logger.error(
                f"Stage '{description}' failed with exit code {result.returncode}"
            )
        else:
            logger.info(f"Stage '{description}' completed successfully")
        return result.returncode
    except Exception as e:
        logger.error(f"Exception while running '{description}': {e}")
        return 1
    finally:
        # Update peak memory after the subprocess finishes (whether success or not)
        _runtime.update_peak()

# ----------------------------------------------------------------------
# Individual pipeline stages
# ----------------------------------------------------------------------
def stage_ingest(args: argparse.Namespace) -> int:
    """Ingestion stage: download → metadata → feature matrix."""
    # 1. Download NCBI assemblies
    cmd_download = [
        sys.executable,
        "code/01_ingest/download_ncbi.py",
        "--bio_project",
        args.bio_project,
        "--max-isolates",
        str(args.n_isolates),
    ]
    rc = run_subprocess(cmd_download, "download_ncbi")
    if rc != 0:
        return rc

    # 2. Process metadata
    cmd_metadata = [sys.executable, "code/01_ingest/ingest_metadata.py"]
    rc = run_subprocess(cmd_metadata, "ingest_metadata")
    if rc != 0:
        return rc

    # 3. Build feature matrix
    cmd_feature = [sys.executable, "code/02_process/build_feature_matrix.py"]
    rc = run_subprocess(cmd_feature, "build_feature_matrix")
    return rc

def stage_contract_validation() -> int:
    """Run pytest on the contract tests. Abort on failure with E001."""
    cmd = [sys.executable, "-m", "pytest", "tests/contract/"]
    rc = run_subprocess(cmd, "contract_validation")
    if rc != 0:
        logger.error("Contract validation failed – aborting pipeline (E001).")
        sys.exit(EXIT_CONTRACT_FAILED)
    return rc

def stage_train(args: argparse.Namespace) -> int:
    """Model training stage."""
    cmd = [
        sys.executable,
        "code/03_model/train_models.py",
        "--antibiotic",
        args.antibiotic,
    ]
    return run_subprocess(cmd, "train_models")

def stage_validate(args: argparse.Namespace) -> int:
    """Validation stage: permutation test followed by sensitivity analysis."""
    # Resolve permutation count (may be a string like "[sufficient_permutations]")
    try:
        perms = int(args.permutations)
    except (ValueError, TypeError):
        logger.warning(
            f"Invalid permutations argument '{args.permutations}'. Falling back to 1000."
        )
        perms = 1000

    # 1. Phylogenetic permutation test
    cmd_perm = [
        sys.executable,
        "code/04_validate/phylo_permutation.py",
        "--antibiotic",
        args.antibiotic,
        "--permutations",
        str(perms),
    ]
    rc = run_subprocess(cmd_perm, "phylo_permutation")
    if rc != 0:
        return rc

    # 2. Sensitivity analysis
    cmd_sens = [
        sys.executable,
        "code/04_validate/sensitivity_analysis.py",
        "--antibiotic",
        args.antibiotic,
    ]
    return run_subprocess(cmd_sens, "sensitivity_analysis")

def stage_viz(args: argparse.Namespace) -> int:
    """Visualization stage: generate ROC and feature‑importance plots."""
    cmd = [
        sys.executable,
        "code/05_viz/generate_plots.py",
        "--antibiotic",
        args.antibiotic,
    ]
    return run_subprocess(cmd, "generate_plots")

def stage_hash_artifacts() -> int:
    """Final stage – compute SHA‑256 hashes for all data and code artifacts."""
    cmd = [sys.executable, "code/utils/hash_artifacts.py"]
    return run_subprocess(cmd, "hash_artifacts")

# ----------------------------------------------------------------------
# Argument parsing
# ----------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Antibiotic resistance prediction pipeline orchestrator"
    )
    parser.add_argument(
        "--stage",
        choices=[
            "ingest",
            "contract",
            "train",
            "validate",
            "viz",
            "hash",
            "full",
        ],
        default="full",
        help="Pipeline stage to execute",
    )
    parser.add_argument(
        "--n-isolates",
        type=int,
        default=1000,
        help="Number of isolates to download",
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
        help="Antibiotic class",
    )
    parser.add_argument(
        "--permutations",
        type=str,
        default="1000",
        help="Permutation count (integer or placeholder)",
    )
    return parser.parse_args()

# ----------------------------------------------------------------------
# Runtime report writer
# ----------------------------------------------------------------------
def write_runtime_report(report: dict | None = None) -> None:
    """
    Serialize the runtime report to ``data/processed/pipeline_runtime.json``.
    If *report* is ``None`` the global ``_runtime`` object is used.
    """
    if report is None:
        report = _runtime.report()
    runtime_path = paths.data("processed", "pipeline_runtime.json")
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(runtime_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Pipeline runtime written to {runtime_path}")
    except Exception as e:
        logger.error(f"Failed to write pipeline runtime report: {e}")

# ----------------------------------------------------------------------
# Main driver
# ----------------------------------------------------------------------
def main() -> int:
    args = parse_args()

    # Helper to run a stage and immediately write an updated runtime report.
    def run_and_report(stage_func, *stage_args):
        rc = stage_func(*stage_args)
        # Update peak memory already done inside run_subprocess / stage functions
        write_runtime_report()
        return rc

    # ------------------------------------------------------------------
    # Single‑stage execution (useful for debugging)
    # ------------------------------------------------------------------
    if args.stage == "ingest":
        return run_and_report(stage_ingest, args)
    if args.stage == "contract":
        return run_and_report(stage_contract_validation)
    if args.stage == "train":
        return run_and_report(stage_train, args)
    if args.stage == "validate":
        return run_and_report(stage_validate, args)
    if args.stage == "viz":
        return run_and_report(stage_viz, args)
    if args.stage == "hash":
        return run_and_report(stage_hash_artifacts)

    # ------------------------------------------------------------------
    # Full pipeline execution (default)
    # ------------------------------------------------------------------
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
        if rc != 0:
            # Record runtime before exiting so the user can see how far the
            # pipeline progressed.
            write_runtime_report()
            return rc

    # All stages succeeded – finalize runtime and enforce limits.
    _runtime.finalize()
    _runtime.enforce_limits()   # Will exit if limits exceeded
    write_runtime_report()
    return EXIT_SUCCESS

if __name__ == "__main__":
    sys.exit(main())