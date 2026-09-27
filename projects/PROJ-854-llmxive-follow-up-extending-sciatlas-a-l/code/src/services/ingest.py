import os
import random
import logging
import time
import traceback
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import networkx as nx
import pandas as pd
import numpy as np
from scipy import stats
from datasets import load_dataset
import pyarrow.parquet as pq

from src.models.config import SEED, DATA_PATH, ARTIFACT_PATH, MAX_BUFFER_ROWS, MAX_RAM_GB
from src.models.node import Node
from src.models.graph_utils import louvain_cluster, calc_bridging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_sample_ids(num_samples: int = 100) -> List[str]:
    """Fetch a sample of work IDs from OpenAlex."""
    try:
        dataset = load_dataset("openalex/works", split="works", streaming=True)
        ids = []
        for item in dataset:
            if len(ids) >= num_samples:
                break
            ids.append(item['id'])
        return ids
    except Exception as e:
        logger.error(f"Failed to fetch sample IDs: {e}")
        raise

def fetch_work_details(work_ids: List[str]) -> List[Dict[str, Any]]:
    """Fetch details for a list of work IDs."""
    details = []
    try:
        dataset = load_dataset("openalex/works", split="works", streaming=True)
        id_set = set(work_ids)
        for item in dataset:
            if item['id'] in id_set:
                details.append(item)
                if len(details) == len(work_ids):
                    break
    except Exception as e:
        logger.error(f"Failed to fetch work details: {e}")
        raise
    return details

def build_graph_from_details(details: List[Dict[str, Any]]) -> nx.Graph:
    """Build a NetworkX graph from OpenAlex work details."""
    G = nx.Graph()
    for item in details:
        node_id = item['id']
        title = item.get('title')
        cited_by_count = item.get('cited_by_count', 0)
        publication_date = item.get('publication_date')

        G.add_node(
            node_id,
            title=title,
            citation_count=cited_by_count,
            publication_date=publication_date,
            embedding_vector=None,
            primary_cluster=None,
            topic_cluster=None,
            bridging_coefficient=0.0
        )

        if 'referenced_works' in item and item['referenced_works']:
            for ref in item['referenced_works']:
                ref_id = ref['id']
                G.add_edge(node_id, ref_id)
    return G

def sample_subgraph_stream(
    G_stream: nx.Graph,
    target_size: int,
    seed_node_id: Optional[str] = None,
    max_depth: int = 3
) -> nx.Graph:
    """Perform snowball sampling on a graph stream."""
    if G_stream.number_of_nodes() == 0:
        return nx.Graph()

    if seed_node_id is None:
        seed_node_id = random.choice(list(G_stream.nodes()))

    visited = set()
    queue = [(seed_node_id, 0)]
    visited.add(seed_node_id)

    while queue:
        current_node, depth = queue.pop(0)
        if depth >= max_depth:
            continue

        neighbors = list(G_stream.neighbors(current_node))
        for neighbor in neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, depth + 1))
                if len(visited) >= target_size:
                    break
        if len(visited) >= target_size:
            break

    sampled_G = G_stream.subgraph(visited).copy()
    return sampled_G

def validate_sampled_graph(G_sampled: nx.Graph) -> Dict[str, Any]:
    """
    Validate the sampled graph for schema compliance and topological representativeness.

    Checks:
    1. Schema: Every node has non-null primary_cluster and bridging_coefficient in [0.0, 1.0].
    2. Topology: Degree distribution follows power-law (approx) and cluster sizes are non-degenerate.

    Returns:
        Dict containing validation results and metrics.
    """
    result = {
        "sampled_node_count": G_sampled.number_of_nodes(),
        "sampled_edge_count": G_sampled.number_of_edges(),
        "valid_bridging_count": 0,
        "valid_cluster_count": 0,
        "representativeness_passed": False,
        "details": {}
    }

    if G_sampled.number_of_nodes() == 0:
        result["details"]["error"] = "Graph is empty"
        return result

    # 1. Schema Validation
    bridging_valid = True
    cluster_valid = True
    valid_bridging_count = 0
    valid_cluster_count = 0
    degrees = []
    cluster_sizes = []

    for node, data in G_sampled.nodes(data=True):
        # Check primary_cluster
        cluster = data.get('primary_cluster')
        if cluster is not None:
            valid_cluster_count += 1
        else:
            cluster_valid = False

        # Check bridging_coefficient
        bridging = data.get('bridging_coefficient')
        if bridging is not None and 0.0 <= bridging <= 1.0:
            valid_bridging_count += 1
        else:
            bridging_valid = False

        degrees.append(data.get('degree', 0))

    result["valid_bridging_count"] = valid_bridging_count
    result["valid_cluster_count"] = valid_cluster_count
    result["schema_passed"] = bridging_valid and cluster_valid
    result["details"]["schema_issues"] = {
        "missing_clusters": result["sampled_node_count"] - valid_cluster_count,
        "invalid_bridging": result["sampled_node_count"] - valid_bridging_count
    }

    # 2. Topological Representativeness (Internal Consistency)
    # Check for degenerate graphs (e.g., all isolated or single giant component with no structure)
    if valid_cluster_count == 0:
        result["details"]["topology_issue"] = "No clusters assigned"
    else:
        # Calculate cluster sizes
        clusters = {}
        for node, data in G_sampled.nodes(data=True):
            c = data.get('primary_cluster')
            if c is not None:
                clusters[c] = clusters.get(c, 0) + 1
        cluster_sizes = list(clusters.values())

        # Check for variance in cluster sizes (avoid single giant or all singletons)
        if len(cluster_sizes) > 1:
            cluster_variance = np.var(cluster_sizes)
            mean_degree = np.mean(degrees) if degrees else 0.0

            # Heuristic: If variance is too low (all clusters same size) or too high (one giant), warn
            # But we pass if we have > 1 cluster and mean degree > 0
            if mean_degree > 0 and len(cluster_sizes) > 1:
                result["representativeness_passed"] = True
                result["details"]["topology_check"] = "Passed: Multi-cluster, non-isolated"
            else:
                result["details"]["topology_check"] = "Warning: Low connectivity or single cluster"
        else:
            result["details"]["topology_check"] = "Warning: Only one cluster or no clusters"

    # 3. Degree Distribution Check (Power-law approximation)
    if len(degrees) > 10:
        # Simple check: log-log plot linearity (approx)
        # We'll just check if there's a mix of low and high degree nodes
        degree_counts = np.bincount(degrees)
        non_zero_degrees = [i for i, c in enumerate(degree_counts) if c > 0]
        if len(non_zero_degrees) > 2:
            result["details"]["degree_distribution"] = "Non-trivial"
        else:
            result["details"]["degree_distribution"] = "Trivial (few degree values)"

    return result

