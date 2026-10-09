"""
Main entry point for the antibiotic resistance prediction pipeline.

This script orchestrates the five pipeline stages:
  1. Ingestion
  2. Contract validation (pytest)
  3. Modeling (training)
  4. Validation (permutation + sensitivity)
  5. Versioning / state finalization (hash artifacts)

It can be invoked for a single stage (using --stage) or for the full
pipeline (default: run all stages in order).
"""

import argparse
import subprocess
import sys
from pathlib import Path

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
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    logger.debug(result.stdout)
    if result.returncode != 0:
        logger.error(f"Stage '{description}' failed with exit code {result.returncode}")
    else:
        logger.info(f"Stage '{description}' completed successfully")
    return result.returncode


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
        f"--max-isolates={args.n_isolates}"
    ]
    rc = run_subprocess(cmd_download, "download_ncbi")
    if rc != 0:
        return rc

    # 2. Process metadata
    cmd_metadata = [
        sys.executable,
        "code/01_ingest/ingest_metadata.py"
    ]
    rc = run_subprocess(cmd_metadata, "ingest_metadata")
    if rc != 0:
        return rc

    # 3. Build feature matrix
    cmd_feature = [
        sys.executable,
        "code/02_process/build_feature_matrix.py"
    ]
    rc = run_subprocess(cmd_feature, "build_feature_matrix")
    return rc


def stage_contract_validation() -> int:
    """
    Run pytest on the contract tests. Abort on failure.
    """
    cmd = [sys.executable, "-m", "pytest", "tests/contract/"]
    rc = run_subprocess(cmd, "contract_validation")
    if rc != 0:
        logger.error("Contract validation failed – aborting pipeline.")
        sys.exit(EXIT_CONTRACT_FAILED)
    return rc


def stage_train(args: argparse.Namespace) -> int:
    """
    Model training stage.
    Calls train_models.py with the specified antibiotic class.
    """
    cmd = [
        sys.executable,
        "code/03_model/train_models.py",
        f"--antibiotic={args.antibiotic}"
    ]
    return run_subprocess(cmd, "train_models")


def stage_validate(args: argparse.Namespace) -> int:
    """
    Validation stage:
      - phylo_permutation.py
      - sensitivity_analysis.py
    """
    # Permutation test
    cmd_perm = [
        sys.executable,
        "code/04_validate/phylo_permutation.py",
        f"--antibiotic={args.antibiotic}",
        f"--permutations={args.permutations}"
    ]
    rc = run_subprocess(cmd_perm, "phylo_permutation")
    if rc != 0:
        return rc

    # Sensitivity analysis
    cmd_sens = [
        sys.executable,
        "code/04_validate/sensitivity_analysis.py",
        f"--antibiotic={args.antibiotic}"
    ]
    return run_subprocess(cmd_sens, "sensitivity_analysis")


def stage_viz(args: argparse.Namespace) -> int:
    """
    Visualization stage – generate plots for the specified antibiotic.
    """
    cmd = [
        sys.executable,
        "code/05_viz/generate_plots.py",
        f"--antibiotic={args.antibiotic}"
    ]
    return run_subprocess(cmd, "generate_plots")


def stage_hash_artifacts() -> int:
    """
    Final stage – compute SHA256 hashes for all data and code artifacts.
    """
    cmd = [
        sys.executable,
        "code/utils/hash_artifacts.py"
    ]
    return run_subprocess(cmd, "hash_artifacts")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Antibiotic resistance prediction pipeline orchestrator"
    )
    parser.add_argument(
        "--stage",
        choices=["ingest", "contract", "train", "validate", "viz", "hash", "full"],
        default="full",
        help="Pipeline stage to execute (default: full run)"
    )
    parser.add_argument(
        "--n-isolates",
        type=int,
        default=1000,
        help="Number of isolates to download during ingestion"
    )
    parser.add_argument(
        "--bio_project",
        type=str,
        default="PRJNA528852",
        help="NCBI BioProject identifier"
    )
    parser.add_argument(
        "--antibiotic",
        type=str,
        default="ciprofloxacin",
        help="Antibiotic class for training/validation/viz"
    )
    parser.add_argument(
        "--permutations",
        type=int,
        default=1000,
        help="Number of permutations for the permutation test"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.stage == "ingest":
        return stage_ingest(args)

    if args.stage == "contract":
        return stage_contract_validation()

    if args.stage == "train":
        return stage_train(args)

    if args.stage == "validate":
        return stage_validate(args)

    if args.stage == "viz":
        return stage_viz(args)

    if args.stage == "hash":
        return stage_hash_artifacts()

    # Full pipeline execution
    rc = stage_ingest(args)
    if rc != 0:
        return rc

    # Contract validation is mandatory and aborts on failure
    stage_contract_validation()

    rc = stage_train(args)
    if rc != 0:
        return rc

    rc = stage_validate(args)
    if rc != 0:
        return rc

    rc = stage_viz(args)
    if rc != 0:
        return rc

    rc = stage_hash_artifacts()
    return rc


if __name__ == "__main__":
    sys.exit(main())
