"""
Runtime instrumentation utilities for the evaluation pipeline.

This module provides a simple API to record start/end timestamps for
named pipeline stages and to write a JSON report summarising the
elapsed time per stage and the total runtime.

The implementation is deliberately lightweight – it does not depend on
any external packages beyond the standard library and the project's
``llmxive_toolkit`` helpers for path handling and logging.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

class RuntimeRecorder:
    """
    Record timing information for a predefined list of pipeline stages.

    Example
    -------
    >>> stages = ["data_acquisition", "prompt_engineering"]
    >>> recorder = RuntimeRecorder(stages, Path("runtime_report.json"))
    >>> recorder.start_stage("data_acquisition")
    >>> # ... do work ...
    >>> recorder.end_stage("data_acquisition")
    >>> recorder.write()
    """

    def __init__(self, stages: List[str], output_path: Optional[Path] = None):
        self.stages = stages
        self.output_path = output_path or paths.data("processed", "runtime_report.json")
        self._stage_start_times: Dict[str, float] = {}
        self.stage_durations: Dict[str, float] = {}
        self._overall_start: Optional[float] = None
        self._overall_end: Optional[float] = None

    # ------------------------------------------------------------------
    # Overall timing
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Mark the beginning of the whole pipeline run."""
        self._overall_start = time.time()
        log.debug("Pipeline overall timer started.")

    def stop(self) -> None:
        """Mark the end of the whole pipeline run."""
        self._overall_end = time.time()
        log.debug("Pipeline overall timer stopped.")

    # ------------------------------------------------------------------
    # Per‑stage timing
    # ------------------------------------------------------------------
    def start_stage(self, stage_name: str) -> None:
        """Record the start time for *stage_name*."""
        if stage_name not in self.stages:
            raise ValueError(f"Stage '{stage_name}' is not a recognised pipeline stage.")
        self._stage_start_times[stage_name] = time.time()
        log.debug(f"Stage '{stage_name}' timer started.")

    def end_stage(self, stage_name: str) -> None:
        """Record the end time for *stage_name* and compute its duration."""
        if stage_name not in self._stage_start_times:
            raise RuntimeError(f"Cannot end stage '{stage_name}' that was never started.")
        start_ts = self._stage_start_times.pop(stage_name)
        duration = time.time() - start_ts
        self.stage_durations[stage_name] = duration
        log.debug(f"Stage '{stage_name}' completed in {duration:.3f} s.")

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def _total_seconds(self) -> float:
        """Return the total elapsed seconds for the whole run."""
        if self._overall_start is None:
            return 0.0
        end = self._overall_end if self._overall_end is not None else time.time()
        return end - self._overall_start

    def write(self) -> None:
        """Serialise the timing information to ``self.output_path``."""
        report = {
            "stage_times": self.stage_durations,
            "total_seconds": self._total_seconds(),
        }
        # Ensure the target directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("w", encoding="utf-8") as fp:
            json.dump(report, fp, indent=2)
        log.info(f"Runtime report written to {self.output_path}")

# ----------------------------------------------------------------------
# Module‑level convenience API
# ----------------------------------------------------------------------
_global_recorder: Optional[RuntimeRecorder] = None

def init_runtime(
    stages: List[str],
    output_path: Optional[Path] = None,
) -> RuntimeRecorder:
    """
    Initialise (or re‑initialise) the global ``RuntimeRecorder`` instance.

    Parameters
    ----------
    stages: List[str]
        Ordered list of stage identifiers that the pipeline will
        report.  The list must contain *all* stages that downstream
        verification expects.
    output_path: Optional[Path]
        Destination for the JSON report.  Defaults to
        ``data/processed/runtime_report.json`` via ``llmxive_toolkit.paths``.
    """
    global _global_recorder
    _global_recorder = RuntimeRecorder(stages, output_path)
    _global_recorder.start()
    log.debug("Global RuntimeRecorder initialised.")
    return _global_recorder

def start_stage(stage_name: str) -> None:
    """Convenience wrapper around ``_global_recorder.start_stage``."""
    if _global_recorder is None:
        raise RuntimeError("RuntimeRecorder has not been initialised – call init_runtime() first.")
    _global_recorder.start_stage(stage_name)

def end_stage(stage_name: str) -> None:
    """Convenience wrapper around ``_global_recorder.end_stage``."""
    if _global_recorder is None:
        raise RuntimeError("RuntimeRecorder has not been initialised – call init_runtime() first.")
    _global_recorder.end_stage(stage_name)

def write_report() -> None:
    """Flush the recorded timings to disk."""
    if _global_recorder is None:
        raise RuntimeError("RuntimeRecorder has not been initialised – call init_runtime() first.")
    _global_recorder.stop()
    _global_recorder.write()

# ----------------------------------------------------------------------
# Context‑manager helper for idiomatic usage
# ----------------------------------------------------------------------
from contextlib import contextmanager

@contextmanager
def stage(name: str):
    """
    Context manager that automatically starts and ends a stage.

    Example
    -------
    >>> from code.runtime import init_runtime, stage
    >>> init_runtime(["download", "process"])
    >>> with stage("download"):
    ...     download_data()
    """
    start_stage(name)
    try:
        yield
    finally:
        end_stage(name)
