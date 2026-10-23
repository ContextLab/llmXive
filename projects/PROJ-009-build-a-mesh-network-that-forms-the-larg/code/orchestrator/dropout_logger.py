"""
Helper module for persisting dropout‑event information produced by the
``Scheduler``.  The scheduler itself records events internally; this module
provides a thin wrapper that can be used by higher‑level orchestration code
(e.g. the CLI or a sweep runner) to write the JSON file to the canonical
location ``data/raw/dropout_events.json``.
"""

from pathlib import Path
from orchestrator.scheduler import Scheduler

def write_dropout_events(scheduler: Scheduler, output_path: Path) -> None:
    """
    Write the scheduler's internal dropout‑event log to *output_path*.

    Parameters
    ----------
    scheduler: Scheduler
        An instantiated scheduler that has already recorded events via
        ``_record_dropout_event``.
    output_path: Path
        Destination file path.  Parent directories are created automatically.
    """
    scheduler.dump_events(output_path)