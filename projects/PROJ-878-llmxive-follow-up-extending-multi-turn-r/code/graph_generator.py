import argparse
import json
import random
import math
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import networkx as nx

# Import utilities from the shared graph_utils module
from utils.graph_utils import (
    is_dag,
    nesting_depth,
    branching_factor,
    graph_to_dict,
)

logger = logging.getLogger(__name__)

class LogicalPuzzleGenerator:
    """Generates logical puzzles represented as DAGs with controlled topology."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(self.seed)

    def _generate_base_dag(self, target_depth: int, target_branching: float) -> nx.DiGraph:
        """
        Construct a DAG that roughly respects the requested depth and branching factor.
        The construction proceeds layer‑by‑layer to guarantee acyclicity.
        """
        G = nx.DiGraph()
        num_layers = target_depth
        # Heuristic: more nodes per layer yields higher possible branching
        nodes_per_layer = max(2, int(target_branching * 2))

        layers: List[List[str]] = []
        for i in range(num_layers):
            layer = [f"L{i}_N{j}" for j in range(nodes_per_layer)]
            layers.append(layer)
            G.add_nodes_from(layer)

        # Ensure a path that spans all layers (the longest path)
        for i in range(num_layers - 1):
            for u in layers[i]:
                # Connect each node to at least one node in the next layer
                v = random.choice(layers[i + 1])
                G.add_edge(u, v)

        # Add extra edges to increase branching without creating cycles
        for i in range(num_layers - 2):
            for u in layers[i]:
                v = random.choice(layers[i + 2])
                G.add_edge(u, v)

        return G

    def _calculate_metrics(self, G: nx.DiGraph) -> Tuple[int, float]:
        """Return (nesting_depth, branching_factor) for a graph."""
        return nesting_depth(G), branching_factor(G)

    def generate_single_puzzle(
        self,
        target_depth: int,
        target_branching: float,
        max_attempts: int = 100,
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt to generate a single puzzle that meets the depth/branching
        tolerances (±1 for depth, ±1.0 for branching). Returns a dict with
        the graph and its metrics, or None if generation fails.
        """
        for attempt in range(max_attempts):
            G = self._generate_base_dag(target_depth, target_branching)

            if not is_dag(G):
                continue

            depth, branch = self._calculate_metrics(G)

            if abs(depth - target_depth) <= 1 and abs(branch - target_branching) <= 1.0:
                return {
                    "graph": G,
                    "depth": depth,
                    "branch": branch,
                }

        logger.warning(
            f"Failed to generate graph for depth={target_depth}, branch={target_branching}"
        )
        return None

def _select_ground_truth_path(G: nx.DiGraph) -> Tuple[List[Any], List[Any]]:
    """
    Choose a source‑sink pair based on the longest DAG path, then return a
    ground‑truth path that is *different* from that longest path when possible.
    If only one simple path exists, the longest path is returned (with a warning).
    """
    # Compute the longest path using networkx's DAG longest path algorithm
    longest_path = nx.algorithms.dag_longest_path(G)
    if not longest_path:
        raise ValueError("Generated DAG has no path.")

    source = longest_path[0]
    target = longest_path[-1]

    # Enumerate all simple paths between source and target
    all_paths = list(nx.all_simple_paths(G, source=source, target=target))
    if not all_paths:
        raise ValueError("No path between source and target in generated DAG.")

    # Remove the longest path from the alternatives
    alternatives = [p for p in all_paths if p != longest_path]

    if alternatives:
        gt_path = random.choice(alternatives)
    else:
        gt_path = longest_path
        logger.warning("Only one path exists; using longest path as ground truth.")

    return gt_path, longest_path

