"""
Orchestrator data models.

This module defines the core dataclasses used throughout the
orchestration codebase: ``PhysicalNode``, ``TaskChunk`` and the
``TaskStatus`` enum.  The definitions are deliberately lightweight
and compatible with the unit‑test fixtures that construct nodes
with ``ip``, ``status`` and ``ram_mb`` fields.  Additional optional
attributes (e.g. ``cpu_speed_mhz``) are provided to support the
scheduler's heterogeneity scoring logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class TaskStatus(str, Enum):
    """
    Simple enumeration of task lifecycle states.

    The string values are used when serialising to JSON and match the
    values expected by the contract tests.
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REASSIGNED = "reassigned"


@dataclass
class PhysicalNode:
    """
    Minimal representation of a compute node.

    The test suite creates ``PhysicalNode`` instances with only the
    ``ip``, ``status`` and ``ram_mb`` arguments, so those fields are
    required.  ``cpu_speed_mhz`` is optional but required by the
    scheduler for heterogeneity scoring; a sensible default is
    provided.
    """
    ip: str
    status: str = "active"
    ram_mb: float = 2048.0
    cpu_speed_mhz: float = 1500.0
    # Additional metadata can be added later without breaking
    # existing tests.


@dataclass
class TaskChunk:
    """
    Represents a chunk of work dispatched to a node.

    Fields required by the scheduler:
    - ``id``: unique identifier for the chunk.
    - ``size_mb``: memory footprint of the chunk (used for OOM checks).
    - ``iterations``: number of benchmark iterations.
    - ``data``: opaque payload (e.g. benchmark configuration).
    Optional indexing fields are used by the recursive split logic.
    """
    id: str
    size_mb: float
    iterations: int
    data: Any = None
    start_idx: Optional[int] = None
    end_idx: Optional[int] = None
