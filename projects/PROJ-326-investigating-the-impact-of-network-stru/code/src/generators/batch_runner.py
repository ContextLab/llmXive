"""
Batch runner for generating graphs with sample size adjustment logic.

Implements T056: Adjust batch size if rejection rate exceeds threshold.
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

# Import from project structure
from code.src.generators.base import BaseGenerator
from code.src.generators.er import ErdosRenyiGenerator
from code.src.generators.sw import WattsStrogatzGenerator
from code.src.generators.sf import BarabasiAlbertGenerator
from code.src.utils.config import load_config, get_global_config
from code.src.utils.logging import log_metric, log_run
from code.src.generators.binning import classify_graph
from code.src.generators.quota_checker import check_quotas
from code.src.generators.manifest_updater import save_manifest, update_manifest

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
REJECTION_THRESHOLD = 0.2  # Default threshold from spec
MAX_BATCH_SIZE = 1000      # Safety cap to prevent infinite loops
MIN_BATCH_SIZE = 1         # Minimum batch size
ADJUSTMENT_FACTOR = 1.5    # Factor to increase batch size when rejection is high

def get_generator(topology_type: str) -> BaseGenerator:
    """Factory function to get the appropriate graph generator."""
    generators = {
        'er': ErdosRenyiGenerator,
        'sw': WattsStrogatzGenerator,
        'sf': BarabasiAlbertGenerator
    }
    
    if topology_type not in generators:
        raise ValueError(f"Unknown topology type: {topology_type}. "
                       f"Available: {list(generators.keys())}")
    
    return generators[topology_type]()

def generate_single_graph(generator: BaseGenerator, config: Dict[str, Any]) -> Optional[nx.Graph]:
    """
    Generate a single graph with connectivity check and retry logic.
    
    Returns None if generation fails after retries (rejection).
    """
    try:
        graph = generator.generate(config)
        
        # Verify connectivity (T051 requirement)
        if not nx.is_connected(graph):
            logger.debug(f"Generated disconnected graph, rejecting")
            return None
        
        return graph
    except Exception as e:
        logger.warning(f"Graph generation failed: {e}")
        return None

def generate_batch(
    generator: BaseGenerator,
    config: Dict[str, Any],
    batch_size: int,
    target_bin: Optional[str] = None
) -> Tuple[List[nx.Graph], int, int]:
    """
    Generate a batch of graphs with stratification support.
    
    Returns:
        Tuple of (successful_graphs, total_attempts, rejected_attempts)
    """
    graphs = []
    total_attempts = 0
    rejected_attempts = 0
    
    for _ in range(batch_size):
        total_attempts += 1
        graph = generate_single_graph(generator, config)
        
        if graph is None:
            rejected_attempts += 1
            continue
        
        # Check bin classification if target specified
        if target_bin is not None:
            graph_bin = classify_graph(graph)
            if graph_bin != target_bin:
                rejected_attempts += 1
                continue
        
        graphs.append(graph)
    
    return graphs, total_attempts, rejected_attempts

def calculate_rejection_rate(total_attempts: int, rejected_attempts: int) -> float:
    """Calculate rejection rate as rejected_attempts / total_attempts."""
    if total_attempts == 0:
        return 0.0
    return rejected_attempts / total_attempts

def adjust_batch_size(current_size: int, rejection_rate: float, config: Dict[str, Any]) -> int:
    """
    Adjust batch size based on rejection rate.
    
    Implements T056: If rate > 0.2, increase batch_size by adjustment factor.
    """
    threshold = config.get('stratification_params', {}).get('rejection_threshold', REJECTION_THRESHOLD)
    
    if rejection_rate > threshold:
        new_size = int(current_size * ADJUSTMENT_FACTOR)
        new_size = min(new_size, MAX_BATCH_SIZE)  # Cap at maximum
        logger.info(f"High rejection rate ({rejection_rate:.2f} > {threshold}). "
                   f"Increasing batch size from {current_size} to {new_size}")
        return new_size
    elif rejection_rate < threshold * 0.5 and current_size > MIN_BATCH_SIZE:
        # Optional: decrease batch size if rejection is very low to improve efficiency
        new_size = int(current_size / ADJUSTMENT_FACTOR)
        new_size = max(new_size, MIN_BATCH_SIZE)
        logger.info(f"Low rejection rate ({rejection_rate:.2f}). "
                   f"Decreasing batch size from {current_size} to {new_size}")
        return new_size
    
    return current_size

def run_stratified_generation(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run stratified graph generation with sample size adjustment.
    
    This is the main entry point for T056 logic.
    """
    seed = config.get('global_seed', 42)
    np.random.seed(seed)
    
    strat_params = config.get('stratification_params', {})
    bins = strat_params.get('bins', [0.1, 0.2, 0.3, 0.4, 0.5])
    target_counts = strat_params.get('target_counts', {})
    tolerance = strat_params.get('tolerance', 0.1)
    rejection_threshold = strat_params.get('rejection_threshold', REJECTION_THRESHOLD)
    
    topology_targets = config.get('topology_targets', ['er', 'sw', 'sf'])
    
    # Initialize tracking
    current_counts = {bin_id: 0 for bin_id in bins}
    all_graphs = []
    batch_size = 10  # Initial batch size
    total_generated = 0
    total_attempts = 0
    total_rejected = 0
    
    logger.info(f"Starting stratified generation with bins: {bins}")
    logger.info(f"Target counts: {target_counts}")
    logger.info(f"Initial batch size: {batch_size}")
    
    # Generation loop with sample size adjustment
    iteration = 0
    max_iterations = 100  # Safety limit
    
    while not check_quotas(current_counts, target_counts) and iteration < max_iterations:
        iteration += 1
        logger.info(f"Iteration {iteration}: Current counts = {current_counts}")
        
        # Select bin that needs more graphs
        needs_graph = None
        for bin_id in bins:
            if current_counts.get(bin_id, 0) < target_counts.get(bin_id, 0):
                needs_graph = bin_id
                break
        
        if needs_graph is None:
            break  # All quotas met
        
        # Generate batch
        # Select topology type (round-robin or random)
        topology = topology_targets[iteration % len(topology_targets)]
        generator = get_generator(topology)
        
        # Adjust config for this topology
        topology_config = config.get('simulation_params', {}).get(topology, {})
        topology_config['seed'] = seed + iteration  # Vary seed per batch
        
        graphs, attempts, rejected = generate_batch(
            generator, topology_config, batch_size, target_bin=needs_graph
        )
        
        total_attempts += attempts
        total_rejected += rejected
        total_generated += len(graphs)
        
        # Update counts and graphs
        for graph in graphs:
            graph_bin = classify_graph(graph)
            if graph_bin in current_counts:
                current_counts[graph_bin] += 1
                all_graphs.append({
                    'graph': graph,
                    'bin': graph_bin,
                    'topology': topology,
                    'seed': topology_config['seed']
                })
        
        # T056: Calculate rejection rate and adjust batch size
        rejection_rate = calculate_rejection_rate(attempts, rejected)
        logger.info(f"Batch {iteration}: Generated {len(graphs)}/{attempts}, "
                   f"rejection rate: {rejection_rate:.2f}")
        
        batch_size = adjust_batch_size(batch_size, rejection_rate, config)
        
        # Log progress
        log_metric(
            event_type='batch_completed',
            run_id=f'gen_{iteration}',
            seed=seed,
            status='success' if len(graphs) > 0 else 'partial',
            duration_seconds=0.0,  # Would be measured in real run
            metadata={
                'iteration': iteration,
                'batch_size': batch_size,
                'graphs_generated': len(graphs),
                'rejection_rate': rejection_rate,
                'current_counts': current_counts
            }
        )
    
    # Final statistics
    final_rejection_rate = calculate_rejection_rate(total_attempts, total_rejected)
    logger.info(f"Generation complete. Total: {total_generated} graphs, "
               f"attempts: {total_attempts}, final rejection rate: {final_rejection_rate:.2f}")
    
    return {
        'graphs': all_graphs,
        'total_generated': total_generated,
        'total_attempts': total_attempts,
        'total_rejected': total_rejected,
        'final_rejection_rate': final_rejection_rate,
        'final_batch_size': batch_size,
        'iterations': iteration,
        'current_counts': current_counts
    }

