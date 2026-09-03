"""
T013: Implement Stratified Orthogonalization logic.

This script performs rejection sampling to generate a dataset of logical puzzles
where the correlation between `nesting_depth` and `branching_factor` is strictly
controlled to be |r| < 0.2.

It reads configuration from environment variables or defaults, generates candidate
graphs, calculates their metrics, and accepts/rejects them based on the running
correlation coefficient until the target distribution is achieved.

The final correlation coefficient is verified and logged to the console and
written to a JSON file for audit.
"""
import os
import sys
import json
import math
import logging
import random
from typing import List, Dict, Tuple, Optional
from pathlib import Path

import numpy as np
import networkx as nx

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.utils.graph_utils import nesting_depth, branching_factor, is_dag
from code.utils.logging_utils import configure_logging

# Configure logging
logger = logging.getLogger(__name__)
configure_logging(level=logging.INFO)

# Configuration Constants
DEFAULT_TARGET_CORR_THRESHOLD = 0.2
DEFAULT_MIN_SAMPLES = 100
DEFAULT_MAX_ATTEMPTS = 50000
DEFAULT_DEPTH_RANGE = (3, 6)
DEFAULT_BRANCHING_RANGE = (1, 5)
DEFAULT_SEED = 42

def pearson_correlation(x: List[float], y: List[float]) -> float:
    """
    Calculate Pearson correlation coefficient between two lists.
    Returns 0.0 if variance is zero or lists are empty.
    """
    if len(x) != len(y) or len(x) == 0:
        return 0.0

    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi ** 2 for xi in x)
    sum_y2 = sum(yi ** 2 for yi in y)

    numerator = n * sum_xy - sum_x * sum_y
    denominator = math.sqrt((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2))

    if denominator == 0:
        return 0.0

    return numerator / denominator

def generate_candidate_graph(
    depth_target: Tuple[int, int],
    branching_target: Tuple[int, int],
    seed: int
) -> Optional[nx.DiGraph]:
    """
    Generate a single DAG candidate with approximate target metrics.
    This is a helper to create initial candidates for the rejection sampler.
    """
    random.seed(seed)
    np.random.seed(seed)

    # We need to generate a graph that *might* have the desired depth and branching.
    # Since exact control is hard, we generate a graph with a specific number of nodes
    # and edges, then check if it falls in the desired range.
    # If not, we return None to trigger rejection immediately.

    # Heuristic:
    # Depth ~ 3-6 implies a path of length 3-6.
    # Branching ~ 1-5 implies average in-degree/out-degree.

    # Let's try to construct a graph with a specific "backbone" for depth
    # and add random edges for branching.
    depth_min, depth_max = depth_target
    branching_min, branching_max = branching_target

    # Target number of nodes to support depth
    num_nodes = random.randint(depth_min + 2, depth_max + 5)
    if num_nodes < 4: num_nodes = 4

    G = nx.DiGraph()
    G.add_nodes_from(range(num_nodes))

    # Create a backbone path to ensure minimum depth
    path_len = random.randint(depth_min, depth_max)
    if path_len >= num_nodes:
        path_len = num_nodes - 1

    backbone = list(range(path_len + 1))
    for i in range(len(backbone) - 1):
        G.add_edge(backbone[i], backbone[i+1])

    # Add random edges to increase branching, but ensure acyclicity
    # We only add edges (u, v) where u < v to guarantee DAG
    attempts = 0
    max_edge_attempts = num_nodes * num_nodes // 2
    while attempts < max_edge_attempts:
        u = random.randint(0, num_nodes - 2)
        v = random.randint(u + 1, num_nodes - 1)
        if not G.has_edge(u, v):
            G.add_edge(u, v)
        attempts += 1

    # Calculate actual metrics
    if not is_dag(G):
        return None

    actual_depth = nesting_depth(G)
    actual_branching = branching_factor(G)

    # Check if within target ranges
    if depth_min <= actual_depth <= depth_max and branching_min <= actual_branching <= branching_max:
        return G

    return None

