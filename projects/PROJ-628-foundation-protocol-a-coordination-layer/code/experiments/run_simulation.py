import os
import sys
import json
import logging
import argparse
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Project imports
from foundation_protocol.direct_comm import create_direct_comm_agent
from foundation_protocol.middleware import create_middleware_agent
from benchmarks.hanabi_runner import run_hanabi_benchmark
from benchmarks.spear_runner import run_spear_benchmark
from benchmarks.resource_alloc_runner import run_resource_allocation_benchmark
from experiments.crash_injector import create_crash_injector
from foundation_protocol.utils import log_seed, get_hash
from data.generate_seeds import generate_seed_pool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/experiment.log')
    ]
)
logger = logging.getLogger(__name__)

def run_single_seed(
    seed: int,
    protocol: str,
    task: str,
    crash_fraction: float = 0.0,
    crash_type: str = "single"
) -> Dict[str, Any]:
    """
    Run a single seed for a specific protocol and task.

    Args:
        seed: Random seed for reproducibility
        protocol: Either 'foundation' or 'native_direct'
        task: Either 'hanabi', 'spear', or 'resource_alloc'
        crash_fraction: Fraction of agents to crash (for SPEAR)
        crash_type: 'single' or 'simultaneous' (for SPEAR)

    Returns:
        Dictionary containing metrics and metadata
    """
    logger.info(f"Running seed={seed}, protocol={protocol}, task={task}")
    
    # Set random seeds
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)
    
    # Initialize protocol agents
    if protocol == 'foundation':
        agent_factory = create_middleware_agent
    else:
        agent_factory = create_direct_comm_agent
    
    # Initialize crash injector if needed (only for SPEAR)
    crash_injector = None
    if task == 'spear' and crash_fraction > 0:
        crash_injector = create_crash_injector(
            crash_fraction=crash_fraction,
            crash_type=crash_type,
            seed=seed
        )
    
    # Run the appropriate benchmark
    start_time = time.time()
    
    try:
        if task == 'hanabi':
            results = run_hanabi_benchmark(
                agent_factory=agent_factory,
                seed=seed,
                num_episodes=10,  # Reduced for testing
                protocol=protocol
            )
        elif task == 'spear':
            results = run_spear_benchmark(
                agent_factory=agent_factory,
                seed=seed,
                num_episodes=10,  # Reduced for testing
                crash_injector=crash_injector,
                protocol=protocol
            )
        elif task == 'resource_alloc':
            results = run_resource_allocation_benchmark(
                agent_factory=agent_factory,
                seed=seed,
                num_episodes=10,  # Reduced for testing
                protocol=protocol
            )
        else:
            raise ValueError(f"Unknown task: {task}")
        
        end_time = time.time()
        
        # Prepare result
        result = {
            'seed': seed,
            'protocol': protocol,
            'task': task,
            'execution_time': end_time - start_time,
            'metrics': results,
            'status': 'success'
        }
        
        logger.info(f"Completed seed={seed}: {len(results)} episodes processed")
        return result
        
    except Exception as e:
        logger.error(f"Error running seed={seed}, protocol={protocol}, task={task}: {str(e)}")
        return {
            'seed': seed,
            'protocol': protocol,
            'task': task,
            'status': 'failed',
            'error': str(e)
        }

def run_simulation(
    seeds: List[int],
    protocols: List[str],
    tasks: List[str],
    output_dir: str = 'results',
    crash_fraction: float = 0.0,
    crash_type: str = "single"
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run the full simulation across seeds, protocols, and tasks.

    Args:
        seeds: List of random seeds to run
        protocols: List of protocols to test ('foundation', 'native_direct')
        tasks: List of tasks to run ('hanabi', 'spear', 'resource_alloc')
        output_dir: Directory to save results
        crash_fraction: Fraction of agents to crash (for SPEAR)
        crash_type: 'single' or 'simultaneous' (for SPEAR)

    Returns:
        Dictionary mapping task names to lists of results
    """
    os.makedirs(output_dir, exist_ok=True)
    
    all_results = {task: [] for task in tasks}
    
    total_combinations = len(seeds) * len(protocols) * len(tasks)
    combination_count = 0
    
    for task in tasks:
        for protocol in protocols:
            # Adjust crash parameters for non-SPEAR tasks
            effective_crash_fraction = crash_fraction if task == 'spear' else 0.0
            
            for seed in seeds:
                combination_count += 1
                logger.info(f"Progress: {combination_count}/{total_combinations}")
                
                result = run_single_seed(
                    seed=seed,
                    protocol=protocol,
                    task=task,
                    crash_fraction=effective_crash_fraction,
                    crash_type=crash_type
                )
                
                if result['status'] == 'success':
                    all_results[task].append(result)
                else:
                    logger.warning(f"Seed {seed} failed for {protocol}/{task}")
    
    # Save individual results
    for task, task_results in all_results.items():
        output_path = os.path.join(output_dir, f"{task}_results.json")
        with open(output_path, 'w') as f:
            json.dump(task_results, f, indent=2)
        logger.info(f"Saved {len(task_results)} results to {output_path}")
    
    # Save summary
    summary = {
        'total_seeds': len(seeds),
        'protocols': protocols,
        'tasks': tasks,
        'crash_fraction': crash_fraction,
        'crash_type': crash_type,
        'results_by_task': {
            task: len(results) for task, results in all_results.items()
        }
    }
    
    summary_path = os.path.join(output_dir, 'simulation_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Simulation complete. Summary saved to {summary_path}")
    return all_results

def main():
    """Main entry point for running simulations."""
    parser = argparse.ArgumentParser(description='Run Foundation Protocol simulations')
    parser.add_argument('--seeds', type=int, nargs='+', default=list(range(30)),
                      help='List of seeds to run (default: 0-29)')
    parser.add_argument('--protocols', type=str, nargs='+', 
                      choices=['foundation', 'native_direct'],
                      default=['foundation', 'native_direct'],
                      help='Protocols to test')
    parser.add_argument('--tasks', type=str, nargs='+',
                      choices=['hanabi', 'spear', 'resource_alloc'],
                      default=['hanabi', 'spear', 'resource_alloc'],
                      help='Tasks to run')
    parser.add_argument('--output-dir', type=str, default='results',
                      help='Output directory for results')
    parser.add_argument('--crash-fraction', type=float, default=0.0,
                      help='Fraction of agents to crash (for SPEAR)')
    parser.add_argument('--crash-type', type=str, default='single',
                      choices=['single', 'simultaneous'],
                      help='Type of crash injection')
    parser.add_argument('--seed-config', type=str, default=None,
                      help='Path to seed configuration file')
    
    args = parser.parse_args()
    
    # Load seeds from config if provided
    if args.seed_config:
        logger.info(f"Loading seeds from {args.seed_config}")
        with open(args.seed_config, 'r') as f:
            config = json.load(f)
            args.seeds = config.get('seeds', args.seeds)
    
    logger.info(f"Starting simulation with {len(args.seeds)} seeds")
    logger.info(f"Protocols: {args.protocols}")
    logger.info(f"Tasks: {args.tasks}")
    logger.info(f"Crash fraction: {args.crash_fraction}, Type: {args.crash_type}")
    
    results = run_simulation(
        seeds=args.seeds,
        protocols=args.protocols,
        tasks=args.tasks,
        output_dir=args.output_dir,
        crash_fraction=args.crash_fraction,
        crash_type=args.crash_type
    )
    
    logger.info("Simulation completed successfully")
    return 0

if __name__ == '__main__':
    sys.exit(main())