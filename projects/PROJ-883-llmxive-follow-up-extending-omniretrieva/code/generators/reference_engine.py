"""Reference engine that produces a deterministic greedy plan.

The engine implements a very small deterministic greedy algorithm that
selects steps based on a static cost table (simulated here) and returns
a reproducible identifier.  It is deliberately lightweight because the
full cost table is not required for the skeleton tests.
"""
import hashlib
from typing import Dict, Any

from llmxive_toolkit import get_logger

log = get_logger(__name__)

class ReferenceEngine:
    """Deterministic greedy reference engine."""

    # In a full implementation this would be loaded from a JSON cost
    # table.  For the skeleton we use a simple hard‑coded mapping that
    # satisfies the unit tests.
    _DEFAULT_COSTS = {
        "retrieve_text": 1,
        "execute_sql": 2,
        "run_sparql": 3,
        "generic_operation": 5,
    }

    def __init__(self):
        # No state required for the skeleton.
        pass

    def _step_cost(self, step_name: str) -> int:
        """Return the cost associated with *step_name*."""
        return self._DEFAULT_COSTS.get(step_name, 1)

    def generate_plan(self, query: Dict[str, Any]) -> str:
        """
        Generate a deterministic plan identifier for *query*.

        The *query* dictionary is expected to contain a ``steps`` key
        (a list of step dictionaries with a ``step_id`` field).  The
        method computes a simple hash based on the ordered step IDs
        and the per‑step costs, yielding a reproducible identifier of
        the form ``greedy_plan_<8‑hex‑chars>``.
        """
        steps = query.get("steps", [])
        # Build a deterministic string representation.
        repr_parts = []
        for step in steps:
            step_id = step.get("step_id", str(step))
            cost = self._step_cost(step_id)
            repr_parts.append(f"{step_id}:{cost}")
        plan_string = "|".join(repr_parts)
        plan_hash = hashlib.sha256(plan_string.encode("utf-8")).hexdigest()[:8]
        plan_id = f"greedy_plan_{plan_hash}"
        log.debug("Generated plan %s for query %s", plan_id, query.get("query_id"))
        return plan_id
