"""
network_features.py
-------------------

This module implements feature extraction for misinformation cascades
based on the *pre‑cascade historical network context*.  For each cascade
we compute:

* Degree distribution moments (mean, variance, skewness)
* Average clustering coefficient
* Mean betweenness centrality

The results are written to a CSV file (default:
``data/intermediate_network_features.csv``).  All steps are logged to
``pipeline.log`` via the shared logger from ``pipeline.utils``.
"""

import argparse
import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import networkx as nx
import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger
from pipeline.utils import setup_logger

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def load_historical_networks(network_paths: List[Path]) -> Dict[str, nx.Graph]:
    """
    Load historical network graphs from JSON files.

    Each JSON file is expected to contain an ``edges`` field that is a list
    of ``[source, target]`` pairs.  The filename (without extension) is
    interpreted as the ``user_id`` whose ego‑network is stored in the
    file.

    Parameters
    ----------
    network_paths: List[Path]
        Paths to JSON files describing historical networks.

    Returns
    -------
    Dict[str, nx.Graph]
        Mapping from ``user_id`` → ``networkx.Graph``.
    """
    logger = get_logger(__name__)
    networks: Dict[str, nx.Graph] = {}
    for p in network_paths:
        try:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
            edges = data.get("edges", [])
            G = nx.Graph()
            G.add_edges_from(edges)
            user_id = p.stem  # filename without suffix
            networks[user_id] = G
            logger.debug("Loaded historical network for user_id=%s (%d edges)",
                         user_id, len(edges))
        except Exception as e:
            logger.error("Failed to load network from %s: %s", p, e)
            raise
    return networks


def compute_degree_moments(G: nx.Graph) -> Dict[str, float]:
    """
    Compute the first three moments of the degree distribution.

    Returns a dictionary with keys ``degree_mean``, ``degree_variance``,
    and ``degree_skewness``.  For an empty graph ``np.nan`` values are
    returned.
    """
    if G.number_of_nodes() == 0:
        return {
            "degree_mean": np.nan,
            "degree_variance": np.nan,
            "degree_skewness": np.nan,
        }
    degrees = np.array([d for _, d in G.degree()], dtype=float)
    mean = degrees.mean()
    var = degrees.var(ddof=0)
    # Skewness: (E[(X-μ)^3]) / σ^3
    if var == 0:
        skew = 0.0
    else:
        skew = ((degrees - mean) ** 3).mean() / (np.sqrt(var) ** 3)
    return {
        "degree_mean": mean,
        "degree_variance": var,
        "degree_skewness": skew,
    }


def compute_clustering_coefficient(G: nx.Graph) -> float:
    """
    Compute the average clustering coefficient of the graph.

    Returns ``np.nan`` for an empty graph.
    """
    if G.number_of_nodes() == 0:
        return np.nan
    return nx.average_clustering(G)


def compute_mean_betweenness(G: nx.Graph) -> float:
    """
    Compute the mean betweenness centrality over all nodes.

    Returns ``np.nan`` for an empty graph.
    """
    if G.number_of_nodes() == 0:
        return np.nan
    betweenness = nx.betweenness_centrality(G, normalized=True, endpoints=False)
    return float(np.mean(list(betweenness.values())))


def extract_cascade_nodes(cascade_path: Path) -> Dict[str, List[str]]:
    """
    Extract node identifiers and associated user identifiers from a cascade
    JSON file.

    The expected schema (validated elsewhere) contains a top‑level
    ``nodes`` list where each element has at least ``node_id`` and
    ``user_id`` fields.

    Returns
    -------
    Dict[str, List[str]]
        ``{'node_ids': [...], 'user_ids': [...]}``
    """
    with cascade_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    node_ids = [n.get("node_id") for n in nodes if "node_id" in n]
    user_ids = [n.get("user_id") for n in nodes if "user_id" in n]

    return {"node_ids": node_ids, "user_ids": user_ids}


