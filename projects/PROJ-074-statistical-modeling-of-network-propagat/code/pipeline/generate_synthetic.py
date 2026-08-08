"""
generate_synthetic.py

Generates a small benchmark dataset for testing the misinformation cascade pipeline.

This script synthesizes a dataset containing:
- cascade_id, node_id, timestamp, cascade_label
- historical_degree, historical_shares
- user_id, message_id, platform_id

The dataset is designed to be 'small' (≤50 cascades, ≤2,000 nodes each)
and includes the susceptibility score calculated using the formula:
(historical_degree >= 2 AND historical_shares >= 1) ? 1.0 : 0.0

Output:
- data/raw/synthetic_cascades.json (JSON edge-list format)
- data/raw/synthetic_features.csv (aggregated features)

Note: This is a synthetic dataset strictly for testing the pipeline's
schema validation, feature engineering, and model fitting stages.
"""

import json
import logging
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.utils import set_global_seed, setup_logger

# Constants
RANDOM_SEED = 12345
MAX_CASCADES = 50
MAX_NODES_PER_CASCADE = 2000
OUTPUT_DIR = Path("data/raw")
OUTPUT_JSON = OUTPUT_DIR / "synthetic_cascades.json"
OUTPUT_CSV = OUTPUT_DIR / "synthetic_features.csv"

# Platform IDs for diversity
PLATFORMS = ["twitter", "facebook", "reddit"]

logger = logging.getLogger(__name__)


def generate_cascade_nodes(cascade_id: int, num_nodes: int, base_time: datetime) -> list:
    """
    Generate a list of nodes for a single cascade.

    Each node includes:
    - node_id: unique identifier
    - timestamp: propagation time (relative to base_time)
    - cascade_id: the cascade this node belongs to
    - user_id: synthetic user ID
    - message_id: synthetic message ID
    - platform_id: synthetic platform ID
    - historical_degree: synthetic historical degree
    - historical_shares: synthetic historical share count
    - cascade_label: binary label (0 or 1) for cascade size (small/large)
    """
    nodes = []
    users = [f"user_{random.randint(1000, 9999)}" for _ in range(num_nodes)]
    messages = [f"msg_{random.randint(10000, 99999)}" for _ in range(num_nodes)]
    platforms = [random.choice(PLATFORMS) for _ in range(num_nodes)]

    # Generate historical metrics
    # historical_degree: 0-10 (mostly low, some high)
    historical_degrees = np.random.exponential(scale=2.0, size=num_nodes).astype(int)
    historical_degrees = np.clip(historical_degrees, 0, 20)

    # historical_shares: 0-50 (mostly low, some high)
    historical_shares = np.random.exponential(scale=5.0, size=num_nodes).astype(int)
    historical_shares = np.clip(historical_shares, 0, 100)

    # Determine cascade label based on total size
    # If cascade has > 100 nodes, label as 1 (large), else 0 (small)
    cascade_label = 1 if num_nodes > 100 else 0

    for i in range(num_nodes):
        # Timestamp: exponential distribution for cascade propagation
        time_offset = timedelta(seconds=random.expovariate(0.1))
        timestamp = base_time + time_offset

        node = {
            "node_id": f"node_{cascade_id}_{i}",
            "timestamp": timestamp.isoformat(),
            "cascade_id": f"cascade_{cascade_id}",
            "user_id": users[i],
            "message_id": messages[i],
            "platform_id": platforms[i],
            "historical_degree": int(historical_degrees[i]),
            "historical_shares": int(historical_shares[i]),
            "cascade_label": cascade_label,
        }
        nodes.append(node)

    return nodes


def compute_susceptibility(historical_degree: int, historical_shares: int) -> float:
    """
    Compute susceptibility score using the formula:
    (historical_degree >= 2 AND historical_shares >= 1) ? 1.0 : 0.0
    """
    if historical_degree >= 2 and historical_shares >= 1:
        return 1.0
    return 0.0


def main():
    """
    Main function to generate synthetic benchmark dataset.
    """
    set_global_seed(RANDOM_SEED)
    logger = setup_logger("generate_synthetic")
    logger.info(f"Starting synthetic dataset generation with seed {RANDOM_SEED}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_nodes = []
    feature_rows = []

    base_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    # Generate cascades
    num_cascades = random.randint(30, MAX_CASCADES)
    logger.info(f"Generating {num_cascades} cascades")

    for cascade_id in range(num_cascades):
        # Random number of nodes (1 to MAX_NODES_PER_CASCADE)
        num_nodes = random.randint(10, MAX_NODES_PER_CASCADE)
        logger.debug(f"Generating cascade_{cascade_id} with {num_nodes} nodes")

        nodes = generate_cascade_nodes(cascade_id, num_nodes, base_time)
        all_nodes.extend(nodes)

        # Aggregate features for this cascade
        cascade_data = nodes[0]  # All nodes in a cascade share the same cascade_id
        avg_degree = np.mean([n["historical_degree"] for n in nodes])
        avg_shares = np.mean([n["historical_shares"] for n in nodes])
        max_degree = max([n["historical_degree"] for n in nodes])
        max_shares = max([n["historical_shares"] for n in nodes])

        # Compute susceptibility for the cascade (average of node susceptibilities)
        susceptibilities = [
            compute_susceptibility(n["historical_degree"], n["historical_shares"])
            for n in nodes
        ]
        avg_susceptibility = np.mean(susceptibilities)

        feature_rows.append({
            "cascade_id": cascade_data["cascade_id"],
            "node_count": num_nodes,
            "avg_historical_degree": avg_degree,
            "avg_historical_shares": avg_shares,
            "max_historical_degree": max_degree,
            "max_historical_shares": max_shares,
            "avg_susceptibility": avg_susceptibility,
            "platform": cascade_data["platform_id"],
            "cascade_label": cascade_data["cascade_label"],
        })

    # Write JSON edge-list format
    logger.info(f"Writing {len(all_nodes)} nodes to {OUTPUT_JSON}")
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_nodes, f, indent=2)

    # Write aggregated features CSV
    logger.info(f"Writing {len(feature_rows)} feature rows to {OUTPUT_CSV}")
    df_features = pd.DataFrame(feature_rows)
    df_features.to_csv(OUTPUT_CSV, index=False)

    logger.info("Synthetic dataset generation complete")
    logger.info(f"Output JSON: {OUTPUT_JSON}")
    logger.info(f"Output CSV: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()