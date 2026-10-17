import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.config import get_project_paths, ensure_directories
from analysis.simulation_loop import run_single_simulation
from analysis.results_recorder import save_single_run_results
from analysis.simulation_logging import log_simulation_start, log_simulation_end

def parse_args():
    parser = argparse.ArgumentParser(description="Main entry point for random matrix eigenvalue analysis")
    parser.add_argument('--mode', type=str, choices=['single', 'sweep', 'sensitivity'], default='single')
    parser.add_argument('--N', type=int, default=1000)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--theta', type=float, default=2.5)
    parser.add_argument('--k', type=int, default=1)
    parser.add_argument('--pattern', type=str, default='diagonal')
    parser.add_argument('--output', type=str, default='data/processed/single_run_results.json')
    parser.add_argument('--verbose', action='store_true')
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
    logger = logging.getLogger(__name__)
    params = {
        'N': args.N,
        'seed': args.seed,
        'theta': args.theta,
        'k': args.k,
        'pattern': args.pattern
    }
    logger.info(f"Running single simulation with params: {params}")
    log_simulation_start(params)
    result = run_single_simulation(params)
    log_simulation_end(result)
    save_single_run_results(result, args.output)
    logger.info(f"Results saved to {args.output}")
    return result

def main():
    args = parse_args()
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        ensure_directories()
        if args.mode == 'single':
            result = run_single_mode(args)
            print(json.dumps(result, indent=2))
        else:
            logger.error(f"Mode {args.mode} not implemented in this task version.")
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
