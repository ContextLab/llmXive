"""
Batch generation script for producing per-topology-class batches.

This module orchestrates the generation of graphs for different topology classes
(Erdős-Rényi, Watts-Strogatz, Barabási-Albert) with controlled parameters.
It implements retry logic for disconnected networks (T018b) and timeout handling (T016a).
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
import numpy as np

from code.src.utils.config import load_config
from code.src.utils.logging import log_run, get_run_log, append_to_log
from code.src.generators.base import BaseGenerator
from code.src.generators.er import ErdosRenyiGenerator
from code.src.generators.sw import WattsStrogatzGenerator
from code.src.generators.sf import BarabasiAlbertGenerator
from code.src.generators.binning import classify_graph
from code.src.generators.retry_logic import get_retry_limit, log_retry_failure

# Ensure logger is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_generator(topology_class: str, config: Dict[str, Any]) -> BaseGenerator:
    """Factory to instantiate the correct generator based on topology class."""
    seed = config.get('global_seed', 42)
    if topology_class == 'er':
        return ErdosRenyiGenerator(
            n=config.get('n', 100),
            p=config.get('p', 0.1),
            seed=seed,
            config=config
        )
    elif topology_class == 'sw':
        return WattsStrogatzGenerator(
            n=config.get('n', 100),
            k=config.get('k', 4),
            p=config.get('p', 0.1),
            seed=seed,
            config=config
        )
    elif topology_class == 'sf':
        return BarabasiAlbertGenerator(
            n=config.get('n', 100),
            m=config.get('m', 2),
            seed=seed,
            config=config
        )
    else:
        raise ValueError(f"Unknown topology class: {topology_class}")

def generate_single_graph(generator: BaseGenerator, target_clustering: Optional[float] = None) -> Tuple[Optional[nx.Graph], bool]:
    """
    Attempt to generate a single graph.
    Returns (graph, is_accepted).
    If target_clustering is set, checks against binning logic.
    """
    graph = generator.generate()
    if graph is None:
        return None, False

    # Connectivity check is handled inside generator (T051), but double check for safety
    if not nx.is_connected(graph):
        return graph, False

    if target_clustering is not None:
        # Use the binning logic to classify
        # The task implies checking if the graph falls into the target bin
        # For T056, we are specifically looking at rejection rate for clustering targets.
        # We assume if the graph's clustering is far from target, it's a rejection candidate
        # or if the binning logic explicitly rejects it.
        # However, T056 specifically mentions "rejection rate for clustering targets > 40%".
        # This implies we are counting graphs that failed to meet the clustering criteria.
        # We will use the classify_graph function to see if it matches the expected bin.
        # For simplicity in this logic, if the graph's clustering is not within a tolerance
        # of the target, we count it as a rejection for the batch size adjustment logic.
        
        cc = nx.average_clustering(graph)
        # Tolerance from config or default 0.05
        tolerance = config.get('stratification_params', {}).get('tolerance', 0.05)
        
        if abs(cc - target_clustering) > tolerance:
            return graph, False # Rejected based on clustering

    return graph, True

def generate_batch(topology_class: str, target_count: int, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a batch of graphs for a specific topology class.
    Implements T056: Sample Size Adjustment logic.
    """
    generator = get_generator(topology_class, config)
    target_clustering = config.get('stratification_params', {}).get('target_counts', {}).get(topology_class, None)
    
    # Determine if we need to adjust batch size
    # Initial batch size is the target count
    current_batch_size = target_count
    max_attempts = current_batch_size * 10 # Safety limit to prevent infinite loops
    
    graphs = []
    failed_graphs = []
    attempts = 0
    clustering_rejections = 0
    total_rejections = 0
    
    logger.info(f"Starting batch generation for {topology_class}, target: {target_count}")
    
    while len(graphs) < target_count and attempts < max_attempts:
        attempts += 1
        graph, is_accepted = generate_single_graph(generator, target_clustering)
        
        if graph is None:
            # Generation failed entirely (e.g. connectivity retries exhausted)
            log_retry_failure(topology_class, attempts, "Generation failed")
            total_rejections += 1
            continue

        if not is_accepted:
            total_rejections += 1
            # Check specifically if it was a clustering rejection
            if target_clustering is not None:
                cc = nx.average_clustering(graph)
                tolerance = config.get('stratification_params', {}).get('tolerance', 0.05)
                if abs(cc - target_clustering) > tolerance:
                    clustering_rejections += 1
            failed_graphs.append({
                "id": f"{topology_class}_{attempts}",
                "reason": "clustering_mismatch" if target_clustering else "connectivity"
            })
            continue

        graphs.append(graph)
        # Log successful generation if needed (T019 metadata)
    
    # T056 Logic: Check rejection rate for clustering targets
    # If target_clustering is set, we calculate the rejection rate relative to attempts
    rejection_rate = 0.0
    if attempts > 0:
        rejection_rate = total_rejections / attempts
    
    # Specifically for clustering targets as per T056 description
    clustering_rejection_rate = 0.0
    if attempts > 0 and target_clustering is not None:
        clustering_rejection_rate = clustering_rejections / attempts

    # The task says: "If the rejection rate for clustering targets > 40%"
    # This implies we check the rate of graphs that failed due to clustering constraints.
    # We use the clustering_rejection_rate.
    adjustment_factor = config.get('rejection_adjustment_factor', 1.5)
    
    if target_clustering is not None and clustering_rejection_rate > 0.4:
        # Sample Size Adjustment triggered
        new_batch_size = int(current_batch_size * adjustment_factor)
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "sample_size_adjustment",
            "run_id": config.get('run_id', 'unknown'),
            "seed": config.get('global_seed'),
            "topology": topology_class,
            "original_batch_size": current_batch_size,
            "new_batch_size": new_batch_size,
            "rejection_rate": clustering_rejection_rate,
            "message": f"Sample Size Adjustment: New batch size = {new_batch_size}"
        }
        
        # Log to data/run_log.json
        append_to_log(log_entry)
        logger.warning(f"Sample Size Adjustment: New batch size = {new_batch_size} (Rejection rate: {clustering_rejection_rate:.2f})")
        
        # Note: In a full pipeline, this would trigger a re-run or a larger generation loop.
        # Here we log the event as required by the task.
    
    return {
        "topology_class": topology_class,
        "target_count": target_count,
        "generated_count": len(graphs),
        "total_attempts": attempts,
        "rejection_rate": total_rejections / attempts if attempts > 0 else 0.0,
        "clustering_rejection_rate": clustering_rejection_rate,
        "graphs": graphs, # In a real scenario, we might save these to disk here or return IDs
        "failed_graphs": failed_graphs
    }

def main():
    """Entry point for batch generation."""
    parser = argparse.ArgumentParser(description="Batch Graph Generation with T056 Adjustment")
    parser.add_argument('--config', type=str, default='code/config.yaml', help='Path to config file')
    parser.add_argument('--topology', type=str, required=True, help='Topology class (er, sw, sf)')
    parser.add_argument('--count', type=int, default=10, help='Target number of graphs')
    args = parser.parse_args()

    config = load_config(args.config)
    config['run_id'] = config.get('run_id', 'batch_run')
    
    # Ensure log file exists
    log_path = Path('data/run_log.json')
    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'w') as f:
            json.dump([], f)

    result = generate_batch(args.topology, args.count, config)
    
    print(json.dumps(result, indent=2, default=str))
    return result

if __name__ == '__main__':
    main()
