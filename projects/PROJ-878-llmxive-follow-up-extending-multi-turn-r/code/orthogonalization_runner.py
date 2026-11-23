"""
Orthogonalization Runner for Stratified Orthogonalization.

Implements rejection sampling to ensure |r| < 0.2 between nesting_depth
and branching_factor in generated graph datasets.
"""
import os
import sys
import json
import math
import logging
import random
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

import networkx as nx
import numpy as np

# Import from project utils
from utils.logging_utils import configure_logging, log_experiment_metadata
from utils.graph_utils import compute_graph_metrics, is_dag

# Configure logging
logger = logging.getLogger(__name__)

def pearson_correlation(x: List[float], y: List[float]) -> float:
    """Calculate Pearson correlation coefficient between two lists."""
    if len(x) != len(y) or len(x) == 0:
        return 0.0
    
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    denom_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    denom_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
    
    if denom_x == 0 or denom_y == 0:
        return 0.0
    
    return numerator / (denom_x * denom_y)

def generate_candidate_graph(
    target_depth: int,
    target_branching: float,
    min_nodes: int = 5,
    max_nodes: int = 20
) -> Optional[nx.DiGraph]:
    """
    Generate a single candidate DAG with approximate target depth and branching.
    Uses a constructive approach to bias towards targets, but exact values
    will be measured after generation.
    """
    # Randomize number of nodes slightly
    num_nodes = random.randint(min_nodes, max_nodes)
    
    G = nx.DiGraph()
    G.add_nodes_from(range(num_nodes))
    
    # Create a backbone path for depth
    # Depth = longest path length (number of edges)
    # We need a path of length 'target_depth'
    effective_depth = min(target_depth, num_nodes - 1)
    
    if effective_depth < 1:
        return None
        
    backbone = list(range(effective_depth + 1))
    for i in range(len(backbone) - 1):
        G.add_edge(backbone[i], backbone[i+1])
    
    # Add remaining nodes
    remaining_nodes = [n for n in range(num_nodes) if n not in backbone]
    
    # Add edges to approximate branching factor
    # Branching factor = mean in-degree (excluding source) or mean out-degree?
    # Based on graph_utils, branching_factor is mean in-degree of non-source nodes
    # We'll add edges to approximate the target mean in-degree
    
    current_edges = G.number_of_edges()
    target_edges = int(target_branching * (num_nodes - 1)) # Approximation
    
    # Add random edges ensuring acyclicity
    attempts = 0
    max_attempts = 1000
    
    while G.number_of_edges() < target_edges and attempts < max_attempts:
        u = random.choice(range(num_nodes))
        v = random.choice(range(num_nodes))
        
        if u != v and not G.has_edge(u, v):
            # Check if adding edge creates a cycle
            try:
                test_G = G.copy()
                test_G.add_edge(u, v)
                if nx.is_directed_acyclic_graph(test_G):
                    G.add_edge(u, v)
            except:
                pass
        
        attempts += 1
    
    # Verify it's a DAG
    if not nx.is_directed_acyclic_graph(G):
        return None
        
    return G

