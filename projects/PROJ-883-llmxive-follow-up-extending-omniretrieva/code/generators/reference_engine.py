"""Deterministic greedy reference engine.

The engine implements the contract required by the unit tests in
``tests/unit/test_reference_engine.py``.  It receives a query dict that
may contain a ``steps`` list.  Each step is a mapping with at least
``step_id`` and ``estimated_cost`` keys.

The greedy algorithm sorts steps by ``estimated_cost`` (ascending).  If
several steps share the same cost, the original order (interpreted as
depth) is preserved.  The resulting plan is returned as a string of the
form ``gt_plan_<query_id>_<step1>_<step2>_...``.  When no steps are
provided, the fallback identifier ``gt_plan_<query_id>`` is returned.
"""

from __future__ import annotations

from typing import Any, Dict, List

from llmxive_toolkit import get_logger

log = get_logger(__name__)


class ReferenceEngine:
    """Greedy deterministic reference engine."""

    def generate_plan(self, query: Dict[str, Any]) -> str:
        """Generate a ground‑truth plan string for *query*.

        Parameters
        ----------
        query: dict
            Must contain a ``query_id`` key.  Optionally a ``steps``
            list where each element has ``step_id`` and
            ``estimated_cost`` fields.

        Returns
        -------
        str
            Plan identifier string as described in the module docstring.
        """
        query_id = query.get("query_id")
        if query_id is None:
            raise ValueError("Query must contain a 'query_id' field")

        steps: List[Dict[str, Any]] = query.get("steps", [])
        if not steps:
            plan = f"gt_plan_{query_id}"
            log.debug("No steps for query %s – returning %s", query_id, plan)
            return plan

        # Preserve original order for tie‑breaking by enumerating depth.
        # Sort by (estimated_cost, original_index)
        sorted_steps = sorted(
            enumerate(steps),
            key=lambda pair: (pair[1].get("estimated_cost", float("inf")), pair[0]),
        )
        ordered_step_ids = [step["step_id"] for _, step in sorted_steps]
        plan = f"gt_plan_{query_id}_" + "_".join(ordered_step_ids)
        log.debug(
            "Generated plan for query %s: %s (ordered steps: %s)",
            query_id,
            plan,
            ordered_step_ids,
        )
        return plan
