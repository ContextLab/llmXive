"""
Stratified sampling loop for network generation.

This module implements the logic to generate graphs until bin quotas
defined in `config.yaml` under `stratification_params` are met.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import networkx as nx
import numpy as np

from code.src.utils.config import get_global_config, load_config
from code.src.utils.logging import log_run, log_metric
from code.src.generators.binning import classify_graph
from code.src.generators.batch_runner import generate_batch
from code.src.generators.metadata import save_graph_metadata

logger = logging.getLogger(__name__)

def run_stratified_generation(config_path: str = "code/config.yaml",
                              output_dir: str = "data/raw",
                              log_path: str = "data/run_log.json") -> Dict[str, Any]:
    """
    Execute the stratified sampling loop.

    Generates graphs repeatedly, classifying them into clustering coefficient bins,
    until the target counts for each bin (defined in config) are met.

    Args:
        config_path: Path to the configuration file.
        output_dir: Directory to save generated graphs.
        log_path: Path to the run log file.

    Returns:
        A summary dictionary of the generation process.
    """
    # Load configuration
    config = load_config(config_path)
    strat_params = config.get("stratification_params", {})

    if not strat_params:
        raise ValueError("stratification_params not found in config. Cannot run stratified generation.")

    bins = strat_params.get("bins", [])
    target_counts = strat_params.get("target_counts", {})
    tolerance = strat_params.get("tolerance", 0.0)

    if not bins or not target_counts:
        raise ValueError("bins and target_counts must be defined in stratification_params.")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Initialize state
    current_counts = {b: 0 for b in bins}
    total_generated = 0
    total_attempts = 0
    generated_graphs = []
    failed_graphs = []
    start_time = time.time()

    logger.info(f"Starting stratified generation. Targets: {target_counts}")

    # Check if we are done
    def is_quota_met():
        for b in bins:
            if current_counts.get(b, 0) < target_counts.get(b, 0):
                return False
        return True

    # Main loop
    while not is_quota_met():
        # Determine which bin we still need to fill
        needed_bins = [b for b in bins if current_counts.get(b, 0) < target_counts.get(b, 0)]
        if not needed_bins:
            break

        # Pick a target bin to focus on (simple round-robin or random selection)
        # Here we just pick the first one that needs filling to simplify
        target_bin = needed_bins[0]
        target_clustering = target_bin

        # Generate a single graph
        # We use the batch runner logic but for single generation to control the loop
        # Note: The actual generator selection (ER, SW, SF) is usually config-driven.
        # For stratified sampling, we might need to try different topologies or parameters
        # until we hit the bin. The base generator logic (T051) handles retries for connectivity.
        
        # Since we don't have a direct "generate until bin X" function in base,
        # we will invoke the batch runner for a small batch (e.g., 1 or 5) and filter.
        # However, to be efficient, we should try to bias generation if possible.
        # For now, we generate a batch of 1 and classify.
        
        # We need to select a generator type. Let's assume we cycle or pick randomly.
        # For this implementation, we'll generate using a generic approach or
        # rely on the fact that the user configures the generator type in config.
        # If config specifies a single topology, we might struggle to hit all bins.
        # Assuming the config allows for varied generation or we iterate topologies.
        # To keep it simple and robust: We generate one graph using the configured generator.
        
        # If the config doesn't specify a single generator, we might need to loop through them.
        # Let's assume the config has a 'topology_targets' or similar.
        # For T062c, we assume the existing generators (ER, SW, SF) are available.
        # We will try to generate a graph, classify it, and if it matches a needed bin, accept it.
        
        # Strategy: Generate a graph. If it falls into a bin that is not yet full, accept.
        # If it falls into a full bin, discard (or keep as overflow).
        # If it falls into no bin (out of range), discard.
        
        # To avoid infinite loops if a bin is impossible to hit with current params,
        # we should have a max attempts per bin or global timeout.
        # We will rely on the global timeout mechanism (T016a) if implemented in the runner.
        
        # Let's use a simple batch generation of 1 to keep the loop tight.
        # We need to pick a generator. Let's assume 'watts_strogatz' is the primary for clustering control.
        # Or we can try all. For this task, we will attempt to generate using the 'watts_strogatz' generator
        # as it is most sensitive to clustering coefficient.
        
        # We will call the batch runner for a single graph, but we need to handle the result.
        # The batch_runner returns a list of graphs.
        
        # Since we don't have a direct "generate_one" function exposed that returns a graph object
        # without side effects (like saving), we might need to replicate the logic or use the batch runner
        # and filter.
        
        # Let's implement a simple generation loop using the base generator logic directly.
        # We need to import the specific generators.
        from code.src.generators.er import ErdosRenyiGenerator
        from code.src.generators.sw import WattsStrogatzGenerator
        from code.src.generators.sf import BarabasiAlbertGenerator

        # Try to generate a graph that fits a needed bin.
        # We will try a few times to hit the target bin.
        success = False
        attempts_for_this_graph = 0
        max_attempts_per_graph = 50 # Avoid infinite loop on a single graph attempt

        while attempts_for_this_graph < max_attempts_per_graph:
            attempts_for_this_graph += 1
            total_attempts += 1
            
            # Choose a generator strategy.
            # To hit specific clustering bins, SW is best. But we might need ER/SF too.
            # Let's try SW first, then ER, then SF.
            # Or random. Let's try SW for now as it's the most controllable for clustering.
            
            # We need a seed.
            seed = int(time.time() * 1000000) % (2**32)
            
            # Try Watts-Strogatz
            try:
                sw_gen = WattsStrogatzGenerator(n=100, k=4, p=0.1, seed=seed) # Default p, will vary?
                # Actually, we need to vary p to hit bins.
                # But the generator class might not support dynamic p easily without re-init.
                # Let's assume we can pass p.
                # For simplicity, let's just generate a graph and see.
                # We need to vary parameters to hit bins.
                # This is complex. Let's assume the task implies we generate a batch and filter.
                # But the task says "generating graphs until bin quotas are met".
                # So we must generate.
                
                # Let's try a simple approach: Generate a graph using the configured generator type
                # (from config). If it fits, good. If not, try again.
                # If we can't hit the bin after many tries, log warning.
                
                # For this implementation, we will use the batch_runner's logic for a single graph.
                # But batch_runner expects a generator type.
                # Let's just call the underlying generate logic.
                
                # We will use a simple heuristic:
                # If we need low clustering, try ER.
                # If we need medium, try SW with low p.
                # If we need high, try SW with high p or SF.
                
                # To keep it generic, let's just generate a SW graph with random p.
                p_val = np.random.uniform(0.01, 0.99)
                sw_gen = WattsStrogatzGenerator(n=100, k=4, p=p_val, seed=seed)
                graph = sw_gen.generate()
                
                if graph is None:
                    continue
                
                # Classify
                bin_label, clust_val = classify_graph(graph)
                
                # Check if this bin is needed
                if bin_label in needed_bins and current_counts[bin_label] < target_counts[bin_label]:
                    # Accept
                    graph.graph['bin'] = bin_label
                    graph.graph['clustering'] = clust_val
                    generated_graphs.append(graph)
                    current_counts[bin_label] += 1
                    total_generated += 1
                    success = True
                    
                    # Save metadata
                    graph_id = f"strat_{total_generated}"
                    save_graph_metadata(graph, graph_id, output_dir)
                    # Save graph
                    graph_path = os.path.join(output_dir, f"{graph_id}.gpickle")
                    import networkx as nx
                    nx.write_gpickle(graph, graph_path)
                    
                    logger.info(f"Accepted graph {graph_id} in bin {bin_label} (clust={clust_val:.3f})")
                    break
                else:
                    # Discard or keep as overflow? Task says "until quotas met".
                    # We can discard.
                    pass
                    
            except Exception as e:
                logger.warning(f"Generation attempt failed: {e}")
                continue

        if not success:
            logger.warning(f"Failed to generate a graph for bin {target_bin} after {max_attempts_per_graph} attempts.")
            # In a real scenario, we might adjust parameters or switch generator.
            # For now, we log and continue, but this might lead to infinite loop if bin is unreachable.
            # We should have a global timeout or max total attempts.
            if total_attempts > 10000:
                logger.error("Max total attempts reached. Stopping.")
                break

    duration = time.time() - start_time

    summary = {
        "total_generated": total_generated,
        "total_attempts": total_attempts,
        "success_rate": total_generated / total_attempts if total_attempts > 0 else 0.0,
        "bin_counts": current_counts,
        "target_counts": target_counts,
        "duration_seconds": duration,
        "status": "completed" if is_quota_met() else "incomplete"
    }

    # Log to run_log
    log_metric(log_path, "stratified_generation_summary", summary)

    return summary

def main():
    """Main entry point for stratified runner."""
    import argparse
    parser = argparse.ArgumentParser(description="Run stratified graph generation.")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file.")
    parser.add_argument("--output", type=str, default="data/raw", help="Output directory.")
    parser.add_argument("--log", type=str, default="data/run_log.json", help="Log file path.")
    args = parser.parse_args()

    setup_logging = True # Placeholder for actual logging setup if not done
    # Ensure logging is configured
    logging.basicConfig(level=logging.INFO)

    try:
        result = run_stratified_generation(
            config_path=args.config,
            output_dir=args.output,
            log_path=args.log
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Stratified generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
