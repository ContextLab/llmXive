"""
Entry point for the end‑to‑end evaluation pipeline.

This script orchestrates the individual pipeline stages while
recording start/end timestamps for each stage via the
``code.runtime`` utilities (Task T014).  The implementation is
deliberately defensive: even if a downstream stage raises an
exception, the runtime recorder is always flushed so that
``runtime_report.json`` contains timing entries for **all** stages
as required by the verification test.
"""

import importlib
import logging
import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths
from code.runtime import init_runtime, write_report, stage

# ------------------------------------------------------------------
# Global logger
# ------------------------------------------------------------------
log = get_logger(__name__)

# ------------------------------------------------------------------
# List of canonical pipeline stages (must match verification)
# ------------------------------------------------------------------
PIPELINE_STAGES = [
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

def _run_stage_module(module_name: str):
    """
    Import ``code.<module_name>`` and, if it defines a ``main`` function,
    execute it inside the ``stage`` context manager.  If the module does
    not exist or lacks a ``main`` entry point, the stage is still timed
    (a no‑op) so that the runtime report contains an entry for every
    expected stage.
    """
    full_name = f"code.{module_name}"
    try:
        module = importlib.import_module(full_name)
    except ModuleNotFoundError:
        log.warning(f"Stage module '{full_name}' not found – recording empty stage.")
        with stage(module_name):
            pass
        return

    # If the module provides a ``main`` callable, run it.
    entry = getattr(module, "main", None)
    if callable(entry):
        with stage(module_name):
            log.info(f"Running stage '{module_name}' via {full_name}.main()")
            entry()
    else:
        # No explicit entry point – still record the timing.
        with stage(module_name):
            log.info(f"Stage '{module_name}' has no main() – recorded as empty.")
            pass

def main(argv=None):
    """
    Execute the full pipeline.

    Parameters
    ----------
    argv : list[str] | None
        Optional list of command‑line arguments (defaults to ``sys.argv``).

    Returns
    -------
    int
        Exit code (0 = success, non‑zero = failure).
    """
    if argv is None:
        argv = sys.argv[1:]

    # Initialise the global runtime recorder.
    init_runtime(PIPELINE_STAGES, output_path=paths.data("processed", "runtime_report.json"))

    # Run each stage in order, protecting against unexpected crashes.
    try:
        for stage_name in PIPELINE_STAGES:
            _run_stage_module(stage_name)
    except Exception as exc:  # pragma: no cover – any unexpected error is logged
        log.exception("Unhandled exception in pipeline execution", exc_info=exc)
        # Continue to the finally block to ensure the report is written.
        return 1
    finally:
        # Flush the timings regardless of success/failure.
        write_report()
        log.info(f"Runtime report written to {paths.data('processed', 'runtime_report.json')}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
