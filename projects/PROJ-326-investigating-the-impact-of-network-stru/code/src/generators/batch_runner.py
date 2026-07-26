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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import from project API surface
from code.src.generators.base import BaseGenerator
from code.src.generators.er import ErdosRenyiGenerator
from code.src.generators.sw import WattsStrogatzGenerator
from code.src.generators.sf import BarabasiAlbertGenerator
from code.src.generators.timeout import TimeoutHandler, enforce_timeout
from code.src.generators.retry_logic import RetryHandler
from code.src.generators.metadata import save_graph_metadata, log_generation_batch
from code.src.generators.binning import classify_graph
from code.src.utils.config import load_config
from code.src.utils.logging import log_run, log_metric, get_run_log
from code.src.utils.io import save_graph_gpickle, compute_file_checksum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_generator(topology_class: str, config: Dict[str, Any]) -> BaseGenerator:
    """
    Factory function to instantiate the appropriate generator based on topology class.

    Args:
        topology_class: One of 'erdos_renyi', 'watts_strogatz', 'barabasi_albert'
        config: Configuration dictionary with generator parameters

    Returns:
        Instantiated generator object

    Raises:
        ValueError: If topology_class is not recognized
    """
    if topology_class == 'erdos_renyi':
        return ErdosRenyiGenerator(config.get('er_params', {}))
    elif topology_class == 'watts_strogatz':
        return WattsStrogatzGenerator(config.get('sw_params', {}))
    elif topology_class == 'barabasi_albert':
        return BarabasiAlbertGenerator(config.get('sf_params', {}))
    else:
        raise ValueError(f"Unknown topology class: {topology_class}")


def generate_single_graph(
    generator: BaseGenerator,
    topology_class: str,
    seed: int,
    retry_handler: RetryHandler,
    timeout_handler: TimeoutHandler,
    run_id: str
) -> Tuple[Optional[Any], str]:
    """
    Generate a single graph with retry and timeout handling.

    Args:
        generator: The generator instance
        topology_class: Class of the topology
        seed: Random seed for this graph
        retry_handler: Handler for retry logic on disconnection
        timeout_handler: Handler for timeout enforcement
        run_id: Unique run identifier for logging

    Returns:
        Tuple of (graph object or None, status string)
    """
    start_time = time.time()

    try:
        # Apply timeout wrapper
        graph = enforce_timeout(
            generator.generate,
            timeout_seconds=timeout_handler.get_timeout(),
            seed=seed
        )

        # Check connectivity (handled internally by generator, but verify)
        if not generator.is_connected(graph):
            status = "[DISCONNECTED_NETWORK_FAILURE]"
            logger.warning(f"Generated disconnected graph for {topology_class} at seed {seed}")
            return None, status

        duration = time.time() - start_time
        log_metric(
            event_type="graph_generated",
            run_id=run_id,
            seed=seed,
            topology_class=topology_class,
            duration_ms=int(duration * 1000),
            status="SUCCESS"
        )

        return graph, "SUCCESS"

    except Exception as e:
        duration = time.time() - start_time
        error_msg = str(e)
        logger.error(f"Error generating graph for {topology_class} at seed {seed}: {error_msg}")

        log_metric(
            event_type="graph_generation_error",
            run_id=run_id,
            seed=seed,
            topology_class=topology_class,
            duration_ms=int(duration * 1000),
            status="ERROR",
            error_message=error_msg
        )

        return None, f"[ERROR]: {error_msg}"