def run_orthogonalization(
    num_instances: int = 500,
    target_depth_range: Tuple[int, int] = (3, 6),
    target_branching_range: Tuple[float, float] = (1.0, 5.0),
    max_rejection_ratio: float = 0.2,
    seed: int = 42
) -> Tuple[List[Dict], float]:
    """
    Run stratified orthogonalization via rejection sampling.
    
    Generates graph instances and filters them to ensure the correlation
    between nesting_depth and branching_factor is below the threshold.
    
    Returns:
        Tuple of (list of accepted graph metadata, final correlation coefficient)
    """
    random.seed(seed)
    np.random.seed(seed)
    
    accepted_graphs = []
    all_depths = []
    all_branchings = []
    
    total_generated = 0
    max_total = num_instances * 10  # Safety limit
    
    logger.info(f"Starting orthogonalization for {num_instances} instances")
    logger.info(f"Target depth range: {target_depth_range}")
    logger.info(f"Target branching range: {target_branching_range}")
    logger.info(f"Max allowed correlation: {max_rejection_ratio}")
    
    while len(accepted_graphs) < num_instances and total_generated < max_total:
        total_generated += 1
        
        # Sample target parameters
        target_depth = random.randint(*target_depth_range)
        target_branching = random.uniform(*target_branching_range)
        
        # Generate candidate
        G = generate_candidate_graph(target_depth, target_branching)
        
        if G is None:
            continue
        
        # Measure actual metrics
        metrics = compute_graph_metrics(G)
        depth = metrics['nesting_depth']
        branching = metrics['branching_factor']
        
        # Check if within range
        if not (target_depth_range[0] <= depth <= target_depth_range[1]):
            continue
        if not (target_branching_range[0] <= branching <= target_branching_range[1]):
            continue
        
        # Add to candidate list
        all_depths.append(depth)
        all_branchings.append(branching)
        
        # Check correlation so far
        if len(all_depths) >= 10:
            current_corr = pearson_correlation(all_depths, all_branchings)
            
            # If correlation is too high, reject this instance
            if abs(current_corr) > max_rejection_ratio:
                # Remove the last added values
                all_depths.pop()
                all_branchings.pop()
                logger.debug(f"Rejected instance {total_generated}: corr={current_corr:.3f} > {max_rejection_ratio}")
                continue
        
        # Accept
        graph_dict = nx.node_link_data(G)
        accepted_graphs.append({
            'depth': depth,
            'branching': branching,
            'graph': graph_dict,
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges()
        })
        
        if len(accepted_graphs) % 50 == 0:
            current_corr = pearson_correlation(all_depths, all_branchings)
            logger.info(f"Accepted {len(accepted_graphs)} instances, current corr: {current_corr:.3f}")
    
    # Final correlation check
    if len(all_depths) < 2:
        final_corr = 0.0
    else:
        final_corr = pearson_correlation(all_depths, all_branchings)
    
    logger.info(f"Orthogonalization complete. Generated {total_generated}, Accepted {len(accepted_graphs)}")
    logger.info(f"Final correlation coefficient: {final_corr:.4f}")
    
    if abs(final_corr) >= max_rejection_ratio:
        logger.warning(f"WARNING: Final correlation {final_corr:.4f} exceeds threshold {max_rejection_ratio}")
    
    return accepted_graphs, final_corr

def main():
    """Main entry point for orthogonalization runner."""
    configure_logging(level=logging.INFO)
    
    # Configuration
    num_instances = 500
    depth_range = (3, 6)
    branching_range = (1.0, 5.0)
    max_corr = 0.2
    seed = 42
    
    log_experiment_metadata({
        'task': 'T013_Stratified_Orthogonalization',
        'num_instances': num_instances,
        'depth_range': depth_range,
        'branching_range': branching_range,
        'max_correlation': max_corr,
        'seed': seed
    })
    
    # Run orthogonalization
    graphs, final_corr = run_orthogonalization(
        num_instances=num_instances,
        target_depth_range=depth_range,
        target_branching_range=branching_range,
        max_rejection_ratio=max_corr,
        seed=seed
    )
    
    # Prepare output
    output_data = {
        'metadata': {
            'num_instances': len(graphs),
            'final_correlation': final_corr,
            'target_correlation_threshold': max_corr,
            'depth_range': depth_range,
            'branching_range': branching_range
        },
        'graphs': []
    }
    
    # Extract stats for output
    depths = [g['depth'] for g in graphs]
    branchings = [g['branching'] for g in graphs]
    
    output_data['metadata']['actual_depth_range'] = (min(depths), max(depths))
    output_data['metadata']['actual_branching_range'] = (min(branchings), max(branchings))
    output_data['metadata']['mean_depth'] = np.mean(depths)
    output_data['metadata']['mean_branching'] = np.mean(branchings)
    
    # Save graphs (without full graph structure for brevity in this runner, 
    # full structure will be saved by write_puzzles.py)
    for i, g in enumerate(graphs):
        output_data['graphs'].append({
            'instance_id': f'ortho_{i:04d}',
            'depth': g['depth'],
            'branching': g['branching'],
            'num_nodes': g['num_nodes'],
            'num_edges': g['num_edges']
        })
    
    # Write output
    output_path = Path('data/processed/orthogonalization_results.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Results written to {output_path}")
    logger.info(f"Final correlation: {final_corr:.4f}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
