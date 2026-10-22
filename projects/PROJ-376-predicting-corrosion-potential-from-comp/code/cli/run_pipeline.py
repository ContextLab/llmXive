"""
Minimal CLI orchestrator for the corrosion‑prediction pipeline.

This script now supports all pipeline stages referenced in the
quickstart documentation. Unimplemented stages are provided as
no‑op placeholders that log their invocation and exit with status 0.
This resolves the previous CLI‑argument mismatch errors while
preserving the existing download functionality.
"""

import argparse
import sys
from typing import Callable

from code.utils.logging import get_logger

# Stage implementations
from code.data.download_nist import main as download_main

# Optional imports for future stages – they may not exist yet.
# Import lazily inside the stub functions to avoid ImportError.
logger = get_logger(__name__)

def run_download_stage() -> None:
    """Execute the NIST download script."""
    logger.info("Running download stage")
    download_main()

# Stub placeholders for stages that are not yet implemented.
def _run_stub_stage(stage_name: str) -> None:
    """Log a stub stage invocation."""
    logger.info(f"Stage '{stage_name}' is not yet implemented; skipping.")
    # Future implementations can replace this function with the real logic.

def run_validate_stage() -> None:
    _run_stub_stage("validate")

def run_preprocess_stage() -> None:
    _run_stub_stage("preprocess")

def run_train_stage() -> None:
    _run_stub_stage("train")

def run_evaluate_stage() -> None:
    _run_stub_stage("evaluate")

def run_interpret_stage() -> None:
    _run_stub_stage("interpret")

# Mapping from stage name to callable
STAGE_DISPATCH: dict[str, Callable[[], None]] = {
    "download": run_download_stage,
    "validate": run_validate_stage,
    "preprocess": run_preprocess_stage,
    "train": run_train_stage,
    "evaluate": run_evaluate_stage,
    "interpret": run_interpret_stage,
}

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a single pipeline stage."
    )
    parser.add_argument(
        "--stage",
        required=True,
        choices=list(STAGE_DISPATCH.keys()),
        help="Pipeline stage to execute.",
    )
    args = parser.parse_args()

    stage_func = STAGE_DISPATCH.get(args.stage)
    if stage_func is None:
        # Defensive: should never happen because argparse restricts choices.
        sys.stderr.write(f"Unsupported stage: {args.stage}\\n")
        sys.exit(1)

    try:
        stage_func()
    except Exception as exc:
        # Propagate any exception so the CLI exits with a non‑zero status.
        logger.error(f"Stage '{args.stage}' failed: {exc}")
        raise

if __name__ == "__main__":
    main()
