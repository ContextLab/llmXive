import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.config import get_project_paths, get_outlier_tolerance
from analysis.simulation_loop import run_single_simulation
from analysis.results_recorder import save_single_run_results
from analysis.simulation_logging import log_simulation_start, log_simulation_end

def parse_args():
    parser = argparse.ArgumentParser(description="Main entry point for random matrix eigenvalue analysis")
    parser.add_argument('--config', type=str, default='code/config.json', help='Path to configuration file')
    parser.add_argument('--mode', type=str, choices=['single', 'sweep', 'sensitivity'], default='single',
                        help='Execution mode: single run, parameter sweep, or sensitivity analysis')
    parser.add_argument('--N', type=int, default=1000, help='Matrix dimension')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--theta', type=float, default=2.5, help='Perturbation strength')
    parser.add_argument('--k', type=int, default=1, help='Perturbation rank')
    parser.add_argument('--pattern', type=str, default='diagonal',
                        choices=['diagonal', 'block-sparse', 'random-sparse'],
                        help='Perturbation pattern')
    parser.add_argument('--densities', type=str, default='0.1,0.2,0.3',
                        help='Comma-separated list of support densities for sensitivity analysis')
    parser.add_argument('--iterations', type=int, default=10, help='Number of iterations for sweep')
    parser.add_argument('--output', type=str, default='data/processed/single_run_results.json',
                        help='Output file path')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    return parser.parse_args()

def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/logs/main_execution.log')
        ]
    )

def run_single_mode(args):
    """Run a single simulation instance."""
    logger = logging.getLogger(__name__)
    
    params = {
        'N': args.N,
        'seed': args.seed,
        'theta': args.theta,
        'k': args.k,
        'pattern': args.pattern
    }
    
    logger.info(f"Running single simulation with params: {params}")
    
    # Log simulation start
    log_simulation_start(params)
    
    # Run simulation
    result = run_single_simulation(params)
    
    # Log simulation end
    log_simulation_end(result)
    
    # Save results
    save_single_run_results(result, args.output)
    
    logger.info(f"Results saved to {args.output}")
    return result

def run_sweep_mode(args):
    """Run a parameter sweep over theta values."""
    logger = logging.getLogger(__name__)
    
    # Define theta sweep
    theta_values = [1.5, 2.0, 2.5, 3.0, 3.5]
    results = []
    
    logger.info(f"Starting theta sweep with {len(theta_values)} values")
    
    for theta in theta_values:
        params = {
            'N': args.N,
            'seed': args.seed,
            'theta': theta,
            'k': args.k,
            'pattern': args.pattern
        }
        
        logger.info(f"Running simulation with theta={theta}")
        result = run_single_simulation(params)
        results.append(result)
        
        # Save each result
        output_path = args.output.replace('.json', f'_theta{theta}.json')
        save_single_run_results(result, output_path)
    
    logger.info(f"Sweep complete. {len(results)} results generated.")
    return results

def run_sensitivity_mode(args):
    """Run a sensitivity analysis over support densities."""
    logger = logging.getLogger(__name__)
    
    # Parse densities
    densities = [float(d.strip()) for d in args.densities.split(',')]
    results = []
    
    logger.info(f"Starting sensitivity analysis with densities: {densities}")
    
    for density in densities:
        params = {
            'N': args.N,
            'seed': args.seed,
            'theta': args.theta,
            'k': args.k,
            'pattern': args.pattern,
            'support_density': density
        }
        
        logger.info(f"Running simulation with density={density}")
        result = run_single_simulation(params)
        results.append(result)
        
        # Save each result
        output_path = args.output.replace('.json', f'_density{density}.json')
        save_single_run_results(result, output_path)
    
    logger.info(f"Sensitivity analysis complete. {len(results)} results generated.")
    return results

def main():
    args = parse_args()
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Get project paths and ensure directories exist
        paths = get_project_paths()
        for path in paths.values():
            Path(path).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Project paths configured: {paths}")

        # Execute requested mode
        if args.mode == 'single':
            logger.info("Executing single simulation mode")
            result = run_single_mode(args)
            print(json.dumps(result, indent=2))
        
        elif args.mode == 'sweep':
            logger.info("Executing parameter sweep mode")
            results = run_sweep_mode(args)
            print(f"Sweep complete. {len(results)} results generated.")
        
        elif args.mode == 'sensitivity':
            logger.info("Executing sensitivity analysis mode")
            results = run_sensitivity_mode(args)
            print(f"Sensitivity analysis complete. {len(results)} results generated.")
        
        else:
            logger.error(f"Unknown mode: {args.mode}")
            return 1
        
        return 0

    except Exception as e:
        logger.error(f"Execution failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())