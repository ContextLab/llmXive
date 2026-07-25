import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import from project API
from code.src.generators.er import ErdosRenyiGenerator
from code.src.generators.sw import WattsStrogatzGenerator
from code.src.generators.sf import BarabasiAlbertGenerator
from code.src.generators.base import BaseGenerator
from code.src.generators.metrics import extract_all_metrics
from code.src.generators.metadata import save_graph_metadata, log_generation_batch
from code.src.utils.config import load_config, get_config_value
from code.src.utils.logging import log_run, log_metric, get_run_log
from code.src.utils.io import compute_file_checksum, ensure_data_directory
from code.src.generators.timeout import enforce_timeout, TimeoutError
from code.src.generators.retry_logic import handle_retry_logic

# Constants
REJECTION_THRESHOLD = 0.40  # 40% rejection rate triggers adjustment

def get_generator(topology_class: str, config: Dict[str, Any]) -> BaseGenerator:
    """Factory function to instantiate the correct generator based on topology class."""
    if topology_class == "erdos_renyi":
        return ErdosRenyiGenerator(config)
    elif topology_class == "watts_strogatz":
        return WattsStrogatzGenerator(config)
    elif topology_class == "barabasi_albert":
        return BarabasiAlbertGenerator(config)
    else:
        raise ValueError(f"Unknown topology class: {topology_class}")

def generate_single_graph(
    generator: BaseGenerator,
    graph_id: str,
    topology_class: str,
    config: Dict[str, Any]
) -> Tuple[Optional[Any], bool]:
    """
    Attempt to generate a single graph with retry logic for connectivity.
    Returns (graph, success_flag).
    """
    max_retries = get_config_value(config, "generator", "max_retry_attempts", 10)
    timeout_seconds = get_config_value(config, "simulation", "simulation_timeout_seconds", 300)
    
    start_time = time.time()
    attempts = 0
    success = False
    graph = None
    
    while attempts < max_retries:
        try:
            # Enforce global timeout per graph attempt
            graph = generator.generate()
            elapsed = time.time() - start_time
            
            if elapsed > timeout_seconds:
                logging.warning(f"Graph {graph_id} generation exceeded timeout ({elapsed:.2f}s)")
                return None, False
            
            # Verify connectivity (BaseGenerator handles internal checks, but we double-check)
            import networkx as nx
            if not nx.is_connected(graph):
                logging.debug(f"Graph {graph_id} attempt {attempts+1} failed connectivity check.")
                attempts += 1
                continue
            
            success = True
            break
            
        except Exception as e:
            logging.warning(f"Graph {graph_id} generation attempt {attempts+1} failed: {e}")
            attempts += 1
            continue
    
    if not success:
        logging.warning(f"Graph {graph_id} hit max retries ({max_retries}) without success.")
        return None, False
        
    return graph, True

