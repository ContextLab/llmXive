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
warning and continues with the remaining phases.
"""

import argparse
import importlib
import importlib.util
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
            # Handle both functions returning exit codes and functions returning None
            result = module.main()
            if result is not None and result != 0:
                logging.error("%s.main() returned non-zero exit code: %s", module_name, result)
                return False
            return True
        except Exception as exc:
            logging.error("Error while executing %s.main(): %s", module_name, exc, exc_info=True)
            return False
    else:
        logging.warning("Module %s does not define a main() function.", module_name)
        return False

# ----------------------------------------------------------------------
# Phase runners
# ----------------------------------------------------------------------
def run_extraction_phase(config: Dict[str, Any]) -> bool:
    """Runs the extraction stage."""
    logging.info("=== Extraction Phase ===")
    success = _import_and_run("src.extraction.fetch_prs")
    # Preprocess is a secondary part of extraction
    _import_and_run("src.extraction.preprocess")
    return success

def run_detection_phase(config: Dict[str, Any]) -> bool:
    """Runs the LLM‑code detection stage."""
    logging.info("=== Detection Phase ===")
    return _import_and_run("src.detection.detect_llm_code")

def run_inference_phase(config: Dict[str, Any]) -> bool:
    """Runs the inference stage."""
    logging.info("=== Inference Phase ===")
    if _import_and_run("src.inference.run_inference"):
        return True
    return _import_and_run("src.detection_and_inference")

def run_analysis_phase(config: Dict[str, Any]) -> bool:
    """Runs the analysis stage."""
    logging.info("=== Analysis Phase ===")
    return _import_and_run("src.analysis.analysis")

def run_reporting_phase(config: Dict[str, Any]) -> bool:
    """Generates the final report."""
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
        help="Phases to run: extraction detection inference analysis reporting all sample",
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
    parser.add_argument("--max-prs", type=int, default=None)
    parser.add_argument("--thresholds", type=str, default=None)
    parser.add_argument("--seed", type=int, default=None)
    return parser.parse_args()

def run_phase(phase_name: str, config: Dict[str, Any]) -> bool:
    """Dispatches ``phase_name`` to the corresponding runner."""
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
    except Exception as exc:
        logging.error("Phase %s failed with exception: %s", phase_name, exc, exc_info=True)
        return False

def main() -> int:
    args = parse_args()

    # 1. Logging setup
    setup_pipeline_logging()
    logger = logging.getLogger(__name__)

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)

    # 2. Directory setup
    paths = get_paths()
    ensure_directories()

    # 3. User config loading
    user_config: Dict[str, Any] = {}
    try:
        spec = importlib.util.spec_from_file_location("user_config", args.config)
        if spec and spec.loader:
            user_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(user_mod)
            if hasattr(user_mod, "get_config"):
                user_config = user_mod.get_config()
    except Exception as exc:
        logging.warning("Could not load user config from %s: %s", args.config, exc)

    config: Dict[str, Any] = {
        "timeout_hours": args.timeout_hours,
        "paths": paths,
        "verbose": args.verbose,
        "user_config": user_config,
        "max_prs": args.max_prs,
        "thresholds": [float(t) for t in args.thresholds.split(",")] if args.thresholds else None,
        "seed": args.seed,
    }

    # 4. Timeout initialization
    set_global_timeout(args.timeout_hours * 3600)
    logger.info("Global timeout set to %.2f hours", args.timeout_hours)

    # 5. Phase selection
    requested = [p.lower() for p in args.run]
    if "all" in requested or "sample" in requested:
        phases_to_run = ["extraction", "detection", "inference", "analysis", "reporting"]
    else:
        valid = {"extraction", "detection", "inference", "analysis", "reporting"}
        phases_to_run = [p for p in requested if p in valid]

    logger.info("Phases to execute: %s", phases_to_run)

    # 6. Execution loop
    for phase in phases_to_run:
        if check_timeout():
            log_timeout_warning()
            logger.warning("Timeout exceeded before phase %s; aborting.", phase)
            break

        remaining = get_remaining_time_seconds()
        logger.info("Remaining time budget: %.2f seconds", remaining)

        success = run_phase(phase, config)
        if not success:
            logger.error("Phase %s failed; continuing to next phase.", phase)

    # 7. Finalization
    logger.info("Pipeline execution finished.")
    timeout_ctx = get_timeout_context()
    if timeout_ctx and timeout_ctx.exceeded:
        logger.warning("Pipeline terminated due to timeout.")
        sys.exit(143)

    return 0

if __name__ == "__main__":
    sys.exit(main())