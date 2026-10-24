"""Reference engine that produces a deterministic greedy plan.

The engine implements a deterministic greedy algorithm that:
1. Loads an optional cost table from ``data/processed/cost_table.json``.
2. For a given query's ``steps`` selects the ordering with the lowest
   cost (ties are resolved by original depth order).
3. Returns a deterministic identifier of the form
   ``gt_plan_<query_id>_<ordered_step_ids>`` (or ``gt_plan_<query_id>``
   when no steps are present).

This implementation satisfies the unit tests in
``tests/unit/test_reference_engine.py`` and also writes the generated
identifier into the ``ground_truth_plan`` field of each query record
in ``generation_log.json`` when used by the synthetic query generator.
"""
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

class ReferenceEngine:
    """Deterministic greedy reference engine."""

    def __init__(self):
        # Load a cost table if it exists; otherwise fall back to defaults.
        self.costs = self._load_cost_table()

    def _load_cost_table(self) -> Dict[str, int]:
        """Load ``data/processed/cost_table.json`` if present.

        The file is expected to be a JSON mapping operation name → numeric cost.
        If the file does not exist or cannot be parsed, a hard‑coded default
        mapping is used.
        """
        default_costs = {
            "retrieve_text": 1,
            "execute_sql": 2,
            "run_sparql": 3,
            "generic_operation": 5,
        }
        cost_path = paths.data("processed", "cost_table.json")
        if not cost_path.is_file():
            log.debug("Cost table not found at %s – using defaults", cost_path)
            return default_costs
        try:
            with cost_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            # Ensure all values are ints; coerce if necessary.
            return {k: int(v) for k, v in data.items()}
        except Exception as e:
            log.error("Failed to load cost table %s: %s – falling back to defaults", cost_path, e)
            return default_costs

    def _step_cost(self, step_name: str) -> int:
        """Return the cost associated with *step_name*."""
        return self.costs.get(step_name, 1)

    def _order_steps(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return steps ordered by cost, ties broken by original order."""
        # Attach original index for stable tie‑breaking.
        for idx, step in enumerate(steps):
            step["_orig_idx"] = idx
            # Prefer an explicit ``estimated_cost`` if provided; otherwise use the cost table.
            step["_cost"] = step.get("estimated_cost", self._step_cost(step.get("step_id", "")))
        # Sort by cost then by original index.
        ordered = sorted(steps, key=lambda s: (s["_cost"], s["_orig_idx"]))
        # Clean auxiliary keys.
        for step in ordered:
            step.pop("_orig_idx", None)
            step.pop("_cost", None)
        return ordered

    def generate_plan(self, query: Dict[str, Any]) -> str:
        """
        Generate a deterministic plan identifier for *query*.

        The identifier format matches the expectations of the unit tests:
          - When ``steps`` are present: ``gt_plan_<query_id>_<ordered_step_ids>``
          - When no steps are present: ``gt_plan_<query_id>``

        The ordering respects the greedy rule (lowest cost first,
        depth tie‑breaker).  The function does **not** write to any file;
        callers that need to persist the result should do so explicitly.
        """
        query_id = query.get("query_id", "unknown")
        steps = query.get("steps", [])
        if not steps:
            plan_id = f"gt_plan_{query_id}"
            log.debug("Generated plan %s (no steps) for query %s", plan_id, query_id)
            return plan_id

        ordered_steps = self._order_steps(steps)
        ordered_ids = [str(step.get("step_id", "")) for step in ordered_steps]
        plan_id = f"gt_plan_{query_id}_{'_'.join(ordered_ids)}"
        log.debug("Generated plan %s for query %s", plan_id, query_id)
        return plan_id

    def apply_to_generation_log(self) -> None:
        """Read ``generation_log.json``, fill ``ground_truth_plan`` for each query,
        and write the file back."""
        gen_path = paths.data("processed", "generation_log.json")
        if not gen_path.is_file():
            log.error("Generation log not found at %s – cannot apply reference engine", gen_path)
            raise FileNotFoundError(f"Generation log missing: {gen_path}")

        with gen_path.open("r", encoding="utf-8") as f:
            queries = json.load(f)

        if not isinstance(queries, list):
            raise ValueError("generation_log.json must contain a list of query objects")

        for query in queries:
            plan_id = self.generate_plan(query)
            query["ground_truth_plan"] = plan_id

        # Persist the enriched log.
        gen_path.parent.mkdir(parents=True, exist_ok=True)
        with gen_path.open("w", encoding="utf-8") as f:
            json.dump(queries, f, indent=2)

        log.info("Updated %d queries with ground_truth_plan in %s", len(queries), gen_path)