def _serialize_puzzle(
    idx: int,
    G: nx.DiGraph,
    depth: int,
    branch: float,
    ground_truth_path: List[Any],
    longest_path: List[Any],
) -> Dict[str, Any]:
    """
    Convert a generated graph and its metadata into the JSONL schema
    required by downstream tasks.
    """
    # Deterministic textual representation – simple, yet reproducible
    text = (
        f"Puzzle ID: {idx}\\n"
        f"Nodes: {list(G.nodes())}\\n"
        f"Edges: {list(G.edges())}\\n"
        f"Find a path from {ground_truth_path[0]} to {ground_truth_path[-1]} "
        f"that is NOT the longest path ({len(longest_path)} steps).\\n"
        f"Ground‑truth path (perturbed): {ground_truth_path}\\n"
    )

    puzzle = {
        "instance_id": f"puzzle_{idx:04d}",
        "text": text,
        "ground_truth_path": ground_truth_path,
        "nesting_depth": depth,
        "branching_factor": branch,
        "graph_structure": graph_to_dict(G),
        "is_acyclic": True,
        "is_solvable": True,
        "text_generation_method": "template_based",
        "is_orthogonal": None,  # will be filled after orthogonalization check
        "seed": random.getstate(),
    }
    return puzzle

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
    Generate a batch of puzzles while enforcing the orthogonalization
    constraint (|Pearson correlation| < max_correlation) across the batch.
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    generator = LogicalPuzzleGenerator(seed=seed)
    candidates: List[Dict[str, Any]] = []
    attempts = 0
    max_total_attempts = num_instances * 500

    logger.info(
        f"Generating {num_instances} puzzles (depth {min_depth}-{max_depth}, branching {min_branching}-{max_branching})."
    )

    while len(candidates) < num_instances and attempts < max_total_attempts:
        attempts += 1
        target_depth = random.randint(min_depth, max_depth)
        target_branch = random.uniform(min_branching, max_branching)

        result = generator.generate_single_puzzle(target_depth, target_branch, max_attempts=50)
        if result is None:
            continue

        G = result["graph"]
        depth = result["depth"]
        branch = result["branch"]

        # Store raw graph and metrics; ground‑truth path will be added later
        candidates.append(
            {
                "graph": G,
                "nesting_depth": depth,
                "branching_factor": branch,
            }
        )

    if len(candidates) < num_instances:
        logger.error(
            f"Could only generate {len(candidates)} puzzles after {attempts} attempts."
        )
        # Continue with what we have – downstream checks will flag shortfall.

    # Orthogonalization: ensure correlation below threshold.
    def _correlation(puzzles: List[Dict[str, Any]]) -> float:
        d = [p["nesting_depth"] for p in puzzles]
        b = [p["branching_factor"] for p in puzzles]
        if len(d) < 2:
            return 0.0
        mean_d = sum(d) / len(d)
        mean_b = sum(b) / len(b)
        num = sum((di - mean_d) * (bi - mean_b) for di, bi in zip(d, b))
        den_d = math.sqrt(sum((di - mean_d) ** 2 for di in d))
        den_b = math.sqrt(sum((bi - mean_b) ** 2 for bi in b))
        if den_d == 0 or den_b == 0:
            return 0.0
        return num / (den_d * den_b)

    final_puzzles = []
    attempts_ortho = 0
    max_ortho_attempts = 20
    while attempts_ortho < max_ortho_attempts:
        attempts_ortho += 1
        random.shuffle(candidates)
        selected = candidates[:num_instances]
        r = _correlation(selected)
        logger.info(f"Orthogonalization attempt {attempts_ortho}: correlation = {r:.4f}")
        if abs(r) <= max_correlation:
            final_puzzles = selected
            break
    if not final_puzzles:
        logger.warning(
            f"Failed to meet orthogonalization after {max_ortho_attempts} attempts; using best effort."
        )
        final_puzzles = candidates[:num_instances]

    # Build final JSONL records
    output: List[Dict[str, Any]] = []
    for idx, item in enumerate(final_puzzles):
        G = item["graph"]
        depth = item["nesting_depth"]
        branch = item["branching_factor"]
        gt_path, longest = _select_ground_truth_path(G)
        puzzle_dict = _serialize_puzzle(
            idx=idx,
            G=G,
            depth=depth,
            branch=branch,
            ground_truth_path=gt_path,
            longest_path=longest,
        )
        # Orthogonal flag – set after overall correlation check
        puzzle_dict["is_orthogonal"] = abs(_correlation(final_puzzles)) < max_correlation
        output.append(puzzle_dict)

    return output

