"""
src/config.py

Central configuration module for the RoboDojo symbolic extension pipeline.
This file provides constants required by multiple pipeline components
(orchestrator, executor, planner, data loader, etc.).  All values are
deterministic and intentionally small to keep the CPU‑only pipeline
within the GitHub Actions free‑tier limits.

The configuration mirrors the project‑wide settings defined in
``code/config.py`` (e.g., ``SEED``) but lives in the ``src`` package so
that internal modules can import without pulling in the higher‑level
``code`` package (avoiding circular imports).

All paths are created lazily using ``llmxive_toolkit.paths`` which
guarantees that the corresponding directories exist.
"""

import os
from typing import List

from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# General pipeline constants
# ----------------------------------------------------------------------
# Project root directory (used by several modules for constructing absolute
# paths). ``paths.root`` returns a pathlib.Path pointing at the repository
# root.
BASE_DIR = paths.root

# Random seed – must match the one defined in ``code/config.py`` for
# reproducibility across the whole project.
SEED: int = 42

# ----------------------------------------------------------------------
# Planning / execution limits
# ----------------------------------------------------------------------
# Maximum wall‑clock time (seconds) allowed for the symbolic planner per
# task.  The orchestrator passes this to ``run_planning_pipeline``.
PLANNING_TIMEOUT_S: int = 60

# Tolerances used by the real‑world executor to decide success.
POSE_DEV_TOLERANCE_CM: float = 5.0    # positional deviation tolerance
ORIENT_DEV_TOLERANCE_DEG: float = 15.0  # orientation deviation tolerance

# ----------------------------------------------------------------------
# Dataset identifiers (used by ``src/data_loader`` and ``utils/io``)
# ----------------------------------------------------------------------
# HuggingFace repository that hosts the official RoboDojo dataset.
# This identifier is publicly accessible; if the repository ever becomes
# private the fallback logic in ``utils/io.py`` will raise a clear error.
DATASET_HF_ID: str = "RoboDojo/robodojo"

# Optional commit hash used to pin a specific dataset version.
# Keeping the variable allows downstream code to pin the exact snapshot
# without changing the repository name.
DATASET_COMMIT_HASH: str = "latest"

# ----------------------------------------------------------------------
# Real‑world split name – the dataset provides a ``real`` split containing
# the 18 tasks used for physical evaluation.
# ----------------------------------------------------------------------
REAL_WORLD_SPLIT: str = "real"

# ----------------------------------------------------------------------
# Helper for downstream modules that need a list of the 18 task IDs.
# ----------------------------------------------------------------------
# Import is placed inside the function to avoid importing heavy
# dependencies (datasets) at module import time – this keeps unit‑test
# collection fast and prevents circular imports with ``code/config.py``.
def get_real_task_ids(limit: int = 18) -> List[str]:
    """
    Retrieve the first ``limit`` task identifiers from the real‑world
    RoboDojo split.

    The function streams the dataset using ``src.data_loader.stream_robodojo_tasks``
    which performs checksum validation.  If the dataset cannot be accessed,
    a ``RuntimeError`` is raised so that the failure is loud.

    Returns
    -------
    List[str]
        List of unique task identifiers (e.g., ``["T001", "T002", ...]``).

    Raises
    ------
    RuntimeError
        If the dataset cannot be fetched or fewer than ``limit`` IDs are
        found.
    """
    from .data_loader import stream_robodojo_tasks  # Local import to avoid eager loading

    task_ids: List[str] = []
    try:
        for record in stream_robodojo_tasks(split=REAL_WORLD_SPLIT, streaming=True):
            tid = (
                record.get("task_id")
                or record.get("id")
                or record.get("taskId")
            )
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
