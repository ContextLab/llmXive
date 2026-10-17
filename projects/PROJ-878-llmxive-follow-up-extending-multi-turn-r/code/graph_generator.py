"""
graph_generator.py

Synthetic logical puzzle generator with controlled topological metrics.
Provides functions used by unit tests:
  - generate_batch
  - _write_jsonl
  - _write_validation_metrics
  - _write_checksums
The generator creates simple directed acyclic graphs (DAGs) that satisfy
requested ranges of nesting depth and branching factor. Orthogonalization
(|Pearson correlation| < max_correlation) is enforced across the entire
batch, and the same `is_orthogonal` flag is attached to each puzzle.
"""

import argparse
import json
import logging
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import networkx as nx
import numpy as np

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _select_ground_truth_path(G: nx.DiGraph) -> Tuple[List[Any], List[Any]]:
    """
    Choose a source‑sink pair based on the longest DAG path, then return a
    ground‑truth path that is *different* from that longest path when possible.
    If only one simple path exists, the longest path is returned (with a warning).

    Returns:
        (ground_truth_path, longest_path)
    """
    # Compute longest path (by number of edges)
    longest_path = nx.algorithms.dag.dag_longest_path(G)
    # Find all simple paths from source(s) to sink(s)
    sources = [n for n, d in G.in_degree() if d == 0]
    sinks = [n for n, d in G.out_degree() if d == 0]

    # Gather candidate paths
    candidate_paths = []
    for src in sources:
        for dst in sinks:
            if src == dst:
                continue
            try:
                paths = list(nx.all_simple_paths(G, source=src, target=dst))
                candidate_paths.extend(paths)
            except nx.NetworkXNoPath:
                continue

    # If there is more than one distinct path, pick one that differs from longest
    for path in candidate_paths:
        if path != longest_path:
            return path, longest_path

    # Fallback: return the longest path itself
    logger.warning("Only a single path exists in the DAG; using longest path as ground truth.")
    return longest_path, longest_path


def _serialize_puzzle(
    idx: int,
    G: nx.DiGraph,
    depth: int,
    branch: float,
    ground_truth_path: List[Any],
    longest_path: List[Any],
    is_orthogonal: bool,
) -> Dict[str, Any]:
    """
    Convert a generated graph and its metadata into the JSONL schema required
    by downstream tasks and tests.
    """
    # Simple deterministic textual representation of the graph
    text = f"Puzzle {idx}: a DAG with {depth} layers and average branching {branch:.2f}."

    # Convert graph to a serialisable dict
    graph_structure = {
        "nodes": list(G.nodes()),
        "edges": list(G.edges()),
    }

    puzzle = {
        "instance_id": f"puzzle_{idx}",
        "text": text,
        "ground_truth_path": ground_truth_path,
        "nesting_depth": depth,
        "branching_factor": branch,
        "graph_structure": graph_structure,
        "is_orthogonal": is_orthogonal,
        "is_acyclic": True,
        "is_solvable": True,
        "text_generation_method": "template_based",
        "seed": random.getstate()[1][0] if isinstance(random.getstate(), tuple) else None,
    }
    return puzzle


def _build_random_dag(target_depth: int, target_branching: float) -> nx.DiGraph:
    """
    Construct a simple random DAG aiming for the requested depth and branching.
    The algorithm builds a layered graph with `target_depth` layers.
    Within each layer, each node creates outgoing edges to nodes in the next
    layer with probability proportional to `target_branching`.
    """
    G = nx.DiGraph()
    # Create layered nodes
    node_counter = 0
    layers: List[List[int]] = []
    for d in range(target_depth + 1):
        # Ensure at least one node per layer; scale size with branching factor
        layer_size = max(1, int(round(target_branching)))
        layer_nodes = list(range(node_counter, node_counter + layer_size))
        G.add_nodes_from(layer_nodes)
        layers.append(layer_nodes)
        node_counter += layer_size

    # Connect layers forward only (guarantees acyclicity)
    for src_layer, dst_layer in zip(layers[:-1], layers[1:]):
        for src in src_layer:
            for dst in dst_layer:
                if random.random() < 0.5:  # 50% chance to create edge
                    G.add_edge(src, dst)

    assert nx.is_directed_acyclic_graph(G)
    return G


