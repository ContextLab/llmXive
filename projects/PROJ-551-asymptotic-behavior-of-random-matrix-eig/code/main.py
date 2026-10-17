import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure project root is in path
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from utils.config import ensure_directories
from analysis.simulation_loop import run_single_simulation
from analysis.results_recorder import save_single_run_results
from analysis.simulation_logging import log_simulation_start, log_simulation_end

def parse_args():
    parser = argparse.ArgumentParser(description="Random Matrix Eigenvalue Analysis")
    parser.add_argument('--mode', type=str, choices=['single', 'sweep', 'sensitivity'], default='single')
    parser.add_argument('--N', type=int, default=1000)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--theta', type=float, default=2.5)
    parser.add_argument('--k', type=int, default=1)
    parser.add_argument('--pattern', type=str, default='diagonal')
    parser.add_argument('--output', type=str, default='data/processed/single_run_results.json')
    return parser.parse_args()

def main():
    args = parse_args()
    ensure_directories()
    
    if args.mode == 'single':
        params = {
            'N': args.N,
            'seed': args.seed,
            'theta': args.theta,
            'k': args.k,
            'pattern': args.pattern
        }
        log_simulation_start(params)
        try:
            result = run_single_simulation(params)
            log_simulation_end(result)
            save_single_run_results(result, args.output)
            print(json.dumps(result, indent=2))
            return 0
        except Exception as e:
            logging.error(f"Simulation failed: {e}")
            return 1
    else:
        print(f"Mode {args.mode} not implemented in this task.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
