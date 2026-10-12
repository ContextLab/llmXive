"""Thin wrapper that re‑exports metric utilities.

The actual implementations live in ``code.utils.metrics``.
"""

from importlib import import_module

_metrics_mod = import_module('code.utils.metrics')
entropy = _metrics_mod.entropy
log_prob_shift = _metrics_mod.log_prob_shift
