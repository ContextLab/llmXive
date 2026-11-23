import json
import logging
import time
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

from code.src.utils.config import load_config, set_seed
from code.src.utils.logging import log_metric, log_run, init_logging
from code.src.generators.base import BaseGenerator
from code.src.generators.er import ErdosRenyiGenerator
from code.src.generators.sw import WattsStrogatzGenerator
from code.src.generators.sf import BarabasiAlbertGenerator
from code.src.generators.metrics import extract_metrics
from code.src.generators.binning import classify_graph
from code.src.generators.quota_checker import check_quota_status

# Constants
MANIFEST_PATH = Path("data/raw/global_batch_manifest.json")
LOG_FILE_PATH = Path("data/run_log.json")
BATCH_SIZE_DEFAULT = 10

class GlobalSuccessRateMonitor:
    """
    Tracks failed attempts per graph and global success rate.
    Enforces the "≥95% valid connected graphs within 10 attempts" edge case logic.
    """

    def __init__(self, min_success_rate: float = 0.95, max_attempts: int = 10):
        self.min_success_rate = min_success_rate
        self.max_attempts = max_attempts
        self.total_generated = 0
        self.total_valid = 0
        self.failed_attempts_per_graph: Dict[str, int] = {}
        self.graph_successes: Dict[str, int] = {}
        self.batch_failed = False
        self.critical_error_message = ""

    def record_attempt(self, graph_id: str, success: bool) -> None:
        """Record an attempt for a specific graph."""
        if graph_id not in self.failed_attempts_per_graph:
            self.failed_attempts_per_graph[graph_id] = 0
            self.graph_successes[graph_id] = 0

        if success:
            self.total_valid += 1
            self.graph_successes[graph_id] += 1
        else:
            self.failed_attempts_per_graph[graph_id] += 1

        self.total_generated += 1

    def check_enforcement(self) -> bool:
        """
        Check if the success rate meets the threshold.
        Returns True if enforcement is violated (rate < min).
        """
        if self.total_generated == 0:
            return False

        current_rate = self.total_valid / self.total_generated
        if current_rate < self.min_success_rate:
            self.batch_failed = True
            self.critical_error_message = (
                f"Global success rate ({current_rate:.2%}) dropped below "
                f"threshold ({self.min_success_rate:.2%}) after exhausting retries."
            )
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        """Return current status summary."""
        rate = self.total_valid / self.total_generated if self.total_generated > 0 else 0.0
        return {
            "total_generated": self.total_generated,
            "total_valid": self.total_valid,
            "success_rate": rate,
            "min_required": self.min_success_rate,
            "batch_failed": self.batch_failed,
            "critical_error": self.critical_error_message,
            "failed_attempts_per_graph": self.failed_attempts_per_graph,
        }

def generate_single_graph(
    generator: BaseGenerator, graph_id: str, max_attempts: int
) -> Tuple[Optional[nx.Graph], bool]:
    """
    Attempt to generate a single connected graph.
    Returns (graph, success).
    """
    for attempt in range(max_attempts):
        try:
            # Generate graph
            graph = generator.generate()
            if graph is None:
                continue

            # Check connectivity
            if not nx.is_connected(graph):
                continue

            # Success
            return graph, True
        except Exception as e:
            logging.warning(f"Attempt {attempt+1} failed for {graph_id}: {e}")
            continue

    return None, False

def run_batch_generation(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestrate the batch generation process with global success rate monitoring.
    """
    init_logging()
    seed = config.get("global_seed", 42)
    set_seed(seed)

    topology_targets = config.get("topology_targets", [])
    batch_size = config.get("batch_size", BATCH_SIZE_DEFAULT)
    max_attempts = config.get("thresholds", {}).get("max_attempts_per_graph", 10)
    min_success_rate = config.get("thresholds", {}).get("success_rate_min", 0.95)

    generators_map = {
        "erdos_renyi": ErdosRenyiGenerator,
        "watts_strogatz": WattsStrogatzGenerator,
        "barabasi_albert": BarabasiAlbertGenerator,
    }

    monitor = GlobalSuccessRateMonitor(
        min_success_rate=min_success_rate, max_attempts=max_attempts
    )

    results = []
    run_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    logging.info(f"Starting batch generation with seed {seed} and run_id {run_id}")

    for topology in topology_targets:
        if topology not in generators_map:
            logging.warning(f"Unknown topology target: {topology}")
            continue

        generator_class = generators_map[topology]
        generator = generator_class(config=config)

        for i in range(batch_size):
            graph_id = f"{topology}_{i+1}"
            start_time = time.time()
            graph, success = generate_single_graph(generator, graph_id, max_attempts)
            duration = time.time() - start_time

            monitor.record_attempt(graph_id, success)

            if success:
                metrics = extract_metrics(graph)
                bin_label = classify_graph(metrics["clustering_coefficient"], config)
                result_entry = {
                    "graph_id": graph_id,
                    "topology": topology,
                    "nodes": list(graph.nodes()),
                    "edges": list(graph.edges()),
                    "metrics": metrics,
                    "bin_label": bin_label,
                    "success": True,
                    "duration_seconds": duration,
                }
                results.append(result_entry)
                log_run(
                    run_id=run_id,
                    seed=seed,
                    status="success",
                    duration_seconds=duration,
                    event_type="graph_generated",
                )
            else:
                log_run(
                    run_id=run_id,
                    seed=seed,
                    status="failed",
                    duration_seconds=duration,
                    event_type="graph_generated",
                )
                logging.error(f"Failed to generate valid graph for {graph_id} after {max_attempts} attempts")

    # Final Enforcement Check
    if monitor.check_enforcement():
        logging.critical(monitor.critical_error_message)
        # Log the critical failure to the run log
        log_run(
            run_id=run_id,
            seed=seed,
            status="critical_failure",
            duration_seconds=0.0,
            event_type="simulation_end", # Using end event to mark batch stop
        )
        raise RuntimeError(monitor.critical_error_message)

    # Write Manifest
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": run_id,
        "seed": seed,
        "timestamp": datetime.now().isoformat(),
        "total_graphs": len(results),
        "success_rate": monitor.get_status()["success_rate"],
        "results": results,
    }

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)

    logging.info(f"Batch generation complete. Manifest written to {MANIFEST_PATH}")
    return manifest

def main():
    """Main entry point for batch generation."""
    config = load_config()
    try:
        run_batch_generation(config)
    except Exception as e:
        logging.error(f"Batch generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
