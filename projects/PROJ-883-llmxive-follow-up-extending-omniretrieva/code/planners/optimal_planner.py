"""Optimal planner for exhaustive search over query step orderings.

This script reads the synthetic query generation log
``data/processed/generation_log.json``, samples a stratified subset
(default 5 % of the total while preserving the distribution of
``source_type`` and ``complexity_level``), and computes the true
minimal‑cost plan for each sampled query by brute‑force permutation
search.  The cost of a plan is defined as the sum of
``cost(step) * position_index`` (1‑based), where ``cost(step)`` is
looked up in the same cost table used by the deterministic greedy
reference engine (``data/processed/cost_table.json``).  The optimal
ordering is the permutation with the smallest weighted sum; ties are
broken by the lexicographically smallest concatenated step identifier.

The resulting mapping ``query_id → optimal_plan_id`` is written to
``data/processed/optimal_ground_truth.json``.  Each ``optimal_plan_id``
has the format ``optimal_plan_<8‑hex‑digest>``, where the digest is the
first eight characters of the SHA‑256 hash of the ordered step IDs.

The module also provides a ``run_optimal_planner`` function that can be
imported by unit tests.  When executed as a script (``python -m
code.planners.optimal_planner``) it runs the planner with the default
5 % sampling fraction.
"""

from __future__ import annotations

import itertools
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

##########################################################################
# Helper utilities
##########################################################################
def _load_cost_table() -> Dict[str, int]:
    """Load the operation cost table.

    The table is expected at ``data/processed/cost_table.json``.
    If the file is missing, a default table matching the reference
    engine is used.
    """
    default_costs = {
        "retrieve_text": 1,
        "execute_sql": 2,
        "run_sparql": 3,
        "generic_operation": 5,
    }
    cost_path = paths.data("processed", "cost_table.json")
    if not cost_path.is_file():
        log.debug("Cost table not found – using default costs")
        return default_costs
    try:
        with cost_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure integer values
        return {k: int(v) for k, v in data.items()}
    except Exception as exc:
        log.error("Failed to read cost table %s: %s – falling back to defaults", cost_path, exc)
        return default_costs

def _load_generation_log() -> List[Dict]:
    """Load the synthetic query generation log."""
    gen_path = paths.data("processed", "generation_log.json")
    if not gen_path.is_file():
        raise FileNotFoundError(f"Generation log not found at {gen_path}")
    with gen_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("generation_log.json must contain a list of query objects")
    return data

def _weighted_cost(ordering: Tuple[str, ...], cost_map: Dict[str, int]) -> int:
    """Compute the weighted cost of a particular ordering.

    Weighted cost = Σ cost(step_i) * (position_i), positions are 1‑based.
    """
    total = 0
    for idx, step_name in enumerate(ordering, start=1):
        step_cost = cost_map.get(step_name, 1)
        total += step_cost * idx
    return total

def _optimal_order(steps: List[str], cost_map: Dict[str, int]) -> Tuple[Tuple[str, ...], int]:
    """Return the ordering with minimal weighted cost and its cost."""
    best_order: Tuple[str, ...] = tuple()
    best_cost = float("inf")
    # Exhaustive search – feasible because maximum depth is small (≤4)
    for perm in itertools.permutations(steps):
        cur_cost = _weighted_cost(perm, cost_map)
        if cur_cost < best_cost:
            best_cost = cur_cost
            best_order = perm
        elif cur_cost == best_cost:
            # Tie‑break by lexicographically smallest concatenated IDs
            if "".join(perm) < "".join(best_order):
                best_order = perm
    return best_order, int(best_cost)

def _hash_plan(step_ids: Tuple[str, ...]) -> str:
    """Create an 8‑character hash suffix for a plan."""
    joined = "_".join(step_ids)
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()[:8]
    return digest

def _stratified_sample(
    queries: List[Dict],
    fraction: float = 0.05,
) -> List[Dict]:
    """Return a stratified sample preserving source_type & complexity distribution."""
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0, 1]")
    # Group by (source_type, complexity_level)
    groups: Dict[Tuple[str, int], List[Dict]] = {}
    for q in queries:
        key = (q.get("source_type"), int(q.get("complexity_level", 1)))
        groups.setdefault(key, []).append(q)

    sampled: List[Dict] = []
    for group, items in groups.items():
        n_total = len(items)
        n_sample = max(1, int(round(n_total * fraction)))
        # Deterministic sampling using a fixed RNG seed
        rng = itertools.islice(items, n_sample)  # simple deterministic slice
        sampled.extend(list(rng))
    log.debug(
        "Stratified sample size: %d (fraction %.2f) from %d total queries",
        len(sampled),
        fraction,
        len(queries),
    )
    return sampled

##########################################################################
# Core planner implementation
##########################################################################
def run_optimal_planner(sample_fraction: float = 0.05) -> Dict[str, str]:
    """Execute the exhaustive optimal planner.

    Returns
    -------
    dict
        Mapping ``query_id`` → ``optimal_plan_id``.
    """
    cost_map = _load_cost_table()
    queries = _load_generation_log()
    if not queries:
        log.warning("No queries found in generation log – nothing to plan")
        return {}

    sampled_queries = _stratified_sample(queries, fraction=sample_fraction)

    result_mapping: Dict[str, str] = {}
    for q in sampled_queries:
        qid = q.get("query_id")
        steps = q.get("logical_plan", {}).get("steps", [])
        if not isinstance(steps, list) or not steps:
            # No steps – plan identifier is simply the query id.
            plan_id = f"optimal_plan_{qid}"
            result_mapping[qid] = plan_id
            continue

        # Compute optimal ordering
        optimal_ordering, _ = _optimal_order(steps, cost_map)
        plan_hash = _hash_plan(optimal_ordering)
        plan_id = f"optimal_plan_{plan_hash}"
        result_mapping[qid] = plan_id

    # Persist the mapping
    out_path = paths.data("processed", "optimal_ground_truth.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result_mapping, f, indent=2)
    log.info(
        "Optimal planner finished – %d entries written to %s",
        len(result_mapping),
        out_path,
    )
    return result_mapping

##########################################################################
# CLI entry point
##########################################################################
if __name__ == "__main__":
    # When run as a script we simply execute with the default 5 % sample.
    run_optimal_planner()