def save_batch_results(results: Dict[str, Any], output_path: str):
    """Save batch generation results to JSON."""
    # Prepare serializable data (exclude actual graph objects for manifest)
    serializable = {
        'total_generated': results['total_generated'],
        'total_attempts': results['total_attempts'],
        'total_rejected': results['total_rejected'],
        'final_rejection_rate': results['final_rejection_rate'],
        'final_batch_size': results['final_batch_size'],
        'iterations': results['iterations'],
        'current_counts': results['current_counts'],
        'stratification_summary': {
            'bins': list(results['current_counts'].keys()),
            'counts': results['current_counts']
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(serializable, f, indent=2)
    
    logger.info(f"Saved batch results to {output_path}")

def main():
    """Main entry point for batch runner with sample size adjustment."""
    parser = argparse.ArgumentParser(description='Batch graph generator with sample size adjustment')
    parser.add_argument('--config', type=str, default='code/config.yaml',
                      help='Path to configuration file')
    parser.add_argument('--output', type=str, default='data/analysis/batch_results.json',
                      help='Output path for results')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    seed = config.get('global_seed', 42)
    np.random.seed(seed)
    
    # Setup logging
    log_run(
        run_id='batch_runner_main',
        seed=seed,
        event_type='simulation_start',
        status='started'
    )
    
    try:
        # Run stratified generation with T056 logic
        results = run_stratified_generation(config)
        
        # Ensure output directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save results
        save_batch_results(results, str(output_path))
        
        # Log completion
        log_metric(
            event_type='simulation_end',
            run_id='batch_runner_main',
            seed=seed,
            status='completed',
            duration_seconds=0.0,
            metadata={'total_generated': results['total_generated']}
        )
        
        logger.info(f"Batch generation completed successfully. "
                   f"Generated {results['total_generated']} graphs with "
                   f"final rejection rate: {results['final_rejection_rate']:.2f}")
        
    except Exception as e:
        logger.error(f"Batch generation failed: {e}")
        log_metric(
            event_type='simulation_end',
            run_id='batch_runner_main',
            seed=seed,
            status='failed',
            duration_seconds=0.0,
            metadata={'error': str(e)}
        )
        raise

if __name__ == '__main__':
    main()
