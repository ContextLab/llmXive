"""
Simple gap‑logging utility.

The pipeline must record design‑or other gaps in ``docs/gaps.md``.  This
helper appends a single line ``<dataset_id>: <reason>`` to that file.
It uses the ``llmxive_toolkit.paths`` helper to obtain the correct location
inside the repository and a logger for diagnostic output.
"""

from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def log_gap(dataset_id: str, reason: str) -> None:
    """
    Append a gap description to ``docs/gaps.md``.

    Parameters
    ----------
    dataset_id : str
        Identifier of the dataset that exhibits a gap.
    reason : str
        Short machine‑readable reason (e.g., ``design_missing``).
    """
    gaps_path: Path = paths.docs("gaps.md")
    # Ensure the parent directory exists – ``paths.docs`` creates it.
    line = f"{dataset_id}: {reason}\n"
    try:
        with gaps_path.open("a", encoding="utf-8") as f:
            f.write(line)
        log.info(f"Logged gap for {dataset_id} – {reason}")
    except Exception as exc:
        log.error(f"Failed to write gap log for {dataset_id}: {exc}")
        raise