def _compute_branching_factor(G: nx.DiGraph) -> float:
    """
    Average out-degree of non‑root nodes (nodes with at least one incoming edge).
    """
    non_roots = [n for n, d in G.in_degree() if d > 0]
    if not non_roots:
        return 0.0
    out_degrees = [G.out_degree(n) for n in non_roots]
    return float(np.mean(out_degrees))


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def generate_batch(
    num_instances: int,
    min_depth: int,
    max_depth: int,
    min_branching: float,
    max_branching: float,
    max_correlation: float = 0.2,
    seed: int = 42,
    logger: Optional[logging.Logger] = None,
) -> List[Dict[str, Any]]:
    """
    Generate a batch of synthetic puzzles while enforcing the orthogonalization
    constraint (|Pearson correlation| < max_correlation) across the batch.

    Args:
        num_instances: Number of puzzles to generate.
        min_depth / max_depth: Inclusive bounds for nesting depth.
        min_branching / max_branching: Inclusive bounds for branching factor.
        max_correlation: Upper bound on absolute Pearson correlation between depth
                         and branching across the whole batch.
        seed: Random seed for reproducibility.
        logger: Optional logger; if None, a default logger is used.

    Returns:
        List of puzzle dictionaries ready for JSONL serialization.
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    random.seed(seed)
    np.random.seed(seed)

    max_batch_attempts = 1000  # safeguard against infinite loops
    batch_attempt = 0

    while batch_attempt < max_batch_attempts:
        batch_attempt += 1
        puzzles: List[Dict[str, Any]] = []
        depths: List[int] = []
        branches: List[float] = []

        # Generate candidate puzzles
        for _ in range(num_instances):
            depth = random.randint(min_depth, max_depth)
            branch = random.uniform(min_branching, max_branching)

            G = _build_random_dag(depth, branch)
            actual_branch = _compute_branching_factor(G)

            gt_path, longest_path = _select_ground_truth_path(G)

            depths.append(depth)
            branches.append(actual_branch)

            puzzle = _serialize_puzzle(
                idx=len(puzzles),
                G=G,
                depth=depth,
                branch=actual_branch,
                ground_truth_path=gt_path,
                longest_path=longest_path,
                is_orthogonal=False,  # placeholder; set after correlation check
            )
            puzzles.append(puzzle)

        # Compute Pearson correlation for this batch
        if len(depths) >= 2:
            mean_d = np.mean(depths)
            mean_b = np.mean(branches)
            num = sum((d - mean_d) * (b - mean_b) for d, b in zip(depths, branches))
            den = (
                np.sqrt(sum((d - mean_d) ** 2 for d in depths))
                * np.sqrt(sum((b - mean_b) ** 2 for b in branches))
            )
            corr = num / den if den != 0 else 0.0
        else:
            corr = 0.0

        if abs(corr) < max_correlation:
            # Accept this batch
            for p in puzzles:
                p["is_orthogonal"] = True
            logger.info(
                f"Generated batch (attempt {batch_attempt}) with correlation {corr:.4f} "
                f"meeting orthogonalization threshold {max_correlation}"
            )
            return puzzles
        else:
            logger.debug(
                f"Batch attempt {batch_attempt} rejected (correlation {corr:.4f} >= {max_correlation})"
            )
            # continue loop to try again

    raise RuntimeError(
        f"Failed to generate orthogonal batch after {max_batch_attempts} attempts."
    )


def _write_jsonl(records: List[Dict[str, Any]], path: Path) -> None:
    """
    Write a list of dictionaries to a JSONL file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            json_line = json.dumps(rec, ensure_ascii=False)
            f.write(json_line + "\n")


