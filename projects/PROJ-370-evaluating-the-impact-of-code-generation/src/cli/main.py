"""
CLI entry point for the LLM impact evaluation pipeline.

This script wires together the individual pipeline phases:
  - extraction
  - detection
  - inference
  - analysis
  - reporting

It respects the global timeout wrapper (src.utils.timeout_wrapper) and
uses the structured logger (src.utils.logger).  The implementation is
defensive: if a phase module cannot be imported, the pipeline logs a
warning and continues with the remaining phases.  This allows the CLI
to be executed even when only a subset of the pipeline has been
implemented.
"""

import argparse
import importlib
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Timeout and logging utilities
from src.utils.timeout_wrapper import (
    set_global_timeout,
    check_timeout,
    get_remaining_time_seconds,
    log_timeout_warning,
    get_timeout_context,
)
from src.utils.logger import (
    setup_pipeline_logging,
    increment_pr_processed,
    increment_pr_skipped,
)

# Configuration helpers
from config.settings import get_paths, ensure_directories, get_config

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _import_and_run(module_name: str) -> bool:
    """
    Import ``module_name`` and, if it defines a ``main`` function,
    execute it.

    Returns ``True`` if the module was imported and the ``main`` function
    ran without raising an exception, otherwise ``False``.
    """
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        logging.warning("Phase module %s could not be imported: %s", module_name, exc)
        return False

    if hasattr(module, "main"):
        try:
            logging.info("Running %s.main()", module_name)
            module.main()
            return True
        except Exception as exc:  # pragma: no cover – defensive
            logging.error("Error while executing %s.main(): %s", module_name, exc, exc_info=True)
            return False
    else:
        logging.warning("Module %s does not define a main() function.", module_name)
        return False

# ----------------------------------------------------------------------
# Phase runners
# ----------------------------------------------------------------------
def run_extraction_phase(config: Dict[str, Any]) -> bool:
    """
    Runs the extraction stage.  It attempts to execute the two
    extraction entry points that exist in the current code base:

    * src.extraction.fetch_prs.main()
    * src.extraction.preprocess.main()   (if present)
    """
    logging.info("=== Extraction Phase ===")
    success = _import_and_run("src.extraction.fetch_prs")
    # ``preprocess`` may not be implemented yet – we ignore its failure.
    _import_and_run("src.extraction.preprocess")
    return success

def run_detection_phase(config: Dict[str, Any]) -> bool:
    """
    Runs the LLM‑code detection stage.
    """
    logging.info("=== Detection Phase ===")
    return _import_and_run("src.detection.detect_llm_code")

def run_inference_phase(config: Dict[str, Any]) -> bool:
    """
    Runs the inference stage.  The concrete implementation may live in
    either ``src.inference.run_inference`` or the combined script
    ``src.detection_and_inference``.  Both are tried in order.
    """
    logging.info("=== Inference Phase ===")
    if _import_and_run("src.inference.run_inference"):
        return True
    # Fallback to the combined script used in earlier drafts.
    return _import_and_run("src.detection_and_inference")

def run_analysis_phase(config: Dict[str, Any]) -> bool:
    """
    Runs the analysis stage (alignment, metric computation, statistical tests).
    """
    logging.info("=== Analysis Phase ===")
    return _import_and_run("src.analysis.analysis")

def run_reporting_phase(config: Dict[str, Any]) -> bool:
    """
    Generates the final markdown report and a machine‑readable copy of the
    metrics.
    """
    logging.info("=== Reporting Phase ===")
    return _import_and_run("src.reporting.generate_report")