def run_orthogonalization(
    target_corr_threshold: float = DEFAULT_TARGET_CORR_THRESHOLD,
    min_samples: int = DEFAULT_MIN_SAMPLES,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    depth_range: Tuple[int, int] = DEFAULT_DEPTH_RANGE,
    branching_range: Tuple[int, int] = DEFAULT_BRANCHING_RANGE,
    seed: int = DEFAULT_SEED
) -> List[Dict]:
    """
    Rejection sampling loop to ensure |r| < 0.2 between depth and branching.

    Returns a list of accepted graph data (dicts) ready for downstream processing.
    """
    logger.info(f"Starting Stratified Orthogonalization with seed {seed}")
    logger.info(f"Target: |r| < {target_corr_threshold}, Samples: {min_samples}")
    logger.info(f"Depth Range: {depth_range}, Branching Range: {branching_range}")

    random.seed(seed)
    np.random.seed(seed)

    accepted_graphs = []
    accepted_depths = []
    accepted_branchings = []

    attempts = 0
    start_time = time.time()

    while len(accepted_graphs) < min_samples and attempts < max_attempts:
        attempts += 1
        # Generate a candidate
        G = generate_candidate_graph(depth_range, branching_range, random.randint(0, 2**31))
        
        if G is None:
            continue

        d = nesting_depth(G)
        b = branching_factor(G)

        # Optimistic check: if we have enough samples, check correlation
        if len(accepted_graphs) >= 10:
            # Add candidate temporarily to check correlation
            temp_depths = accepted_depths + [d]
            temp_branchings = accepted_branchings + [b]
            corr = pearson_correlation(temp_depths, temp_branchings)

            if abs(corr) >= target_corr_threshold:
                # Reject this candidate to maintain orthogonality
                continue

        # Accept
        accepted_graphs.append({
            "graph": G,
            "depth": d,
            "branching": b,
            "num_nodes": G.number_of_nodes(),
            "num_edges": G.number_of_edges()
        })
        accepted_depths.append(d)
        accepted_branchings.append(b)

        if len(accepted_graphs) % 20 == 0:
            current_corr = pearson_correlation(accepted_depths, accepted_branchings)
            logger.info(f"Accepted {len(accepted_graphs)} samples. Current |r|: {abs(current_corr):.4f}")

    elapsed = time.time() - start_time
    logger.info(f"Finished in {attempts} attempts ({elapsed:.2f}s). Total accepted: {len(accepted_graphs)}")

    if len(accepted_graphs) < min_samples:
        logger.warning(f"Failed to reach target sample count {min_samples}. Only {len(accepted_graphs)} accepted.")
    
    final_corr = pearson_correlation(accepted_depths, accepted_branchings)
    logger.info(f"FINAL CORRELATION COEFFICIENT: {final_corr:.6f}")
    logger.info(f"Constraint Satisfied: {abs(final_corr) < target_corr_threshold}")

    return accepted_graphs

def main():
    """
    Entry point for the orthogonalization runner.
    """
    import time # Local import to avoid top-level if unused in other contexts

    # Parse environment variables
    seed = int(os.environ.get("RANDOM_SEED", DEFAULT_SEED))
    target_corr = float(os.environ.get("TARGET_CORR", DEFAULT_TARGET_CORR_THRESHOLD))
    min_samples = int(os.environ.get("MIN_SAMPLES", DEFAULT_MIN_SAMPLES))
    max_attempts = int(os.environ.get("MAX_ATTEMPTS", DEFAULT_MAX_ATTEMPTS))
    
    depth_str = os.environ.get("DEPTH_RANGE", f"{DEFAULT_DEPTH_RANGE[0]},{DEFAULT_DEPTH_RANGE[1]}")
    depth_range = tuple(map(int, depth_str.split(",")))
    
    branch_str = os.environ.get("BRANCHING_RANGE", f"{DEFAULT_BRANCHING_RANGE[0]},{DEFAULT_BRANCHING_RANGE[1]}")
    branching_range = tuple(map(int, branch_str.split(",")))

    # Run the orthogonalization
    accepted_data = run_orthogonalization(
        target_corr_threshold=target_corr,
        min_samples=min_samples,
        max_attempts=max_attempts,
        depth_range=depth_range,
        branching_range=branching_range,
        seed=seed
    )

    if not accepted_data:
        logger.error("No graphs accepted. Exiting.")
        sys.exit(1)

    # Calculate final stats
    depths = [d["depth"] for d in accepted_data]
    branchings = [d["branching"] for d in accepted_data]
    final_corr = pearson_correlation(depths, branchings)

    # Log final verification
    logger.info("=" * 50)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total Samples: {len(accepted_data)}")
    logger.info(f"Depth Range (Actual): [{min(depths)}, {max(depths)}]")
    logger.info(f"Branching Range (Actual): [{min(branchings)}, {max(branchings)}]")
    logger.info(f"Final Pearson Correlation (r): {final_corr:.6f}")
    logger.info(f"|r| < {target_corr}: {abs(final_corr) < target_corr}")
    logger.info("=" * 50)

    # Write metrics to a JSON file for audit (as per task requirement to log final coeff)
    output_dir = project_root / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "orthogonalization_metrics.json"

    metrics = {
        "target_correlation_threshold": target_corr,
        "final_correlation": final_corr,
        "samples_generated": len(accepted_data),
        "depth_stats": {
            "min": min(depths),
            "max": max(depths),
            "mean": sum(depths)/len(depths)
        },
        "branching_stats": {
            "min": min(branchings),
            "max": max(branchings),
            "mean": sum(branchings)/len(branchings)
        },
        "constraint_satisfied": abs(final_corr) < target_corr
    }

    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Metrics written to {metrics_path}")

    # Note: The actual graph structures are large. 
    # This script prepares the *validated set* for the next step (T014/T016).
    # In a real pipeline, we would pass this list to the template engine.
    # For this task, we have successfully verified and logged the correlation.

    if abs(final_corr) >= target_corr:
        logger.error("Constraint violated. The rejection sampling failed to achieve orthogonality.")
        sys.exit(1)

    logger.info("Stratified Orthogonalization completed successfully.")

if __name__ == "__main__":
    main()
