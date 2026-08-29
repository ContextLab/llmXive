"""
Batch Runner for Network Topology Generation.

Orchestrates the generation of synthetic spin network datasets across different
topology classes (Erdős-Rényi, Watts-Strogatz, Barabási-Albert), enforcing
connectivity constraints, retry logic, and global success rate monitoring.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

# Import from local project structure
from code.src.utils.config import load_config, get_global_config
from code.src.utils.logging import log_metric, init_logging
from code.src.generators.base import BaseGenerator
from code.src.generators.er import ErdosRenyiGenerator
from code.src.generators.sw import WattsStrogatzGenerator
from code.src.generators.sf import BarabasiAlbertGenerator
from code.src.generators.metrics import compute_graph_metrics
from code.src.generators.metadata import save_graph_metadata
from code.src.generators.binning import classify_graph_bin
from code.src.generators.quota_checker import check_quota_status, update_quota
from code.src.generators.manifest_updater import update_manifest

# Constants
DEFAULT_MAX_RETRIES = 10
DEFAULT_SUCCESS_RATE_THRESHOLD = 0.95
LOG_FILE_PATH = "data/run_log.json"
MANIFEST_PATH = "data/raw/global_batch_manifest.json"

logger = logging.getLogger(__name__)


class BatchGenerationError(Exception):
    """Custom exception for batch generation failures."""
    pass


class GlobalSuccessRateMonitor:
    """
    Monitors the global success rate of graph generation across the entire batch.
    Enforces the requirement that >=95% of graphs must be valid connected graphs
    within the configured retry limit.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.thresholds = config.get("thresholds", {})
        self.success_rate_min = self.thresholds.get(
            "success_rate_min", DEFAULT_SUCCESS_RATE_THRESHOLD
        )
        self.max_attempts = self.config.get("simulation_params", {}).get(
            "max_generation_attempts", DEFAULT_MAX_RETRIES
        )

        self.total_attempts = 0
        self.total_successes = 0
        self.total_failures = 0
        self.failed_graphs: List[Dict[str, Any]] = []
        self.successful_graphs: List[Dict[str, Any]] = []

    def record_attempt(self, graph_id: str, success: bool, graph: Optional[nx.Graph] = None):
        """Record a generation attempt result."""
        self.total_attempts += 1
        if success:
            self.total_successes += 1
            if graph:
                self.successful_graphs.append({
                    "graph_id": graph_id,
                    "node_count": graph.number_of_nodes(),
                    "edge_count": graph.number_of_edges(),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        else:
            self.total_failures += 1
            self.failed_graphs.append({
                "graph_id": graph_id,
                "attempts": self.max_attempts,
                "reason": "Max retries exceeded (disconnected)",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

    def get_current_success_rate(self) -> float:
        """Calculate current success rate."""
        if self.total_attempts == 0:
            return 1.0
        return self.total_successes / self.total_attempts

    def check_threshold(self) -> Tuple[bool, str]:
        """
        Check if the current success rate meets the minimum threshold.
        Returns (is_valid, message).
        """
        rate = self.get_current_success_rate()
        if rate < self.success_rate_min:
            msg = (
                f"CRITICAL: Global success rate {rate:.2%} is below threshold "
                f"{self.success_rate_min:.2%}. "
                f"Total attempts: {self.total_attempts}, Successes: {self.total_successes}, "
                f"Failures: {self.total_failures}. "
                f"Failed graphs: {[g['graph_id'] for g in self.failed_graphs]}"
            )
            return False, msg
        return True, "Success rate within acceptable limits."

    def log_final_metrics(self):
        """Log final success rate metrics to the run log."""
        rate = self.get_current_success_rate()
        log_metric({
            "event_type": "generation_summary",
            "run_id": "batch_generation",
            "seed": self.config.get("global_seed", 42),
            "status": "completed" if rate >= self.success_rate_min else "critical_error",
            "duration_seconds": 0.0, # Duration tracked per graph, summary is instantaneous
            "metrics": {
                "total_attempts": self.total_attempts,
                "total_successes": self.total_successes,
                "total_failures": self.total_failures,
                "success_rate": rate,
                "threshold": self.success_rate_min
            }
        })


def generate_single_graph(
    generator_class: type,
    graph_id: str,
    params: Dict[str, Any],
    max_retries: int
) -> Tuple[Optional[nx.Graph], bool, int]:
    """
    Attempt to generate a single connected graph using the specified generator.
    Returns (graph, success, attempts_used).
    """
    generator = generator_class()
    attempts = 0
    graph = None
    success = False

    for attempt in range(1, max_retries + 1):
        attempts += 1
        try:
            graph = generator.generate(params)
            if nx.is_connected(graph):
                success = True
                break
            else:
                logger.warning(f"Graph {graph_id} attempt {attempt}: Disconnected. Retrying...")
        except Exception as e:
            logger.warning(f"Graph {graph_id} attempt {attempt} failed with error: {e}. Retrying...")
            graph = None

    return graph, success, attempts


def run_batch_generation(config_path: Optional[str] = None):
    """
    Main orchestration logic for batch generation.
    1. Loads config.
    2. Iterates over topology classes.
    3. Generates graphs with retry logic.
    4. Tracks global success rate.
    5. Fails if global success rate < threshold.
    6. Writes manifest and logs metrics.
    """
    # Initialize logging
    init_logging()
    logger.info("Starting batch generation pipeline.")

    # Load configuration
    if config_path:
        config = load_config(config_path)
    else:
        config = load_config()

    # Initialize Monitor
    monitor = GlobalSuccessRateMonitor(config)

    # Define topology classes and their generators/params
    # This structure can be extended based on config.yaml topology_targets
    topology_classes = [
        {
            "name": "erdos_renyi",
            "generator": ErdosRenyiGenerator,
            "params": {"n": 30, "p": 0.1}
        },
        {
            "name": "watts_strogatz",
            "generator": WattsStrogatzGenerator,
            "params": {"n": 30, "k": 4, "p": 0.3}
        },
        {
            "name": "barabasi_albert",
            "generator": BarabasiAlbertGenerator,
            "params": {"n": 30, "m": 2}
        }
    ]

    # Override with config if specified
    if "topology_targets" in config:
        topology_classes = config["topology_targets"]

    all_generated_graphs = []
    max_attempts = config.get("simulation_params", {}).get("max_generation_attempts", DEFAULT_MAX_RETRIES)

    logger.info(f"Generating graphs with max attempts: {max_attempts}")

    # Iterate over topology classes
    for topo in topology_classes:
        name = topo["name"]
        gen_class = topo["generator"]
        params = topo.get("params", {})
        count = topo.get("count", 1)

        logger.info(f"Processing {count} graphs for topology: {name}")

        for i in range(count):
            graph_id = f"{name}_{i+1}"
            start_time = time.time()

            graph, success, attempts_used = generate_single_graph(
                gen_class, graph_id, params, max_attempts
            )

            duration = time.time() - start_time

            # Record in monitor
            monitor.record_attempt(graph_id, success, graph)

            if success:
                # Compute metrics
                metrics = compute_graph_metrics(graph)
                
                # Save metadata
                save_graph_metadata(graph_id, {
                    "algorithm": name,
                    "params": params,
                    "seed": config.get("global_seed"),
                    "metrics": metrics,
                    "attempts": attempts_used,
                    "duration_seconds": duration
                })

                # Add to batch list
                all_generated_graphs.append({
                    "graph_id": graph_id,
                    "topology": name,
                    "metrics": metrics,
                    "params": params,
                    "success": True
                })

                # Update quota/binning if applicable
                bin_name = classify_graph_bin(metrics.get("clustering_coefficient", 0.0), config)
                update_quota(bin_name, config)
                
                # Log graph generated event
                log_metric({
                    "event_type": "graph_generated",
                    "run_id": "batch_generation",
                    "seed": config.get("global_seed"),
                    "status": "success",
                    "duration_seconds": duration,
                    "graph_id": graph_id,
                    "topology": name
                })
            else:
                logger.error(f"Failed to generate valid connected graph for {graph_id} after {attempts_used} attempts.")
                # Log failure
                log_metric({
                    "event_type": "graph_generated",
                    "run_id": "batch_generation",
                    "seed": config.get("global_seed"),
                    "status": "failed",
                    "duration_seconds": duration,
                    "graph_id": graph_id,
                    "topology": name,
                    "reason": "Max retries exceeded"
                })

    # Final Success Rate Check
    is_valid, message = monitor.check_threshold()
    monitor.log_final_metrics()

    if not is_valid:
        logger.critical(message)
        raise BatchGenerationError(message)

    logger.info(message)

    # Write Manifest
    manifest = {
        "batch_id": "batch_001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config_snapshot": config,
        "total_graphs": len(all_generated_graphs),
        "success_rate": monitor.get_current_success_rate(),
        "graphs": all_generated_graphs
    }

    manifest_path = Path(MANIFEST_PATH)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Manifest written to {MANIFEST_PATH}")

    return manifest


def main():
    """Entry point for the batch runner script."""
    import argparse

    parser = argparse.ArgumentParser(description="Run batch generation of network topologies.")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file.")
    args = parser.parse_args()

    try:
        run_batch_generation(args.config)
        logger.info("Batch generation completed successfully.")
    except BatchGenerationError as e:
        logger.error(f"Batch generation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during batch generation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
