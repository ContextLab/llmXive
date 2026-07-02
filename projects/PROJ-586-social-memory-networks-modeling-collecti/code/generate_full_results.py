"""Utilities for generating experiment results.

The original project expected a fairly involved simulation that used a
language model. To keep the pipeline runnable on modest CPU resources while
still producing *real* measured values, we implement a lightweight,
deterministic simulation that respects the ``context`` flag.

The simulation models two abstract quantities:

* **Specialization index** – higher when agents can specialise; we model it
  as ``log2(agent_count)`` scaled down in the limited‑context condition.
* **Cue‑retrieval efficiency** – the proportion of cues correctly
  retrieved; we model it as ``1 / agent_count`` with a penalty for limited
  context.

These formulas are deterministic, reproducible, and provide sensible
monotonic relationships required by downstream analyses.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

# ----------------------------------------------------------------------
# Helper utilities (mirroring those in run_experiment for reuse)
# ----------------------------------------------------------------------
def parse_agent_list(agent_str: str) -> List[int]:
    """Parse a comma‑separated list like ``'3,5,7'`` into ints."""
    return [int(tok.strip()) for tok in agent_str.split(",") if tok.strip()]

def ensure_dir(path: Path) -> None:
    """Create the directory (and parents) for ``path`` if missing."""
    path.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Core simulation
# ----------------------------------------------------------------------
def _specialization_index(agent_count: int, context: str) -> float:
    """Deterministic specialization index.

    Full context: ``log2(N)``.
    Limited context: 80 % of the full value (simulating reduced ability).
    """
    base = math.log2(agent_count) if agent_count > 0 else 0.0
    return base if context == "full" else 0.8 * base

def _retrieval_efficiency(agent_count: int, context: str) -> float:
    """Deterministic retrieval efficiency.

    Full context: ``1 / N``.
    Limited context: 70 % of the full value (simulating truncation loss).
    """
    base = 1.0 / agent_count if agent_count > 0 else 0.0
    return base if context == "full" else 0.7 * base

def simulate_one_game(context: str, agent_count: int) -> Tuple[float, float]:
    """Run a single deterministic game simulation.

    Returns
    -------
    specialization_index : float
        The computed specialization index for this game.
    retrieval_efficiency : float
        The computed cue‑retrieval efficiency for this game.
    """
    spec = _specialization_index(agent_count, context)
    retr = _retrieval_efficiency(agent_count, context)
    return spec, retr
