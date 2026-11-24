"""
ReplicationResult model.

Captures the outcome of a single bootstrap iteration used in the split‑half
validation step. The model is deliberately simple – it stores the numeric
results required by the downstream aggregation utilities and contract tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

@dataclass
class ReplicationResult:
    """
    Result of a single replication (split‑half) iteration.

    Attributes
    ----------
    effect_size_est: Estimated Cohen's d from the training half.
    p_value: Two‑sided p‑value computed on the test half.
    replication_success: Binary flag (1 = replicated, 0 = not replicated).
    smoothing_kernel_used: Kernel size (e.g. "4mm").
    """
    effect_size_est: float
    p_value: float
    replication_success: int
    smoothing_kernel_used: str
    # Optional fields that may be useful for diagnostics
    iteration_id: Optional[int] = None
    sample_size: Optional[int] = None
