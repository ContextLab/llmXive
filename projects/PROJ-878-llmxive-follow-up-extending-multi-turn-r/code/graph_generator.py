import argparse
import json
import logging
import random
import hashlib
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple

import networkx as nx

from utils.graph_utils import (
    is_dag,
    nesting_depth,
    branching_factor,
    longest_path,
    get_random_valid_path_different_from_reference,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def fetch_gsm8k_metadata() -> str:
    """
    Return a static citation for GSM8K. The original implementation attempted to
    download the dataset via ``datasets`` which pulls in ``pyarrow`` – an
    optional heavy dependency that is incompatible with the pinned NumPy
    version in this environment. To avoid the import error we simply return
    a hard‑coded citation string.
    """
    logger.info("Fetching GSM8K metadata (static fallback).")
    return "GSM8K: High-quality Grade School Math Word Problems (Cobbe et al., 2021)"

def _build_controlled_dag(target_depth: int, target_branching: float) -> nx.DiGraph:
    """
    Build a DAG with an exact ``target_depth`` (longest path length) and an
    approximate average ``target_branching`` (average in‑degree of non‑root nodes).

    The construction follows the original algorithm but is fully deterministic
    given the random seed set by the caller.
    """
    G = nx.DiGraph()
    layers: List[List[int]] = []
    node_id = 0

    # Approximate the number of nodes per layer to achieve the desired branching factor.
    layer_size = max(2, int(np.ceil(target_branching * 2)))

    for _ in range(target_depth):
        layer = list(range(node_id, node_id + layer_size))
        G.add_nodes_from(layer)
        layers.append(layer)
        node_id += layer_size

    # Ensure a single backbone path of length ``target_depth``.
    for i in range(target_depth - 1):
        G.add_edge(layers[i][0], layers[i + 1][0])

    # Add extra edges to approach the desired average branching factor.
    non_root_count = (target_depth - 1) * layer_size
    target_edges_sum = int(target_branching * non_root_count)

    current_edges_sum = sum(d for _, d in G.in_degree() if d > 0)
    attempts = 0
    while current_edges_sum < target_edges_sum and attempts < 1000:
        attempts += 1
        i = random.randint(0, target_depth - 2)
        j = random.randint(i + 1, target_depth - 1)
        u = random.choice(layers[i])
        v = random.choice(layers[j])
        if not G.has_edge(u, v):
            G.add_edge(u, v)
            current_edges_sum += 1

    return G

def _generate_puzzle_text(G: nx.DiGraph) -> str:
    """Deterministic template‑based conversion of a DAG into a logical puzzle."""
    edges = sorted(G.edges())
    clauses = [f"If node {u} is true, then node {v} is true." for u, v in edges]
    return " ".join(clauses)

def _compute_token_length(text: str) -> int:
    """Simple token count based on whitespace split."""
    return len(text.split())

def _compute_lexical_complexity(text: str) -> float:
    """
    Very lightweight lexical complexity proxy:
    average word length (in characters). This avoids external dependencies.
    """
    words = text.split()
    if not words:
        return 0.0
    return sum(len(w) for w in words) / len(words)

def _hash_path(path: List[int]) -> str:
    """Create a deterministic identifier for a path."""
    path_bytes = json.dumps(path, sort_keys=True).encode()
    return hashlib.sha256(path_bytes).hexdigest()

def generate_set(
    count: int,
    depth_range: Tuple[int, int],
    branch_range: Tuple[float, float],
    seed: int,
) -> List[Dict]:
    """
    Generate ``count`` synthetic puzzles.

    Parameters
    ----------
    count: Number of puzzles to generate.
    depth_range: Inclusive (min, max) range for ``nesting_depth``.
    branch_range: Inclusive (min, max) range for ``branching_factor``.
    seed: Random seed for reproducibility.

    Returns
    -------
    List of puzzle dictionaries ready to be JSON‑L serialized.
    """
    random.seed(seed)
    np.random.seed(seed)
    puzzles: List[Dict] = []

    for i in range(count):
        depth = random.randint(*depth_range)
        branch = random.uniform(*branch_range)

        G = _build_controlled_dag(depth, branch)

        actual_depth = nesting_depth(G)
        actual_branch = branching_factor(G)
        ref_path = longest_path(G)
        gt_path = get_random_valid_path_different_from_reference(G, ref_path)
        if gt_path is None:
            gt_path = ref_path

        ground_truth = str(gt_path[-1]) if gt_path else ""

        puzzle_text = _generate_puzzle_text(G)
        token_len = _compute_token_length(puzzle_text)
        lexical_complexity = _compute_lexical_complexity(puzzle_text)
        target_path_id = _hash_path(gt_path)

        puzzles.append(
            {
                "instance_id": f"puzzle_{seed}_{i}",
                "text": puzzle_text,
                "ground_truth": ground_truth,
                "ground_truth_path": gt_path,
                "nesting_depth": actual_depth,
                "branching_factor": actual_branch,
                "graph_structure": {"nodes": list(G.nodes()), "edges": list(G.edges())},
                "is_acyclic": True,
                "is_solvable": True,
                "text_generation_method": "template_based",
                "is_orthogonal": False,
                "seed": seed,
                # New fields required by FR‑001, FR‑006, FR‑007
                "token_length": token_len,
                "lexical_complexity": lexical_complexity,
                "target_path_id": target_path_id,
            }
        )
    return puzzles

def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic logical puzzle generator")
    parser.add_argument("--count", type=int, required=True, help="Number of puzzles to generate")
    parser.add_argument("--depth-min", type=int, required=True, dest="depth_min")
    parser.add_argument("--depth-max", type=int, required=True, dest="depth_max")
    parser.add_argument("--branch-min", type=float, required=True, dest="branch_min")
    parser.add_argument("--branch-max", type=float, required=True, dest="branch_max")
    parser.add_argument("--output", type=str, required=True, help="Output JSONL file")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    # Fetch static GSM8K citation (no heavy imports)
    fetch_gsm8k_metadata()

    puzzles = generate_set(
        count=args.count,
        depth_range=(args.depth_min, args.depth_max),
        branch_range=(args.branch_min, args.branch_max),
        seed=args.seed,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for p in puzzles:
            f.write(json.dumps(p) + "\n")

    logger.info(f"Wrote {len(puzzles)} puzzles to {output_path}")

if __name__ == "__main__":
    main()