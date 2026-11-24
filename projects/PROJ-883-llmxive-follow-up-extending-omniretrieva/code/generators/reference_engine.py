"""Reference engine that produces a deterministic greedy plan.

The engine implements a deterministic greedy algorithm that:
1. Loads an optional cost table from ``data/processed/cost_table.json``.
2. For a given query's ``steps`` selects the ordering with the lowest
   cost (ties are resolved by original depth order).
3. Returns a deterministic identifier of the form
   ``gt_plan_<sanitized_query_id>_<ordered_step_id>_<ordered_step_id>...`` where
   ``sanitized_query_id`` is the original ``query_id`` with any ``_`` characters
   replaced by ``-`` to keep the identifier parsable by the unit test.
   The ordered step identifiers are the raw ``step_id`` strings (e.g. ``op_a``).

This implementation satisfies the unit tests in
``tests/unit/test_optimal_planner.py`` and also writes the generated
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
            return {k: int(v) for k, v in data.items()}
        except Exception as e:
            log.error(
                "Failed to load cost table %s: %s – falling back to defaults",
                cost_path,
                e,
            )
            return default_costs

    def _step_cost(self, step_name: str) -> int:
        """Return the cost associated with *step_name*."""
        return self.costs.get(step_name, 1)

    def _order_steps(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return steps ordered by cost, ties broken by original order (depth)."""
        for idx, step in enumerate(steps):
            # Preserve original index for stable tie‑breaking.
            step["_orig_idx"] = idx
            # Use explicit estimated_cost if present; otherwise look up in cost table.
            step["_cost"] = step.get(
                "estimated_cost", self._step_cost(step.get("step_id", ""))
            )
        ordered = sorted(steps, key=lambda s: (s["_cost"], s["_orig_idx"]))
        # Clean auxiliary keys.
        for step in ordered:
            step.pop("_orig_idx", None)
            step.pop("_cost", None)
        return ordered

    def _hash_from_components(self, components: List[str]) -> str:
        """Create an 8‑character hex hash from a list of string components."""
        concatenated = "_".join(components)
        return hashlib.sha256(concatenated.encode("utf-8")).hexdigest()[:8]

    def generate_plan(self, query: Dict[str, Any]) -> str:
        """
        Generate a deterministic greedy plan identifier for *query*.

        Identifier format: ``gt_plan_<sanitized_query_id>_<ordered_step_id>_…`` where
        ``sanitized_query_id`` replaces any ``_`` in the original ``query_id`` with ``-``,
        and the ordered step identifiers are the raw ``step_id`` strings sorted by
        ascending cost (ties broken by original depth).  No hashing is performed;
        the identifier directly encodes the ordering so that the unit test can
        recover the step sequence by splitting on ``_``.
        """
        raw_query_id = str(query.get("query_id", "unknown"))
        # Replace underscores to keep the split tokenisation stable for the test.
        sanitized_qid = raw_query_id.replace("_", "-")
        steps = query.get("steps", [])
        if not steps:
            plan_id = f"gt_plan_{sanitized_qid}"
            log.debug(
                "Generated greedy plan %s (no steps) for query %s",
                plan_id,
                raw_query_id,
            )
            return plan_id

        ordered_steps = self._order_steps(steps)
        ordered_ids = [str(step.get("step_id", "")) for step in ordered_steps]
        # Build identifier without hashing so the test can extract step ids.
        plan_id = f"gt_plan_{sanitized_qid}_" + "_".join(ordered_ids)
        log.debug(
            "Generated greedy plan %s for query %s (ordered steps %s)",
            plan_id,
            raw_query_id,
            ordered_ids,
        )
        return plan_id

    def apply_to_generation_log(self) -> None:
        """Read ``generation_log.json``, fill ``ground_truth_plan`` for each query,
        and write the file back."""
        gen_path = paths.data("processed", "generation_log.json")
        if not gen_path.is_file():
            log.error(
                "Generation log not found at %s – cannot apply reference engine",
                gen_path,
            )
            raise FileNotFoundError(f"Generation log missing: {gen_path}")

        with gen_path.open("r", encoding="utf-8") as f:
            queries = json.load(f)

        if not isinstance(queries, list):
            raise ValueError(
                "generation_log.json must contain a list of query objects"
            )

        for query in queries:
            plan_id = self.generate_plan(query)
            query["ground_truth_plan"] = plan_id

        # Persist the enriched log.
        gen_path.parent.mkdir(parents=True, exist_ok=True)
        with gen_path.open("w", encoding="utf-8") as f:
            json.dump(queries, f, indent=2)

        log.info(
            "Updated %d queries with ground_truth_plan in %s",
            len(queries),
            gen_path,
        )