def generate_batch(
    topology_class: str,
    config: Dict[str, Any],
    batch_size: int,
    output_dir: Path,
    run_id: str
) -> Dict[str, Any]:
    """
    Generate a batch of graphs for a specific topology class.

    Implements stratified sampling and retry logic as per T062c and T018b.

    Args:
        topology_class: Class of topology to generate
        config: Full configuration dictionary
        batch_size: Target number of graphs to generate
        output_dir: Directory to save generated graphs
        run_id: Unique run identifier

    Returns:
        Dictionary with batch statistics and metadata
    """
    logger.info(f"Starting batch generation for {topology_class}, target size: {batch_size}")

    # Initialize generator
    generator = get_generator(topology_class, config)

    # Initialize handlers
    retry_config = config.get('retry_params', {})
    retry_handler = RetryHandler(
        max_retries=retry_config.get('max_retries', 5),
        timeout_factor=retry_config.get('timeout_factor', 1.5)
    )

    timeout_config = config.get('timeout_params', {})
    timeout_handler = TimeoutHandler(
        default_timeout=timeout_config.get('default_timeout_seconds', 300)
    )

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir = output_dir / "metadata"
    metadata_dir.mkdir(exist_ok=True)

    # Batch tracking
    graphs_generated = []
    failed_graphs = []
    total_attempts = 0
    start_time = time.time()

    # Stratification parameters
    strat_params = config.get('stratification_params', {})
    bins = strat_params.get('bins', [0.1, 0.2, 0.3, 0.4, 0.5])
    target_counts = strat_params.get('target_counts', {})
    tolerance = strat_params.get('tolerance', 0.05)

    # Initialize bin counters
    bin_counts = {b: 0 for b in bins}

    # Generate graphs until batch size or bin quotas are met
    attempts = 0
    max_attempts = batch_size * 10  # Safety limit

    while len(graphs_generated) < batch_size and attempts < max_attempts:
        attempts += 1
        total_attempts += 1

        # Generate seed for this attempt
        seed = config.get('global_seed', 42) + attempts

        # Generate graph
        graph, status = generate_single_graph(
            generator=generator,
            topology_class=topology_class,
            seed=seed,
            retry_handler=retry_handler,
            timeout_handler=timeout_handler,
            run_id=run_id
        )

        if graph is not None:
            # Classify graph by clustering coefficient
            clustering = classify_graph(graph)
            bin_key = None
            for i, b in enumerate(bins):
                if i == len(bins) - 1:
                    if clustering <= b + tolerance:
                        bin_key = b
                        break
                elif b - tolerance <= clustering <= b + tolerance:
                    bin_key = b
                    break

            if bin_key is None:
                bin_key = bins[-1]  # Default to highest bin

            # Check if bin quota is met
            if bin_key in target_counts and bin_counts[bin_key] >= target_counts[bin_key]:
                # Skip this graph if bin is full
                logger.debug(f"Bin {bin_key} quota met, skipping graph")
                continue

            # Save graph
            graph_id = f"{topology_class}_{len(graphs_generated)}"
            graph_path = output_dir / f"{graph_id}.gpickle"
            save_graph_gpickle(graph, graph_path)

            # Save metadata
            metadata = {
                "graph_id": graph_id,
                "topology_class": topology_class,
                "seed": seed,
                "clustering_coefficient": clustering,
                "num_nodes": graph.number_of_nodes(),
                "num_edges": graph.number_of_edges(),
                "generation_algorithm": generator.__class__.__name__,
                "parameter_values": generator.get_params()
            }
            save_graph_metadata(metadata_dir, metadata)

            graphs_generated.append({
                "id": graph_id,
                "path": str(graph_path),
                "seed": seed,
                "clustering": clustering,
                "bin": bin_key
            })

            if bin_key in bin_counts:
                bin_counts[bin_key] += 1

        else:
            # Track failure
            failed_graphs.append({
                "attempt": attempts,
                "seed": seed,
                "status": status
            })

            # Check retry limit
            if retry_handler.should_abort(topology_class, status):
                logger.warning(f"Retry limit reached for {topology_class}, flagging as [DISCONNECTED_NETWORK_FAILURE]")
                log_metric(
                    event_type="divergence_detected",
                    run_id=run_id,
                    seed=seed,
                    topology_class=topology_class,
                    status="[DISCONNECTED_NETWORK_FAILURE]",
                    retry_count=retry_handler.get_retry_count(topology_class)
                )

    duration = time.time() - start_time

    # Calculate rejection rate for sample size adjustment (T056)
    rejection_rate = len(failed_graphs) / total_attempts if total_attempts > 0 else 0
    rejection_threshold = config.get('rejection_threshold', 0.4)
    adjustment_factor = config.get('rejection_adjustment_factor', 1.5)

    if rejection_rate > rejection_threshold:
        new_batch_size = int(batch_size * adjustment_factor)
        log_metric(
            event_type="sample_size_adjustment",
            run_id=run_id,
            topology_class=topology_class,
            original_batch_size=batch_size,
            new_batch_size=new_batch_size,
            rejection_rate=rejection_rate,
            adjustment_factor=adjustment_factor,
            status="ADJUSTED"
        )
        logger.info(f"Sample Size Adjustment: New batch size = {new_batch_size} (rejection rate: {rejection_rate:.2%})")

    # Log batch summary
    log_metric(
        event_type="simulation_end",
        run_id=run_id,
        topology_class=topology_class,
        total_generated=len(graphs_generated),
        total_attempts=total_attempts,
        failed_count=len(failed_graphs),
        success_rate=len(graphs_generated) / total_attempts if total_attempts > 0 else 0,
        duration_ms=int(duration * 1000),
        status="COMPLETE",
        bin_distribution=bin_counts
    )

    return {
        "topology_class": topology_class,
        "target_size": batch_size,
        "actual_size": len(graphs_generated),
        "total_attempts": total_attempts,
        "failed_count": len(failed_graphs),
        "success_rate": len(graphs_generated) / total_attempts if total_attempts > 0 else 0,
        "rejection_rate": rejection_rate,
        "duration_seconds": duration,
        "bin_distribution": bin_counts,
        "failed_graphs": failed_graphs,
        "generated_graphs": graphs_generated
    }


