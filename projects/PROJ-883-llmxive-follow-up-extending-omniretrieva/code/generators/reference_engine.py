"""Deterministic greedy reference engine.

This module implements the deterministic, rule‑based greedy ground‑truth
plan generator required by FR‑008.  Given a query definition it selects the
next step with the *lowest estimated cost* and, in case of ties, the
*shortest depth* (i.e., earliest appearance in the query).  The selected
steps are concatenated to form a reproducible ground‑truth plan identifier.

Expected query format (a subset of the full specification):
    {
        "query_id": "<string>",
        "steps": [
            {
                "step_id": "<string>",          # unique identifier for the step
                "estimated_cost": <float>,      # numeric cost estimate
                "depth": <int> (optional)       # optional explicit depth; if omitted,
                                                # the list index is used as depth
            },
            ...
        ]
    }

If the query does not contain a ``steps`` list, a fallback deterministic
identifier based solely on the ``query_id`` is returned so that downstream
components can continue to operate.
"""

import json
from typing import Dict, Any, List, Optional


class ReferenceEngine:
    """Greedy deterministic reference engine."""

    def _select_next_step(
        self,
        remaining: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Select the next step according to the greedy rule.

        The rule is:
          1. Minimum ``estimated_cost``.
          2. If several steps share the same cost, choose the one with the
             smallest ``depth`` (explicit or inferred from list order).

        Parameters
        ----------
        remaining: List[Dict[str, Any]]
            List of step dictionaries that have not yet been selected.

        Returns
        -------
        Dict[str, Any]
            The chosen step dictionary.
        """
        # Determine the minimum cost among remaining steps
        min_cost = min(step["estimated_cost"] for step in remaining)

        # Filter steps that have this minimum cost
        candidates = [
            step for step in remaining if step["estimated_cost"] == min_cost
        ]

        # Resolve ties by depth (explicit ``depth`` key or positional index)
        # The original order of ``remaining`` reflects the original depth.
        # We compute a depth value for each candidate.
        def depth_of(step: Dict[str, Any]) -> int:
            if "depth" in step:
                return int(step["depth"])
            # Fallback: use the index in the original steps list; this
            # requires that ``remaining`` preserves the original ordering.
            return remaining.index(step)

        # Choose the candidate with the smallest depth
        chosen = min(candidates, key=depth_of)
        return chosen

    def generate_plan(self, query: Dict[str, Any]) -> str:
        """Generate a deterministic ground‑truth plan for *query*.

        The algorithm greedily selects steps until all are consumed,
        respecting the rule described in :meth:`_select_next_step`.

        Parameters
        ----------
        query: Dict[str, Any]
            Query definition containing at least ``query_id`` and optionally a
            ``steps`` list.

        Returns
        -------
        str
            A deterministic plan identifier.  The identifier encodes the
            ``query_id`` and the ordered list of selected ``step_id`` values,
            e.g. ``gt_plan_42_A_B_C``.
        """
        query_id: str = str(query.get("query_id", "0"))

        steps: Optional[List[Dict[str, Any]]] = query.get("steps")
        if not steps:
            # No step information – fall back to a simple deterministic ID.
            return f"gt_plan_{query_id}"

        # Work on a copy to avoid mutating the original query structure.
        remaining_steps = list(steps)
        selected_step_ids: List[str] = []

        while remaining_steps:
            next_step = self._select_next_step(remaining_steps)
            step_id = str(next_step.get("step_id", "unknown"))
            selected_step_ids.append(step_id)
            # Remove the selected step from the pool.
            remaining_steps.remove(next_step)

        # Construct the deterministic identifier.
        steps_part = "_".join(selected_step_ids)
        return f"gt_plan_{query_id}_{steps_part}"
