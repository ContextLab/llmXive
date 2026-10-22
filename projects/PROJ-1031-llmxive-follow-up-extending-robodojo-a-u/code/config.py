"""
Project-wide configuration and environment settings for the RoboDojo symbolic
extension project.

This module defines:
  - A deterministic random seed.
  - CPU and memory limits for the pipeline.
  - Convenience data path helpers using llmxive_toolkit.
  - The list of real‑world RoboDojo task identifiers (exactly 18 entries).

The task IDs are fetched lazily from the official RoboDojo HuggingFace dataset
(split="real") using the verified data loader in ``src.data_loader``.  If the
dataset cannot be reached, an exception is raised so that the failure is
loud and visible to the execution harness.
"""

import os
from typing import List

# ----------------------------------------------------------------------
# Random seed – used throughout the project for reproducibility.
# ----------------------------------------------------------------------
SEED: int = 42

# ----------------------------------------------------------------------
# Resource limits (CPU‑only pipeline).
# ----------------------------------------------------------------------
# Maximum number of CPU cores the planner/executors may use.
MAX_CPU_CORES: int = 2
# Maximum memory usage in megabytes (soft limit; the code should respect it).
MAX_MEMORY_MB: int = 6000

# ----------------------------------------------------------------------
# Data path helpers (provided by llmxive_toolkit).
# ----------------------------------------------------------------------
from llmxive_toolkit import paths

# Base directories for the different data stages.
RAW_DATA_DIR = paths.data("raw")
INTERIM_DATA_DIR = paths.data("interim")
PROCESSED_DATA_DIR = paths.data("processed")
FINAL_DATA_DIR = paths.data("final")

# Ensure the directories exist when this module is imported.
for _dir in (RAW_DATA_DIR, INTERIM_DATA_DIR, PROCESSED_DATA_DIR, FINAL_DATA_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# RoboDojo real‑world task identifiers.
# ----------------------------------------------------------------------
# The IDs are obtained from the official dataset.  We stream the dataset
# and collect the first 18 unique identifiers.  This guarantees that the
# list reflects real data and that the module fails loudly if the dataset
# cannot be accessed.
from src.data_loader import stream_robodojo_tasks

def _load_real_task_ids(limit: int = 18) -> List[str]:
    """Fetch the first ``limit`` task IDs from the real‑world RoboDojo split.

    Returns:
        A list of task identifier strings.

    Raises:
        RuntimeError: If the dataset cannot be fetched or no IDs are found.
    """
    task_ids: List[str] = []
    try:
        for record in stream_robodojo_tasks(split="real", streaming=True):
            # The dataset schema uses the key ``task_id`` for the identifier.
            # We fall back to alternative keys just in case.
            tid = record.get("task_id") or record.get("id") or record.get("taskId")
            if tid and tid not in task_ids:
                task_ids.append(tid)
                if len(task_ids) >= limit:
                    break
    except Exception as exc:
        raise RuntimeError("Unable to retrieve RoboDojo real‑world task IDs") from exc

    if len(task_ids) < limit:
        raise RuntimeError(
            f"Expected at least {limit} task IDs, but only found {len(task_ids)}"
        )
    return task_ids

# Public constant containing exactly 18 real‑world task IDs.
TASK_IDS: List[str] = _load_real_task_ids(18)