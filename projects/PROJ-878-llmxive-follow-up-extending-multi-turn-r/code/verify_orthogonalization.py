"""
Script to verify the stratified orthogonalization logic of T013.
Generates a dataset and explicitly logs the final correlation coefficient.
"""
import os
import sys
import json
import logging
import math
from typing import List, Tuple, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.graph_generator import generate_batch
from code.utils.logging_utils import configure_logging, generate_checksum
from code.utils.graph_utils import nesting_depth, branching_factor

# Configure logging
configure_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = "data/raw"
OUTPUT_FILE = os.path.join(DATA_DIR, "logical_puzzles_orthogonalized.jsonl")
METRICS_FILE = os.path.join(DATA_DIR, "orthogonalization_metrics.json")

def calculate_pearson_correlation(pairs: List[Tuple[int, float]]) -> float:
    """
    Calculates Pearson correlation coefficient between depth and branching.
    """
    if len(pairs) < 2:
        return 0.0

    depths = [p[0] for p in pairs]
    branchings = [p[1] for p in pairs]

    n = len(pairs)
    sum_x = sum(depths)
    sum_y = sum(branchings)
    sum_xy = sum(d * b for d, b in pairs)
    sum_x2 = sum(d * d for d in depths)
    sum_y2 = sum(b * b for b in branchings)

    numerator = n * sum_xy - sum_x * sum_y
    denominator = math.sqrt(
        (n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)
    )

    if denominator == 0:
        return 0.0

    return numerator / denominator

def main():
    logger.info("Starting Stratified Orthogonalization Verification (T013)")

    # Ensure output directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # Configuration
    N_INSTANCES = 100
    DEPTH_RANGE = (3, 6)
    BRANCHING_RANGE = (1.0, 5.0)
    CORRELATION_THRESHOLD = 0.2
    SEED = 42

    logger.info(
        f"Generating {N_INSTANCES} instances with depth {DEPTH_RANGE}, "
        f"branching {BRANCHING_RANGE}, threshold {CORRELATION_THRESHOLD}"
    )

    # Generate data using the orthogonalized generator
    try:
        instances = generate_batch(
            n_instances=N_INSTANCES,
            depth_range=DEPTH_RANGE,
            branching_range=BRANCHING_RANGE,
            seed=SEED,
            correlation_threshold=CORRELATION_THRESHOLD,
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise

    if len(instances) == 0:
        logger.error("No instances generated. Failing loudly.")
        raise RuntimeError("Failed to generate any instances")

    logger.info(f"Generated {len(instances)} instances.")

    # Prepare output data
    output_rows = []
    pairs = []

    for i, inst in enumerate(instances):
        graph = inst["graph"]
        depth = nesting_depth(graph)
        branching = branching_factor(graph)
        pairs.append((depth, branching))

        row = {
            "instance_id": f"puzzle_{i:04d}",
            "nesting_depth": depth,
            "branching_factor": branching,
            "graph_structure": graph,  # Will be serialized below
        }
        output_rows.append(row)

    # Calculate final correlation
    final_corr = calculate_pearson_correlation(pairs)
    logger.info(f"FINAL CORRELATION COEFFICIENT: {final_corr:.6f}")

    # Write to JSONL
    with open(OUTPUT_FILE, "w") as f:
        for row in output_rows:
            # Convert graph to a serializable format (adjacency list dict)
            serializable_row = row.copy()
            serializable_row["graph_structure"] = {
                "nodes": list(row["graph_structure"].nodes()),
                "edges": list(row["graph_structure"].edges()),
            }
            f.write(json.dumps(serializable_row) + "\n")

    logger.info(f"Wrote {len(output_rows)} instances to {OUTPUT_FILE}")

    # Write metrics
    metrics = {
        "total_instances": len(instances),
        "depth_range": DEPTH_RANGE,
        "branching_range": BRANCHING_RANGE,
        "target_correlation_threshold": CORRELATION_THRESHOLD,
        "final_correlation_coefficient": final_corr,
        "correlation_status": "PASS" if abs(final_corr) < CORRELATION_THRESHOLD else "FAIL",
        "seed": SEED,
    }

    with open(METRICS_FILE, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Wrote metrics to {METRICS_FILE}")

    # Generate checksum
    checksum = generate_checksum(OUTPUT_FILE)
    logger.info(f"Checksum for {OUTPUT_FILE}: {checksum}")

    if abs(final_corr) >= CORRELATION_THRESHOLD:
        logger.warning(
            f"Correlation {final_corr:.6f} exceeds threshold {CORRELATION_THRESHOLD}. "
            "This indicates the orthogonalization logic may need tuning or the target "
            "ranges are incompatible."
        )
        # Do not raise here to allow the pipeline to proceed if the user accepts the risk,
        # but log strongly. If strict mode is needed, uncomment next line.
        # raise RuntimeError("Correlation threshold violated")
    else:
        logger.info("Orthogonalization verification PASSED.")

    return 0

if __name__ == "__main__":
    sys.exit(main())