def main():
    """
    Main entry point for batch generation.

    Parses command line arguments, loads configuration, and orchestrates
    batch generation for all configured topology classes.
    """
    parser = argparse.ArgumentParser(description="Batch graph generation for network topology study")
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.yaml",
        help="Path to configuration file (default: code/config.yaml)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw",
        help="Output directory for generated graphs (default: data/raw)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Target batch size per topology class (default: 10)"
    )
    parser.add_argument(
        "--topology",
        type=str,
        nargs="+",
        choices=['erdos_renyi', 'watts_strogatz', 'barabasi_albert', 'all'],
        default=['all'],
        help="Topology classes to generate (default: all)"
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Initialize run
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    logger.info(f"Starting batch generation run: {run_id}")

    # Log run start
    log_run(
        event_type="batch_generation_start",
        run_id=run_id,
        seed=config.get('global_seed', 42),
        config_path=args.config,
        status="STARTED"
    )

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine topology classes
    topology_classes = config.get('topology_targets', {}).get('classes', ['erdos_renyi', 'watts_strogatz', 'barabasi_albert'])
    if 'all' in args.topology:
        classes_to_generate = topology_classes
    else:
        classes_to_generate = args.topology

    # Generate batches
    batch_results = []
    for topology_class in classes_to_generate:
        batch_size = config.get('topology_targets', {}).get('batch_sizes', {}).get(
            topology_class, args.batch_size
        )

        result = generate_batch(
            topology_class=topology_class,
            config=config,
            batch_size=batch_size,
            output_dir=output_dir,
            run_id=run_id
        )
        batch_results.append(result)

    # Log run completion
    total_generated = sum(r['actual_size'] for r in batch_results)
    total_attempts = sum(r['total_attempts'] for r in batch_results)

    log_run(
        event_type="batch_generation_complete",
        run_id=run_id,
        seed=config.get('global_seed', 42),
        total_generated=total_generated,
        total_attempts=total_attempts,
        success_rate=total_generated / total_attempts if total_attempts > 0 else 0,
        status="COMPLETE"
    )

    # Save batch summary
    summary_path = output_dir / "batch_summary.json"
    with open(summary_path, 'w') as f:
        json.dump({
            "run_id": run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config_path": args.config,
            "results": batch_results
        }, f, indent=2)

    logger.info(f"Batch generation complete. Summary saved to {summary_path}")
    logger.info(f"Total graphs generated: {total_generated}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
