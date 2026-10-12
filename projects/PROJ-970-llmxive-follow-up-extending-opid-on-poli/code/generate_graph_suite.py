"""
Batch‑generate synthetic State‑Graph environments for all three complexity tiers.

This script creates 20 graphs per tier (total 60) using the deterministic
seeds ``config.SEED + i`` where ``i`` ranges from 0 to 19.  Each graph is
saved as a JSON file in ``data/raw/synthetic_graphs/`` by the underlying
generator functions.  A manifest CSV ``data/raw/graph_manifest.csv`` is
written with the columns ``graph_id,tier,seed``.
"""

import csv
import logging
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# Project imports
from config import SEED
from environment.graph_generator import (
    generate_tier_1,
    generate_tier_2,
    generate_tier_3,
)
from environment.state_graph import StateGraph

log = get_logger(__name__)

def _generate_for_tier(tier: int, seed_offset: int) -> StateGraph:
    """
    Generate a graph for the specified tier using a seed derived from the
    global ``SEED`` plus ``seed_offset``.  Returns the created ``StateGraph``.
    """
    seed = SEED + seed_offset
    if tier == 1:
        sg = generate_tier_1(seed=seed)
    elif tier == 2:
        sg = generate_tier_2(seed=seed)
    elif tier == 3:
        sg = generate_tier_3(seed=seed)
    else:
        raise ValueError(f"Unsupported tier: {tier}")
    return sg

def main() -> None:
    """
    Entry point for the batch‑generation script.

    - Generates 20 graphs for each tier (1, 2, 3).
    - Writes a manifest CSV ``data/raw/graph_manifest.csv`` with columns:
      ``graph_id,tier,seed``.
    - Relies on the tier‑specific generator functions to persist each graph
      as JSON under ``data/raw/synthetic_graphs/``.
    """
    tiers = [1, 2, 3]
    graphs_per_tier = 20

    manifest_path: Path = paths.data("raw", "graph_manifest.csv")
    # Ensure the parent directory exists (paths.data creates it)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with manifest_path.open(mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["graph_id", "tier", "seed"])

        for tier in tiers:
            log.info("Generating %d graphs for Tier %d", graphs_per_tier, tier)
            for i in range(graphs_per_tier):
                # Offset seeds uniquely per graph; we keep a simple linear scheme.
                seed_offset = (tier - 1) * graphs_per_tier + i
                sg = _generate_for_tier(tier, seed_offset)

                # ``generate_*`` functions already saved the JSON file via
                # ``_save_graph`` inside the generator module.
                if not isinstance(sg, StateGraph):
                    raise TypeError(
                        f"Generator for tier {tier} did not return a StateGraph"
                    )
                graph_id = sg.graph_id
                writer.writerow([graph_id, tier, SEED + seed_offset])

    log.info("Graph suite generation complete. Manifest written to %s", manifest_path)

if __name__ == "__main__":
    main()
