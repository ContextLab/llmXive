"""
analysis package
=================

This package groups together all analysis‑related modules for the
*Predict Plant Disease Resistance* project.  The original modules were
written independently and each contained its own logger configuration,
duplicated imports and ad‑hoc entry‑point functions.  The refactor adds a
lightweight, centralised entry point that can be used by downstream scripts
(e.g. ``code/main.py``) or by developers during interactive sessions.

The public API of the package consists of:

* ``run_all_analysis`` – a convenience wrapper that imports each analysis
  sub‑module and executes its primary pipeline function if it exists.
* ``__all__`` – the symbols that are re‑exported at the package level.

The function does **not** enforce a particular order or pass arguments to
the sub‑module pipelines because the individual pipelines have their own
signatures and configuration handling.  Instead, it attempts to call a
``*_pipeline`` function (if present) and logs the outcome.  This approach
preserves existing behaviour while providing a single, well‑documented
entry point for future refactoring work.
"""

import importlib
import logging
from pathlib import Path
from typing import List

# Use the project's structured logger
from utils.logging import setup_logger, log_pipeline_step

# Initialise a module‑wide logger
logger = setup_logger(__name__)

__all__: List[str] = [
    "run_all_analysis",
]

def _call_pipeline(module_name: str, func_name: str) -> None:
    """
    Helper that imports ``module_name`` and, if ``func_name`` exists,
    calls it.  Any exception is caught and logged so that a failure in
    one analysis step does not abort the whole orchestration.
    """
    try:
        module = importlib.import_module(module_name)
        func = getattr(module, func_name, None)
        if callable(func):
            logger.info(f"Running {func_name} from {module_name}")
            log_pipeline_step(f"Starting {func_name}")
            func()  # type: ignore[arg-type]
            log_pipeline_step(f"Completed {func_name}")
        else:
            logger.debug(f"No callable {func_name} in {module_name}")
    except Exception as e:
        logger.error(
            f"Error while executing {func_name} from {module_name}: {e}",
            exc_info=True,
        )

def run_all_analysis() -> None:
    """
    Execute the primary pipeline function of each analysis sub‑module.

    The function looks for a ``*_pipeline`` function in the following
    modules (in order) and invokes it if present:

    * ``analysis.feature_selection`` – ``feature_selection_pipeline``
    * ``analysis.modeling`` – ``modeling_pipeline``
    * ``analysis.validation`` – ``run_validation_pipeline``
    * ``analysis.holdout_report`` – ``generate_holdout_report_pipeline``
    * ``analysis.biomarker_report`` – ``biomarker_report_pipeline``
    * ``analysis.success_criteria_check`` – ``main``
    * ``analysis.validation_target_check`` – ``main``
    * ``analysis.permutation_test`` – ``permutation_test_pipeline``

    This orchestrator is intentionally forgiving: missing modules or
    functions are logged at ``DEBUG`` level, and any runtime exception is
    captured and logged without propagating.
    """
    logger.info("Starting unified analysis orchestration")
    pipelines = [
        ("analysis.feature_selection", "feature_selection_pipeline"),
        ("analysis.modeling", "modeling_pipeline"),
        ("analysis.validation", "run_validation_pipeline"),
        ("analysis.holdout_report", "generate_holdout_report_pipeline"),
        ("analysis.biomarker_report", "biomarker_report_pipeline"),
        ("analysis.success_criteria_check", "main"),
        ("analysis.validation_target_check", "main"),
        ("analysis.permutation_test", "permutation_test_pipeline"),
    ]

    for module_name, func_name in pipelines:
        _call_pipeline(module_name, func_name)

    logger.info("Unified analysis orchestration completed")