"""
Sweep logic for the OPID Critical-First Routing Complexity Analysis.

Implements the threshold sweep (0.0 to 1.0 in steps of 0.1) and orchestrates
the execution of experiments across tiers and thresholds.
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from experiments.runner import ExperimentRunner, ExperimentConfig
from utils.logging_setup import get_experiment_logger
from config import get_seed, set_seed, ensure_directories
import numpy as np
import os
import csv
from environment.graph_generator import GraphGenerator
from agent.opid_router import OPIDRouter
from agent.policy import create_baseline_policy
from utils.metrics import calculate_success_rate, calculate_action_entropy

@dataclass
class SweepConfig:
    """Configuration for the parameter sweep."""
    min_threshold: float = 0.0
    max_threshold: float = 1.0
    step_size: float = 0.1
    tiers: List[str] = field(default_factory=lambda: ["tier_1", "tier_2", "tier_3"])
    episodes_per_setting: int = 1000  # Will be overridden by config in real usage
    seed: int = 42

def generate_thresholds(config: SweepConfig) -> List[float]:
    """
    Generate a list of threshold values from min to max with the specified step size.
    
    Args:
        config: SweepConfig containing min, max, and step_size.
        
    Returns:
        List of float thresholds.
    """
    thresholds = []
    current = config.min_threshold
    # Use a small epsilon to handle floating point precision issues
    epsilon = 1e-9
    while current <= config.max_threshold + epsilon:
        thresholds.append(round(current, 2))
        current += config.step_size
    return thresholds

def run_sweep(config: SweepConfig, output_dir: str) -> Dict[str, Any]:
    """
    Execute the full sweep across tiers and thresholds.
    
    This function:
    1. Generates the list of thresholds (0.0 to 1.0 in 0.1 steps)
    2. Iterates through each tier
    3. For each tier, iterates through each threshold
    4. Runs the specified number of episodes for each (tier, threshold) pair
    5. Collects and aggregates results
    
    Args:
        config: SweepConfig with all parameters.
        output_dir: Directory to write results.
        
    Returns:
        Dictionary containing aggregated results and metadata.
    """
    logger = get_experiment_logger("sweep")
    logger.info(f"Starting sweep with config: {config}")
    
    # Ensure output directory exists
    ensure_directories(output_dir)
    
    # Generate thresholds
    thresholds = generate_thresholds(config)
    logger.info(f"Generated thresholds: {thresholds}")
    
    # Initialize seed
    set_seed(config.seed)
    
    # Results storage
    all_results = []
    summary_stats = {}
    
    # Initialize components
    graph_gen = GraphGenerator()
    
    # Path for CSV output
    csv_path = os.path.join(output_dir, "sweep_results.csv")
    
    with open(csv_path, mode='w', newline='') as csvfile:
        fieldnames = ['tier', 'threshold', 'episode_id', 'success', 'entropy', 
                     'nodes', 'edges', 'path_length', 'injection_count']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for tier_name in config.tiers:
            logger.info(f"Processing tier: {tier_name}")
            
            tier_results = []
            
            for threshold in thresholds:
                logger.info(f"  Running threshold: {threshold:.2f}")
                
                # Create router for this threshold
                router = OPIDRouter(routing_threshold=threshold, seed=config.seed)
                
                # Create baseline policy
                policy = create_baseline_policy(seed=config.seed)
                
                # Generate a graph for this tier
                # Note: In a real scenario, we might generate a new graph per episode
                # or reuse one. Here we generate one per threshold for consistency
                graph = graph_gen.generate(tier=tier_name, seed=config.seed)
                
                if not graph.is_valid():
                    logger.warning(f"Generated invalid graph for {tier_name} at threshold {threshold}")
                    continue
                
                tier_stats = {
                    'successes': 0,
                    'total_episodes': 0,
                    'total_entropy': 0.0,
                    'total_injections': 0
                }
                
                for episode_id in range(config.episodes_per_setting):
                    # Run a single episode
                    # Reset seed for reproducibility within the episode
                    set_seed(config.seed + episode_id)
                    
                    # Generate episode trajectory
                    # This is a simplified version - the real implementation
                    # would use the full ExperimentRunner logic
                    trajectory = []
                    current_node = graph.start
                    goal_reached = False
                    injection_count = 0
                    actions = []
                    
                    # Simple episode simulation
                    steps = 0
                    max_steps = 100  # Prevent infinite loops
                    
                    while current_node != graph.goal and steps < max_steps:
                        # Get possible actions (edges)
                        possible_actions = []
                        for edge in graph.edges:
                            if edge.from_node == current_node:
                                possible_actions.append(edge)
                        
                        if not possible_actions:
                            break
                        
                        # Decide whether to inject
                        should_inject = router.should_inject(current_node)
                        if should_inject:
                            injection_count += 1
                            
                        # Select action (simplified - real implementation uses policy)
                        selected_edge = possible_actions[0]  # Default to first
                        if should_inject and possible_actions:
                            # Inject skill signal: prefer edge towards goal if known
                            # For now, just pick the first edge that moves forward
                            for edge in possible_actions:
                                if edge.to_node == graph.goal or edge.to_node in graph.nodes:
                                    selected_edge = edge
                                    break
                        
                        # Move to next node
                        current_node = selected_edge.to_node
                        actions.append(selected_edge.action if hasattr(selected_edge, 'action') else 0)
                        trajectory.append({
                            'node': current_node,
                            'action': selected_edge.action if hasattr(selected_edge, 'action') else 0,
                            'injected': should_inject
                        })
                        steps += 1
                    
                    goal_reached = (current_node == graph.goal)
                    
                    # Calculate metrics
                    success = 1 if goal_reached else 0
                    entropy = calculate_action_entropy(actions) if actions else 0.0
                    
                    # Update stats
                    tier_stats['successes'] += success
                    tier_stats['total_episodes'] += 1
                    tier_stats['total_entropy'] += entropy
                    tier_stats['total_injections'] += injection_count
                    
                    # Write to CSV
                    writer.writerow({
                        'tier': tier_name,
                        'threshold': f"{threshold:.2f}",
                        'episode_id': episode_id,
                        'success': success,
                        'entropy': entropy,
                        'nodes': len(graph.nodes),
                        'edges': len(graph.edges),
                        'path_length': steps,
                        'injection_count': injection_count
                    })
                    
                    all_results.append({
                        'tier': tier_name,
                        'threshold': threshold,
                        'success': success,
                        'entropy': entropy,
                        'nodes': len(graph.nodes),
                        'edges': len(graph.edges),
                        'path_length': steps,
                        'injection_count': injection_count
                    })
                
                # Calculate tier-level stats
                if tier_stats['total_episodes'] > 0:
                    success_rate = tier_stats['successes'] / tier_stats['total_episodes']
                    avg_entropy = tier_stats['total_entropy'] / tier_stats['total_episodes']
                    avg_injections = tier_stats['total_injections'] / tier_stats['total_episodes']
                    
                    summary_stats[f"{tier_name}_threshold_{threshold:.2f}"] = {
                        'success_rate': success_rate,
                        'avg_entropy': avg_entropy,
                        'avg_injections': avg_injections,
                        'total_episodes': tier_stats['total_episodes']
                    }
                    
                    logger.info(f"    Tier {tier_name}, Threshold {threshold:.2f}: "
                                f"Success Rate={success_rate:.4f}, Avg Entropy={avg_entropy:.4f}")
    
    logger.info(f"Sweep complete. Results written to {csv_path}")
    
    return {
        'config': config,
        'thresholds': thresholds,
        'results': all_results,
        'summary': summary_stats,
        'csv_path': csv_path
    }

def main():
    """Main entry point for the sweep logic."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run OPID parameter sweep")
    parser.add_argument("--min-threshold", type=float, default=0.0, help="Minimum threshold")
    parser.add_argument("--max-threshold", type=float, default=1.0, help="Maximum threshold")
    parser.add_argument("--step-size", type=float, default=0.1, help="Step size between thresholds")
    parser.add_argument("--episodes", type=int, default=100, help="Episodes per setting (small default for testing)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Output directory")
    
    args = parser.parse_args()
    
    config = SweepConfig(
        min_threshold=args.min_threshold,
        max_threshold=args.max_threshold,
        step_size=args.step_size,
        episodes_per_setting=args.episodes,
        seed=args.seed
    )
    
    results = run_sweep(config, args.output_dir)
    
    # Print summary
    print(f"\nSweep Complete!")
    print(f"Total episodes run: {len(results['results'])}")
    print(f"Results saved to: {results['csv_path']}")
    
    return results

if __name__ == "__main__":
    main()