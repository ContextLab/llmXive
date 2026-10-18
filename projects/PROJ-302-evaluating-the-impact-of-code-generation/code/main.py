"""
Main entry point for the evaluation pipeline with runtime instrumentation.

This script initializes the RuntimeRecorder with all required pipeline stages,
wraps each stage in a context manager that records start/end timestamps,
and invokes the corresponding stage implementation (if available).

The stages are:
  1. data_acquisition
  2. prompt_engineering
  3. synthetic_generation
  4. feature_extraction
  5. timestamp_simulation
  6. matching
  7. analysis
  8. sensitivity
  9. visualization
  10. report_generation

Each stage module is expected to expose a ``main`` function that performs the
work for that stage. If a module or its ``main`` function is missing, the
stage is still timed (the timer will record the brief duration of the
attempted import) and a warning is logged, allowing the pipeline to continue.
"""

import importlib
import argparse
import sys
import logging
from pathlib import Path

from llmxive_toolkit import get_logger
from code.runtime import init_runtime, stage, write_report

log = get_logger(__name__)

# Ensure the ``logs`` directory exists before any stage that may create
# file handlers (e.g., ``code.analysis.matching``) is imported.
Path("logs").mkdir(parents=True, exist_ok=True)

# Mapping from stage name to the module that implements it.
# Adjust these imports if the actual module names differ.
STAGE_MODULES = {
    "data_acquisition": "code.data_acquisition",
    "prompt_engineering": "code.prompt_engineering",
    "synthetic_generation": "code.synthetic_generation",
    "feature_extraction": "code.feature_extraction",
    "timestamp_simulation": "code.timestamp_simulation",
    "matching": "code.analysis.matching",
    "analysis": "code.analysis.statistical_test",
    "sensitivity": "code.analysis.sensitivity",
    "visualization": "code.analysis.visualization",
    "report_generation": "code.analysis.report_generator",
}

# Ordered list of all stages that must appear in the runtime report.
ALL_STAGES = [
    "data_acquisition",
    "prompt_engineering",
    "synthetic_generation",
    "feature_extraction",
    "timestamp_simulation",
    "matching",
    "analysis",
    "sensitivity",
    "visualization",
    "report_generation",
]


def run_stage(stage_name: str) -> None:
    """
    Import the module for ``stage_name`` and execute its ``main`` function
    if it exists. Any exception is propagated so that failures are visible
    to the caller (and thus to the CI verification step).
    """
    module_path = STAGE_MODULES.get(stage_name)
    if not module_path:
        log.warning(f"No module mapping defined for stage '{stage_name}'. Skipping.")
        return

    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        log.error(f"Failed to import module '{module_path}' for stage '{stage_name}': {e}")
        raise

    if hasattr(module, "main"):
        log.info(f"Running main() of '{module_path}' for stage '{stage_name}'.")
        module.main()
    else:
        log.warning(f"Module '{module_path}' does not define a main() function. Skipping execution.")


def main(argv: list | None = None) -> None:
    """
    Entry point for the pipeline. Parses command‑line arguments (currently
    only ``--full-run`` is recognized, but additional arguments can be added
    in the future) and executes all pipeline stages while recording timing
    information.
    """
    parser = argparse.ArgumentParser(description="Run the full evaluation pipeline.")
    parser.add_argument(
        "--full-run",
        action="store_true",
        help="Execute the complete pipeline (default behavior).",
    )
    # Accept any other arguments without parsing errors.
    args, unknown = parser.parse_known_args(argv)

    # Initialise the global runtime recorder with the complete stage list.
    init_runtime(ALL_STAGES)

    # Execute each stage inside the ``stage`` context manager.
    for st in ALL_STAGES:
        with stage(st):
            try:
                run_stage(st)
            except Exception as exc:
                # Log the error and abort the pipeline – the verification step
                # expects a complete runtime report, so a failure here is
                # intentional and visible.
                log.exception(f"Stage '{st}' failed with error: {exc}")
                raise

    # Finalise and write the runtime report.
    write_report()
    log.info("Pipeline completed successfully. Runtime report written.")


if __name__ == "__main__":
    # ``sys.argv[1:]`` passes all command‑line arguments except the script name.
    main(sys.argv[1:])