def _write_jsonl(records: List[Dict[str, Any]], path: Path) -> None:
    """Write a list of dictionaries to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            json.dump(rec, f)
            f.write("\n")

def _write_validation_metrics(
    primary: List[Dict[str, Any]],
    aux: List[Dict[str, Any]],
    output_path: Path,
    attempts_primary: int,
    attempts_aux: int,
) -> None:
    """Create the validation_metrics.json file with required diagnostics."""
    # Compute correlation across the combined set
    combined = primary + aux
    depths = [p["nesting_depth"] for p in combined]
    branches = [p["branching_factor"] for p in combined]
    if len(depths) >= 2:
        mean_d = sum(depths) / len(depths)
        mean_b = sum(branches) / len(branches)
        num = sum((d - mean_d) * (b - mean_b) for d, b in zip(depths, branches))
        den_d = math.sqrt(sum((d - mean_d) ** 2 for d in depths))
        den_b = math.sqrt(sum((b - mean_b) ** 2 for b in branches))
        corr = num / (den_d * den_b) if den_d and den_b else 0.0
    else:
        corr = 0.0

    metrics = {
        "total_puzzles": len(combined),
        "samples_generated_primary": len(primary),
        "samples_generated_aux": len(aux),
        "samples_attempted_primary": attempts_primary,
        "samples_attempted_aux": attempts_aux,
        "correlation_coefficient": corr,
        "cycle_rate": "[deferred]",
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

def _write_checksums(files: List[Path], checksum_path: Path) -> None:
    """Write SHA‑256 checksum lines compatible with `sha256sum -c`."""
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with checksum_path.open("w", encoding="utf-8") as out:
        for file_path in files:
            sha256 = hashlib.sha256()
            with file_path.open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            checksum = sha256.hexdigest()
            rel = file_path.relative_to(Path.cwd())
            out.write(f"{checksum}  {rel}\\n")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic logical puzzles with controlled topology."
    )
    parser.add_argument(
        "--count",
        type=int,
        required=True,
        help="Number of puzzles to generate.",
    )
    parser.add_argument(
        "--depth-min",
        type=int,
        required=True,
        help="Minimum nesting depth.",
    )
    parser.add_argument(
        "--depth-max",
        type=int,
        required=True,
        help="Maximum nesting depth.",
    )
    parser.add_argument(
        "--branch-min",
        type=float,
        required=True,
        help="Minimum branching factor.",
    )
    parser.add_argument(
        "--branch-max",
        type=float,
        required=True,
        help="Maximum branching factor.",
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

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Primary generation
    primary_records = generate_batch(
        num_instances=args.count,
        min_depth=args.depth_min,
        max_depth=args.depth_max,
        min_branching=args.branch_min,
        max_branching=args.branch_max,
        max_correlation=0.2,
        seed=args.seed,
    )

    output_path = Path(args.output)
    _write_jsonl(primary_records, output_path)

    # Validation metrics – only primary metrics are available at this point.
    validation_path = Path("data/validation_metrics.json")
    _write_validation_metrics(
        primary=primary_records,
        aux=[],
        output_path=validation_path,
        attempts_primary=args.count * 500,  # rough upper bound used in generator
        attempts_aux=0,
    )

    # Checksums for the primary file
    checksum_path = Path("data/checksums_primary.txt")
    _write_checksums([output_path], checksum_path)

    logger.info(f"Generated {len(primary_records)} puzzles → {output_path}")
    logger.info(f"Validation metrics written to {validation_path}")
    logger.info(f"Checksums written to {checksum_path}")

if __name__ == "__main__":
    main()
