"""
Execution script for T016: Run CA vs Neural Baseline comparison.

Executes a minimum of 10,000 time-steps for both the Eco-Director (CA)
and Neural Baseline simulations, logging step_latency and other metrics
to data/raw/baseline_comparison_results.csv.

Requirements:
- T004 (eco_director.py)
- T005 (neural_baseline.py)
- T010 (logging infrastructure)
- T013 (throttling logic)
- T014/T015 (memory/time enforcement)
"""
import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional

import pandas as pd
import numpy as np

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import project modules
from src.sim.eco_director import EcoDirector
from src.sim.neural_baseline import NeuralBaseline
from src.data_models import SimulationRun, MetricRecord
from src.config import get_config, set_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_root, 'data', 'logs', 'comparison_run.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('baseline_comparison')

def run_single_simulation(
    simulator_name: str,
    simulator_class: Any,
    config: Dict[str, Any],
    steps: int,
    run_id: str
) -> List[Dict[str, Any]]:
    """
    Run a single simulation and collect metrics.
    
    Args:
        simulator_name: Name of the simulator (CA or Neural)
        simulator_class: Class to instantiate
        config: Configuration dictionary
        steps: Number of time-steps to run
        run_id: Unique identifier for this run
        
    Returns:
        List of metric records
    """
    logger.info(f"Starting {simulator_name} simulation for {steps} steps")
    
    # Initialize simulator
    simulator = simulator_class(config)
    
    metrics = []
    start_time = time.time()
    
    try:
        for step in range(steps):
            step_start = time.time()
            
            # Run one step
            state, metrics_step = simulator.step()
            
            # Calculate step latency
            step_latency = time.time() - step_start
            
            # Create metric record
            record = {
                'run_id': run_id,
                'simulator': simulator_name,
                'step': step,
                'timestamp': datetime.now().isoformat(),
                'step_latency': step_latency,
                'coherence_score': metrics_step.get('coherence_score', 0.0),
                'diversity_score': metrics_step.get('diversity_score', 0.0),
                'memory_usage_mb': metrics_step.get('memory_usage_mb', 0.0),
                'state_valid': metrics_step.get('state_valid', True),
                'converged': metrics_step.get('converged', False)
            }
            
            metrics.append(record)
            
            # Log progress every 1000 steps
            if (step + 1) % 1000 == 0:
                elapsed = time.time() - start_time
                avg_latency = np.mean([m['step_latency'] for m in metrics])
                logger.info(
                    f"{simulator_name} Step {step+1}/{steps} - "
                    f"Avg Latency: {avg_latency:.6f}s - "
                    f"Elapsed: {elapsed:.2f}s"
                )
                
            # Check for early termination (state explosion)
            if not record['state_valid']:
                logger.warning(f"{simulator_name} state invalid at step {step}")
                break
                
    except Exception as e:
        logger.error(f"{simulator_name} simulation failed at step {step}: {str(e)}")
        raise
        
    total_time = time.time() - start_time
    logger.info(f"{simulator_name} completed in {total_time:.2f}s")
    
    return metrics

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Run CA vs Neural Baseline comparison')
    parser.add_argument('--steps', type=int, default=10000, help='Number of steps per simulation')
    parser.add_argument('--config', type=str, default='src/config.yaml', help='Path to config file')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()
    
    # Set seed for reproducibility
    set_seed(args.seed)
    
    # Load configuration
    config = get_config(args.config)
    
    # Create output directory
    output_dir = os.path.join(project_root, 'data', 'raw')
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate unique run ID
    run_id = f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    all_metrics = []
    start_time = time.time()
    
    try:
        # Run CA (Eco-Director) simulation
        ca_metrics = run_single_simulation(
            'CA',
            EcoDirector,
            config.get('eco_director', {}),
            args.steps,
            f"{run_id}_ca"
        )
        all_metrics.extend(ca_metrics)
        
        # Run Neural Baseline simulation
        neural_metrics = run_single_simulation(
            'Neural',
            NeuralBaseline,
            config.get('neural_baseline', {}),
            args.steps,
            f"{run_id}_neural"
        )
        all_metrics.extend(neural_metrics)
        
        # Convert to DataFrame
        df = pd.DataFrame(all_metrics)
        
        # Save results
        output_file = os.path.join(output_dir, 'baseline_comparison_results.csv')
        df.to_csv(output_file, index=False)
        
        logger.info(f"Results saved to {output_file}")
        logger.info(f"Total records: {len(df)}")
        logger.info(f"CA steps: {len(df[df['simulator'] == 'CA'])}")
        logger.info(f"Neural steps: {len(df[df['simulator'] == 'Neural'])}")
        
        # Summary statistics
        summary = {
            'run_id': run_id,
            'total_steps': len(df),
            'ca_steps': len(df[df['simulator'] == 'CA']),
            'neural_steps': len(df[df['simulator'] == 'Neural']),
            'avg_ca_latency': df[df['simulator'] == 'CA']['step_latency'].mean(),
            'avg_neural_latency': df[df['simulator'] == 'Neural']['step_latency'].mean(),
            'ca_avg_coherence': df[df['simulator'] == 'CA']['coherence_score'].mean(),
            'neural_avg_coherence': df[df['simulator'] == 'Neural']['coherence_score'].mean(),
            'execution_time': time.time() - start_time
        }
        
        summary_file = os.path.join(output_dir, 'comparison_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        logger.info(f"Summary saved to {summary_file}")
        logger.info(f"CA Avg Latency: {summary['avg_ca_latency']:.6f}s")
        logger.info(f"Neural Avg Latency: {summary['avg_neural_latency']:.6f}s")
        
    except Exception as e:
        logger.error(f"Comparison run failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()