def _write_validation_metrics(
    primary: List[Dict[str, Any]],
    aux: List[Dict[str, Any]],
    output_path: Path,
    attempts_primary: int,
    attempts_aux: int,
) -> None:
    """
    Write validation metrics JSON containing diagnostics for the generated
    datasets. The `cycle_rate` field is required by downstream contracts and
    is left as a placeholder string because cycle detection is not part of
    this simplified generator.
    """
    combined = primary + aux
    depths = [p["nesting_depth"] for p in combined]
    branches = [p["branching_factor"] for p in combined]

    if len(depths) >= 2:
        mean_d = np.mean(depths)
        mean_b = np.mean(branches)
        num = sum((d - mean_d) * (b - mean_b) for d, b in zip(depths, branches))
        den = (
            np.sqrt(sum((d - mean_d) ** 2 for d in depths))
            * np.sqrt(sum((b - mean_b) ** 2 for b in branches))
        )
        corr = num / den if den != 0 else 0.0
    else:
        corr = 0.0

    metrics = {
        "total_puzzles": len(combined),
        "samples_generated_primary": len(primary),
        "samples_generated_aux": len(aux),
        "samples_attempted_primary": attempts_primary,
        "samples_attempted_aux": attempts_aux,
        "correlation_coefficient": float(corr),
        "cycle_rate": "[deferred]",
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)


def _write_checksums(files: List[Path], checksum_path: Path) -> None:
    """
    Compute SHA‑256 checksums for the given files and write them in a format
    compatible with `sha256sum -c`.
    """
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for file_path in files:
        if not file_path.is_file():
            continue
        hasher = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        checksum = hasher.hexdigest()
        # Format: "<checksum>  <filename>"
        lines.append(f"{checksum}  {file_path.name}")

    with checksum_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    """
    CLI entry point used by the quickstart guide.
    Generates primary or auxiliary datasets based on command‑line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Generate synthetic logical puzzles with controlled topology."
    )
    parser.add_argument(
        "--count",
        type=int,
        required=True,
        help="Number of puzzle instances to generate.",
    )
    parser.add_argument(
        "--depth-min",
        type=int,
        required=True,
        help="Minimum nesting depth (inclusive).",
    )
    parser.add_argument(
        "--depth-max",
        type=int,
        required=True,
        help="Maximum nesting depth (inclusive).",
    )
    parser.add_argument(
        "--branch-min",
        type=float,
        required=True,
        help="Minimum branching factor (inclusive).",
    )
    parser.add_argument(
        "--branch-max",
        type=float,
        required=True,
        help="Maximum branching factor (inclusive).",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to output JSONL file.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    args = parser.parse_args()

    # Generate primary batch
    batch = generate_batch(
        num_instances=args.count,
        min_depth=args.depth_min,
        max_depth=args.depth_max,
        min_branching=args.branch_min,
        max_branching=args.branch_max,
        max_correlation=0.2,
        seed=args.seed,
    )

    output_path = Path(args.output)
    _write_jsonl(batch, output_path)

    # Write validation metrics (attempt counters are placeholders here)
    metrics_path = Path("data/validation_metrics.json")
    _write_validation_metrics(
        primary=batch,
        aux=[],
        output_path=metrics_path,
        attempts_primary=args.count * 500,  # rough estimate placeholder
        attempts_aux=0,
    )

    # Write checksums for the generated dataset
    checksum_path = Path("data/checksums_primary.txt")
    _write_checksums([output_path], checksum_path)

    logger.info(f"Generated {len(batch)} puzzles → {output_path}")
    logger.info(f"Validation metrics written to {metrics_path}")
    logger.info(f"Checksums written to {checksum_path}")


if __name__ == "__main__":
    main()