# ----------------------------------------------------------------------
# Argument parsing
# ----------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LLM Code Impact Analysis Pipeline"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/settings.py",
        help="Path to the configuration module (default: config/settings.py)",
    )
    parser.add_argument(
        "--run",
        type=str,
        nargs="+",
        default=["all"],
        help=(
            "Space‑separated list of phases to run. "
            "Valid values: extraction detection inference analysis reporting all sample. "
            "'sample' runs the full pipeline on a tiny demo dataset (if such a dataset exists)."
        ),
    )
    parser.add_argument(
        "--timeout-hours",
        type=float,
        default=6.0,
        help="Global timeout limit in hours (default: 6.0)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )
    # Compatibility arguments that were previously documented in the
    # quickstart but not originally supported.  They are accepted here
    # and stored in the config dictionary for downstream phases that may
    # wish to use them.
    parser.add_argument(
        "--max-prs",
        type=int,
        default=None,
        help="Maximum number of PRs to process (optional, stored in config)",
    )
    parser.add_argument(
        "--thresholds",
        type=str,
        default=None,
        help="Comma‑separated list of similarity thresholds (optional, stored in config)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (optional, stored in config)",
    )
    return parser.parse_args()

# ----------------------------------------------------------------------
# Core orchestration
# ----------------------------------------------------------------------
def run_phase(phase_name: str, config: Dict[str, Any]) -> bool:
    """
    Dispatches ``phase_name`` to the corresponding runner.
    Returns ``True`` on success, ``False`` otherwise.
    """
    runners = {
        "extraction": run_extraction_phase,
        "detection": run_detection_phase,
        "inference": run_inference_phase,
        "analysis": run_analysis_phase,
        "reporting": run_reporting_phase,
    }

    runner = runners.get(phase_name)
    if runner is None:
        logging.error("Unknown phase requested: %s", phase_name)
        return False

    try:
        return runner(config)
    except Exception as exc:  # pragma: no cover – defensive
        logging.error(
            "Phase %s failed with exception: %s", phase_name, exc, exc_info=True
        )
        return False

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    args = parse_args()

    # ------------------------------------------------------------------
    # Logging configuration
    # ------------------------------------------------------------------
    setup_pipeline_logging()
    logger = logging.getLogger(__name__)

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.debug("Verbose logging enabled.")

    # ------------------------------------------------------------------
    # Ensure required directory tree exists
    # ------------------------------------------------------------------
    paths = get_paths()
    ensure_directories()

    # ------------------------------------------------------------------
    # Load optional user configuration (if the supplied module defines
    # ``get_config`` it will be used; otherwise we fall back to defaults).
    # ------------------------------------------------------------------
    user_config: Dict[str, Any] = {}
    try:
        spec = importlib.util.spec_from_file_location("user_config", args.config)
        if spec and spec.loader:
            user_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(user_mod)
            if hasattr(user_mod, "get_config"):
                user_config = user_mod.get_config()
                logging.debug("User config loaded: %s", user_config)
    except Exception as exc:  # pragma: no cover – defensive
        logging.warning(
            "Could not load user config from %s: %s", args.config, exc
        )

    # ------------------------------------------------------------------
    # Global pipeline configuration dictionary
    # ------------------------------------------------------------------
    config: Dict[str, Any] = {
        "timeout_hours": args.timeout_hours,
        "paths": paths,
        "verbose": args.verbose,
        "user_config": user_config,
        # Compatibility parameters – downstream code may read them.
        "max_prs": args.max_prs,
        "thresholds": (
            [float(t) for t in args.thresholds.split(",")]
            if args.thresholds
            else None
        ),
        "seed": args.seed,
    }

    # ------------------------------------------------------------------
    # Initialise the global timeout wrapper
    # ------------------------------------------------------------------
    set_global_timeout(args.timeout_hours * 3600)  # convert hours → seconds
    logger.info("Global timeout set to %.2f hours", args.timeout_hours)

    # ------------------------------------------------------------------
    # Determine which phases to run
    # ------------------------------------------------------------------
    requested = [p.lower() for p in args.run]
    if "all" in requested:
        phases_to_run = [
            "extraction",
            "detection",
            "inference",
            "analysis",
            "reporting",
        ]
    elif "sample" in requested:
        # ``sample`` is treated as a shortcut for the full pipeline on a
        # tiny dataset.  The underlying phase modules are responsible for
        # limiting themselves to the sample data.
        phases_to_run = [
            "extraction",
            "detection",
            "inference",
            "analysis",
            "reporting",
        ]
    else:
        # Preserve order but filter unknown entries
        valid = {
            "extraction",
            "detection",
            "inference",
            "analysis",
            "reporting",
        }
        phases_to_run = [p for p in requested if p in valid]

    logger.info("Phases to execute: %s", phases_to_run)

    # ------------------------------------------------------------------
    # Execution loop with timeout enforcement
    # ------------------------------------------------------------------
    for phase in phases_to_run:
        # Global timeout check before starting a new phase
        if check_timeout():
            log_timeout_warning()
            logger.warning(
                "Timeout exceeded before phase %s; aborting remaining phases.",
                phase,
            )
            break

        remaining = get_remaining_time_seconds()
        logger.info("Remaining time budget: %.2f seconds", remaining)

        success = run_phase(phase, config)
        if not success:
            # Log the failure but continue with remaining phases so that
            # the CLI can still exit cleanly (useful for sample runs).
            logger.error("Phase %s failed; continuing to next phase.", phase)

    # ------------------------------------------------------------------
    # Finalisation
    # ------------------------------------------------------------------
    logger.info("Pipeline execution finished.")
    timeout_ctx = get_timeout_context()
    if timeout_ctx and getattr(timeout_ctx, "exceeded", False):
        logger.warning("Pipeline terminated due to timeout.")
        sys.exit(143)  # Standard timeout exit code as per FR‑013

    return 0

if __name__ == "__main__":
    sys.exit(main())