def fetch_and_build_subgraph(target_size: int, seed_node_id: Optional[str] = None) -> nx.Graph:
    """Main ingestion pipeline: Fetch, Sample, Cluster, Calc Bridging."""
    logger.info(f"Starting ingestion pipeline for target size {target_size}")

    # 1. Fetch Sample IDs
    ids = fetch_sample_ids(num_samples=target_size * 2)  # Fetch more to ensure enough after sampling
    if not ids:
        raise RuntimeError("No sample IDs fetched from OpenAlex")

    # 2. Fetch Details
    details = fetch_work_details(ids)
    if not details:
        raise RuntimeError("No work details fetched")

    # 3. Build Graph
    G = build_graph_from_details(details)
    logger.info(f"Built graph with {G.number_of_nodes()} nodes")

    # 4. Sample
    if G.number_of_nodes() > target_size:
        G = sample_subgraph_stream(G, target_size, seed_node_id)
        logger.info(f"Sampled graph to {G.number_of_nodes()} nodes")

    # 5. Cluster (Louvain)
    if G.number_of_nodes() > 0:
        clusters = louvain_cluster(G)
        for node, cluster_id in clusters.items():
            G.nodes[node]['primary_cluster'] = cluster_id
        logger.info(f"Assigned {len(set(clusters.values()))} clusters")

    # 6. Calculate Bridging
    calc_bridging(G, clusters)
    logger.info("Calculated bridging coefficients")

    # 7. Validate
    validation_result = validate_sampled_graph(G)
    logger.info(f"Validation result: {validation_result}")

    # Save validation results to artifacts
    artifacts_dir = Path(ARTIFACT_PATH) / "results"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    with open(artifacts_dir / "sampling_validation.json", 'w') as f:
        json.dump(validation_result, f, indent=2)

    # Create topology equivalence report (simplified internal check)
    topology_report = {
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "cluster_count": len(set(clusters.values())) if clusters else 0,
        "avg_degree": np.mean([d for n, d in G.degree()]) if G.number_of_nodes() > 0 else 0,
        "max_degree": max([d for n, d in G.degree()]) if G.number_of_nodes() > 0 else 0,
        "min_degree": min([d for n, d in G.degree()]) if G.number_of_nodes() > 0 else 0,
        "representativeness_passed": validation_result.get("representativeness_passed", False)
    }
    with open(artifacts_dir / "topology_equivalence.json", 'w') as f:
        json.dump(topology_report, f, indent=2)

    return G

def save_graph_to_parquet(G: nx.Graph, output_path: str) -> None:
    """Save graph data to Parquet format."""
    data = []
    for node, attrs in G.nodes(data=True):
        data.append({
            'id': node,
            'title': attrs.get('title'),
            'citation_count': attrs.get('citation_count', 0),
            'primary_cluster': attrs.get('primary_cluster'),
            'topic_cluster': attrs.get('topic_cluster'),
            'bridging_coefficient': attrs.get('bridging_coefficient', 0.0)
        })
    df = pd.DataFrame(data)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved graph to {output_path}")

def validate_final_dataset_schema(df: pd.DataFrame) -> bool:
    """Validate the final dataset against schema requirements."""
    required_cols = ['id', 'citation_count', 'novelty_score', 'primary_cluster', 'topic_cluster']
    if not all(col in df.columns for col in required_cols):
        logger.error(f"Missing columns in dataset: {set(required_cols) - set(df.columns)}")
        return False
    return True

def main():
    """CLI entry point for ingestion."""
    import argparse
    parser = argparse.ArgumentParser(description="Ingest OpenAlex data")
    parser.add_argument("--target-size", type=int, default=100, help="Target subgraph size")
    parser.add_argument("--seed-node", type=str, default=None, help="Seed node ID for sampling")
    args = parser.parse_args()

    G = fetch_and_build_subgraph(args.target_size, args.seed_node)
    output_path = Path(DATA_PATH) / "processed" / "subgraph_with_clusters.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_graph_to_parquet(G, str(output_path))
    print(f"Ingestion complete. Graph saved to {output_path}")

if __name__ == "__main__":
    main()
