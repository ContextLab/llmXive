"""Reference engine for deterministic ground‑truth plan generation.

This module provides a lightweight, deterministic implementation of the
reference engine required by the synthetic query generator and unit tests.
The engine produces a plan consisting of a list of step identifiers whose
ordering follows a greedy heuristic: at each step it selects the operation
with the lowest estimated cost (according to a static cost table) and,
for ties, the one that appears earliest in the original logical plan.
The algorithm is independent of the router’s cost model and therefore
satisfies FR‑008.

The implementation is deliberately simple yet fully deterministic:
- A static ``_COST_TABLE`` maps known operation names to integer costs.
  Unknown operations receive a default cost of 1.
- ``generate_plan`` extracts the ``logical_plan.steps`` list from the
  input query (if present) and sorts those steps according to the greedy
  rule described above.
- If a query does not contain a logical plan (e.g., legacy calls from
  older code), the engine falls back to generating a generic plan of the
  form ``["step_1", "step_2", …]`` whose length equals the query’s
  ``complexity_level``.
- The returned dictionary matches the schema expected by downstream
  components: it contains ``steps``, ``estimated_depth`` and
  ``estimated_cost``.
"""

from __future__ import annotations

from typing import Dict, Any, List

from llmxive_toolkit import get_logger

log = get_logger(__name__)

class ReferenceEngine:
    """Deterministic greedy‑heuristic reference engine.

    The real project uses a sophisticated cost table derived from
    source‑statistics; for the purposes of the research skeleton we use a
    static table that is sufficient for unit‑test verification while
    remaining fully deterministic.
    """

    # Static cost mapping for known operation types.
    # Costs are deliberately simple integers; lower means cheaper.
    _COST_TABLE: Dict[str, int] = {
        "filter": 1,
        "lookup": 1,
        "join": 2,
        "aggregate": 2,
        "recursive_lookup": 3,
        "traverse": 3,
    }

    def __init__(self) -> None:
        # No external state; the engine is stateless.
        log.debug("ReferenceEngine instantiated.")

    def _cost_of(self, step: str) -> int:
        """Return the cost for *step* using the static cost table."""
        return self._COST_TABLE.get(step, 1)

    def _greedy_sort(self, steps: List[str]) -> List[str]:
        """Return steps ordered by greedy cost selection.

        The greedy rule is:
          1. Choose the step with the lowest cost.
          2. If multiple steps share the same cost, preserve their original
             relative order (i.e., stable sort).

        This yields a deterministic ordering for any input list.
        """
        # Pair each step with its original index to guarantee stability.
        indexed = [(idx, step) for idx, step in enumerate(steps)]
        # Sort by (cost, original_index).
        indexed.sort(key=lambda pair: (self._cost_of(pair[1]), pair[0]))
        sorted_steps = [step for _, step in indexed]
        log.debug("Greedy‑sorted steps: %s -> %s", steps, sorted_steps)
        return sorted_steps

    def generate_plan(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a deterministic ground‑truth plan for *query*.

        The returned dictionary contains:

        - ``steps``: a list of operation identifiers ordered by the greedy
          heuristic.
        - ``estimated_depth``: the number of steps (integer).
        - ``estimated_cost``: the sum of the individual step costs
          (float for consistency with downstream code).

        Parameters
        ----------
        query: dict
            Expected keys:
            * ``complexity_level`` (int) – used when no logical plan is
              provided.
            * ``logical_plan`` (dict, optional) – should contain a
              ``steps`` list describing the original operation sequence.

        Returns
        -------
        dict
            The ground‑truth plan.
        """
        # Extract logical steps if present.
        logical_steps: List[str] = (
            query.get("logical_plan", {}).get("steps", [])
        )
        if logical_steps:
            # Apply greedy ordering to the provided steps.
            ordered_steps = self._greedy_sort(logical_steps)
        else:
            # Fallback: generate generic step identifiers based on depth.
            level = int(query.get("complexity_level", 1))
            ordered_steps = [f"step_{i+1}" for i in range(level)]

        depth = len(ordered_steps)
        total_cost = float(sum(self._cost_of(s) for s in ordered_steps))

        plan = {
            "steps": ordered_steps,
            "estimated_depth": depth,
            "estimated_cost": total_cost,
        }

        log.debug(
            "Generated ground‑truth plan for query %s: %s",
            query.get("query_id", "<no id>"),
            plan,
        )
        return plan