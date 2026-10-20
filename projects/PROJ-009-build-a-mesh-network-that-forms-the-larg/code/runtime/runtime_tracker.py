"""
Simple runtime‑budget tracker for the orchestrator pipeline.

The tracker records the total wall‑clock time of a pipeline segment
(e.g. a single ``run`` or a full ``sweep``) and writes two artefacts:

* ``data/runtime/pipeline_runtime.json`` – JSON with ``total_seconds`` and
  ``within_limit`` fields.
* ``data/runtime/timeout_enforced.log`` – written only when the runtime
  exceeds the supplied limit, containing a human‑readable message.
"""

import time
import json
from typing import Optional

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

_start_time: Optional[float] = None

def start() -> None:
    """Mark the beginning of a timed section."""
    global _start_time
    _start_time = time.time()
    log.debug("Runtime tracker started at %s", _start_time)

def stop(limit_seconds: float) -> Tuple[float, bool]:
    """
    Stop the timer, write artefacts and return the elapsed time and
    whether the limit was respected.

    Parameters
    ----------
    limit_seconds: float
        Hard budget in seconds (e.g. 5 h → 18000).

    Returns
    -------
    (elapsed_seconds, within_limit)
    """
    global _start_time
    if _start_time is None:
        raise RuntimeError("RuntimeTracker.stop() called before start()")
    elapsed = time.time() - _start_time
    within = elapsed <= limit_seconds

    # Write pipeline_runtime.json
    runtime_path = paths.data("runtime", "pipeline_runtime.json")
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_path.write_text(
        json.dumps(
            {"total_seconds": elapsed, "within_limit": within},
            indent=2,
        ),
        encoding="utf-8",
    )
    log.info("Pipeline runtime recorded: %.2f s (within limit: %s)", elapsed, within)

    # If we exceeded the budget, write a log file
    if not within:
        log_path = paths.data("runtime", "timeout_enforced.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            f"Timeout exceeded: {elapsed:.2f}s > {limit_seconds:.2f}s",
            encoding="utf-8",
        )
        log.warning("Timeout enforced – see %s", log_path)

    # Reset for potential reuse
    _start_time = None
    return elapsed, within
