"""
Runtime tracking utilities.

This module provides two simple functions used by the orchestrator CLI
to record the total wall‑clock time of a pipeline run and to enforce the
hard timeout required by FR‑007 / SC‑004.

The implementation is deliberately lightweight and has no external
dependencies beyond the standard library and ``llmxive_toolkit``.
"""

import json
import time
from pathlib import Path
from typing import Tuple

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# Global variable to hold the start timestamp of the current run.
_run_start: float | None = None


def start() -> None:
    """
    Record the start time of a pipeline run.

    This function should be called as early as possible (e.g. at the
    beginning of a CLI sub‑command) to capture the total elapsed time.
    """
    global _run_start
    _run_start = time.time()
    log.info("Runtime tracking started at %s", _run_start)


def stop(limit_seconds: float) -> Tuple[float, bool]:
    """
    Stop the timer and write a JSON summary.

    Parameters
    ----------
    limit_seconds: float
        The hard timeout (in seconds) that the pipeline must not exceed.

    Returns
    -------
    Tuple[float, bool]
        A tuple ``(elapsed_seconds, within_limit)`` where ``within_limit``
        is ``True`` if the elapsed time is less than or equal to the
        supplied limit.
    """
    if _run_start is None:
        raise RuntimeError("Runtime tracking was not started – call start() first")

    elapsed = time.time() - _run_start
    within_limit = elapsed <= limit_seconds

    # Write the JSON payload to the canonical location.
    result_path = paths.data("runtime", "pipeline_runtime.json")
    result_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "total_seconds": elapsed,
        "within_limit": within_limit,
    }
    result_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log.info(
        "Runtime tracking stopped – elapsed: %.2f s, within limit: %s",
        elapsed,
        within_limit,
    )
    return elapsed, within_limit
