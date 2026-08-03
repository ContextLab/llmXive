"""Policy Contract v1 constants, DERIVED where the spec derives them (Constitution I — the
LLM-call-ceiling row is the precedent). ONE module: every bound the lane enforces is read
from here, so a value cannot be edited in one consumer and not another.

A later task appends the post-claim phase budgets and the counter caps. This module imports
nothing from the lane, which is what lets `clock.py` depend on it without a cycle."""

from __future__ import annotations

MINUTE = 60

HEARTBEAT_INTERVAL_S = 5 * MINUTE
CLAIM_EXPIRY_S = 3 * HEARTBEAT_INTERVAL_S  # tolerate two missed beats
MAX_CLOCK_SKEW_S = 5 * MINUTE
MAX_SAMPLE_RTT_S = 2  # Policy Contract `max_sample_rtt`

__all__ = [
    "CLAIM_EXPIRY_S",
    "HEARTBEAT_INTERVAL_S",
    "MAX_CLOCK_SKEW_S",
    "MAX_SAMPLE_RTT_S",
    "MINUTE",
]