def _union_graphs(graphs: List[nx.Graph]) -> nx.Graph:
    """
    Return a new graph that is the union of the supplied graphs.
    """
    union = nx.Graph()
    for g in graphs:
        union.add_nodes_from(g.nodes(data=True))
        union.add_edges_from(g.edges(data=True))
    return union


def process_cascades(
    cascade_paths: List[Path],
    network_paths: List[Path],
    output_path: Path,
    logger: logging.Logger,
) -> None:
    """
    Process a collection of cascades and compute network‑level features
    based on the pre‑cascade historical network context.

    Parameters
    ----------
    cascade_paths: List[Path]
        Paths to cascade JSON files.
    network_paths: List[Path]
        Paths to historical network JSON files.
    output_path: Path
        Destination CSV file for the feature table.
    logger: logging.Logger
        Logger instance for progress reporting.
    """
    logger.info("Loading historical networks (%d files)", len(network_paths))
    historical_networks = load_historical_networks(network_paths)

    records = []

    for cascade_path in cascade_paths:
        cascade_id = cascade_path.stem
        logger.info("Processing cascade %s", cascade_id)

        cascade_info = extract_cascade_nodes(cascade_path)
        user_ids = cascade_info["user_ids"]

        # Gather graphs for all users appearing in the cascade.
        graphs = [
            historical_networks[uid]
            for uid in user_ids
            if uid in historical_networks
        ]

        if not graphs:
            logger.warning(
                "No historical network found for any user in cascade %s; "
                "features will be NaN.",
                cascade_id,
            )
            combined = nx.Graph()
        else:
            combined = _union_graphs(graphs)

        degree_stats = compute_degree_moments(combined)
        clustering = compute_clustering_coefficient(combined)
        betweenness = compute_mean_betweenness(combined)

        record = {
            "cascade_id": cascade_id,
            "degree_mean": degree_stats["degree_mean"],
            "degree_variance": degree_stats["degree_variance"],
            "degree_skewness": degree_stats["degree_skewness"],
            "clustering_coeff": clustering,
            "betweenness_mean": betweenness,
        }
        records.append(record)

    df = pd.DataFrame.from_records(records)
    logger.info("Writing %d feature rows to %s", len(df), output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info("Feature extraction completed successfully.")


def main() -> int:
    """
    CLI entry point.

    Example
    -------
    .. code-block:: bash

        python -m pipeline.network_features \\
            --cascades-dir data/node_limit_fixtures \\
            --networks-dir data/historical_networks \\
            --output data/intermediate_network_features.csv
    """
    parser = argparse.ArgumentParser(
        description="Extract pre‑cascade network features for each cascade."
    )
    parser.add_argument(
        "--cascades-dir",
        type=str,
        required=True,
        help="Directory containing cascade JSON files.",
    )
    parser.add_argument(
        "--networks-dir",
        type=str,
        required=True,
        help="Directory containing historical network JSON files.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(paths.data("intermediate_network_features.csv")),
        help="Path to write the output CSV (default: data/intermediate_network_features.csv).",
    )
    args = parser.parse_args()

    # Initialise logger
    logger = setup_logger(__name__, log_file=str(paths.logs("pipeline.log")))
    logger.info("Starting network feature extraction")
    logger.debug("Arguments: %s", args)

    cascade_dir = Path(args.cascades_dir)
    network_dir = Path(args.networks_dir)
    output_path = Path(args.output)

    cascade_paths = sorted(cascade_dir.glob("*.json"))
    network_paths = sorted(network_dir.glob("*.json"))

    if not cascade_paths:
        logger.error("No cascade JSON files found in %s", cascade_dir)
        return 1
    if not network_paths:
        logger.error("No historical network JSON files found in %s", network_dir)
        return 1

    try:
        process_cascades(cascade_paths, network_paths, output_path, logger)
    except Exception as exc:
        logger.exception("Feature extraction failed: %s", exc)
        return 1

    logger.info("Network feature extraction finished")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())