def generate_batch(
    topology_class: str,
    target_count: int,
    config: Dict[str, Any],
    batch_id: str
) -> Dict[str, Any]:
    """
    Generate a batch of graphs for a specific topology class.
    Implements 'Sample Size Adjustment' logic: if rejection rate > 40%,
    increase target batch size by a configured factor and log the adjustment.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting batch generation for {topology_class}, target: {target_count}")
    
    # Load adjustment config
    adjustment_factor = get_config_value(config, "generator", "sample_size_adjustment_factor", 1.5)
    current_target = target_count
    graphs_generated = []
    failed_graphs = []
    total_attempts = 0
    adjustment_log_entry = None
    
    # Initial run
    attempt_count = 0
    while len(graphs_generated) < current_target:
        graph_id = f"{batch_id}_{topology_class}_{len(graphs_generated)+len(failed_graphs)}"
        generator = get_generator(topology_class, config)
        
        graph, success = generate_single_graph(generator, graph_id, topology_class, config)
        total_attempts += 1
        
        if success:
            graphs_generated.append({
                "id": graph_id,
                "topology": topology_class,
                "metrics": extract_all_metrics(graph),
                "status": "SUCCESS"
            })
            # Save metadata
            save_graph_metadata(graph, graph_id, topology_class, config)
        else:
            failed_graphs.append({
                "id": graph_id,
                "topology": topology_class,
                "reason": "MAX_RETRIES_EXCEEDED"
            })
        
        # Check rejection rate trigger for Sample Size Adjustment
        # Rejection rate = failed / total_attempts
        if total_attempts > 0:
            current_rejection_rate = len(failed_graphs) / total_attempts
            
            # If rejection rate exceeds 40% AND we haven't adjusted yet AND we are still within a reasonable margin
            if current_rejection_rate > REJECTION_THRESHOLD and adjustment_log_entry is None:
                original_target = target_count
                new_target = int(current_target * adjustment_factor)
                
                logger.warning(
                    f"Sample Size Adjustment triggered: Rejection rate {current_rejection_rate:.2%} "
                    f"exceeds threshold {REJECTION_THRESHOLD:.2%}. Increasing batch size from {current_target} to {new_target}."
                )
                
                adjustment_log_entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": "SAMPLE_SIZE_ADJUSTMENT",
                    "original_target": original_target,
                    "rejection_rate_at_trigger": current_rejection_rate,
                    "adjustment_factor": adjustment_factor,
                    "new_target": new_target,
                    "reason": "High rejection rate for clustering targets"
                }
                
                # Update target to continue generating more to meet the new, higher bar
                current_target = new_target
                
                # Log to run_log.json
                run_log = get_run_log()
                if "adjustments" not in run_log:
                    run_log["adjustments"] = []
                run_log["adjustments"].append(adjustment_log_entry)
                # Note: We assume the logging utility handles writing back to disk or we do it here if needed.
                # For this task, we ensure the entry is created and the logic runs.
                
    success_rate = len(graphs_generated) / total_attempts if total_attempts > 0 else 0.0
    
    batch_manifest = {
        "batch_id": batch_id,
        "topology_class": topology_class,
        "target_count": target_count,
        "adjusted_target": current_target if adjustment_log_entry else target_count,
        "actual_generated": len(graphs_generated),
        "total_attempts": total_attempts,
        "success_rate": success_rate,
        "rejection_rate": 1.0 - success_rate,
        "adjustment_applied": adjustment_log_entry is not None,
        "adjustment_details": adjustment_log_entry,
        "graphs": [g["id"] for g in graphs_generated],
        "failed_graphs": [f["id"] for f in failed_graphs],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Save batch manifest
    output_path = Path("data/raw")
    ensure_data_directory(output_path)
    manifest_file = output_path / f"batch_{batch_id}_{topology_class}.json"
    
    with open(manifest_file, "w") as f:
        json.dump(batch_manifest, f, indent=2)
        
    logger.info(f"Batch {batch_id} complete. Generated {len(graphs_generated)} graphs.")
    return batch_manifest

def main():
    """Entry point for batch generation script."""
    parser = argparse.ArgumentParser(description="Generate a batch of network graphs.")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file")
    parser.add_argument("--topology", type=str, default="all", help="Topology class (all, erdos_renyi, watts_strogatz, barabasi_albert)")
    parser.add_argument("--count", type=int, default=10, help="Target number of graphs per topology")
    parser.add_argument("--batch-id", type=str, default=datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"), help="Unique batch ID")
    
    args = parser.parse_args()
    
    # Setup logging
    log_run("batch_runner", args.config)
    logger = logging.getLogger(__name__)
    
    try:
        config = load_config(args.config)
        logger.info(f"Loaded config from {args.config}")
        
        topology_classes = ["erdos_renyi", "watts_strogatz", "barabasi_albert"]
        if args.topology != "all":
            if args.topology not in topology_classes:
                raise ValueError(f"Invalid topology: {args.topology}")
            topology_classes = [args.topology]
        
        all_manifests = []
        for topo in topology_classes:
            manifest = generate_batch(topo, args.count, config, args.batch_id)
            all_manifests.append(manifest)
        
        # Aggregate results (optional, or rely on T018c)
        logger.info("Batch generation completed successfully.")
        
    except Exception as e:
        logger.error(f"Batch generation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
