import argparse
import sys
import os
import json
import logging
from typing import List, Optional

# Ensure project root is in path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logging import setup_logging, get_logger
from utils.config import get_config
from analysis.run_shift_sensitivity import main as run_shift_analysis_main
from analysis.shift_validation import main as run_shift_validation_main
from agents.evolutionary_harness import EvolutionaryHarness
from analysis.stats import main as run_stats_analysis_main
from envs.dynamic_shift_env import generate_all_dynamic_shift_envs
from utils.env_discovery import run_discovery

logger = get_logger(__name__)

def run_shift_sensitivity_analysis(args):
    """Execute the shift sensitivity analysis (T013f, T015c)."""
    logger.info("Starting Shift Sensitivity Analysis...")
    # T013d: Ensure environments are discovered
    if not os.path.exists("data/discovered_envs.json"):
        logger.info("Discovered environments missing. Running discovery...")
        run_discovery()
    
    # Run the sensitivity analysis script logic
    run_shift_analysis_main()
    logger.info("Shift Sensitivity Analysis complete.")

def run_shift_validation(args):
    """Execute shift validation and p-value calculation (T014)."""
    logger.info("Starting Shift Validation...")
    if not os.path.exists("data/sensitivity_report.csv"):
        raise FileNotFoundError("sensitivity_report.csv not found. Run shift analysis first.")
    run_shift_validation_main()
    logger.info("Shift Validation complete.")

def run_evolution_pipeline(args):
    """Execute the evolutionary harness pipeline (T032a, T032b, T033, T034, T035)."""
    logger.info("Starting Evolution Pipeline...")
    
    # Pre-flight checks
    if not os.path.exists("data/sensitivity_report.csv"):
        raise FileNotFoundError("sensitivity_report.csv not found. Run shift analysis first.")
    
    # Load config
    config = get_config()
    seeds = args.seeds if args.seeds else config.get('seeds', [42])
    runs = args.runs if args.runs else config.get('runs', 5)
    envs = args.envs if args.envs else config.get('envs', None)
    conditions = args.conditions if args.conditions else config.get('conditions', ['baseline', 'counterfactual'])

    # Initialize Harness
    harness = EvolutionaryHarness(
        seeds=seeds,
        runs_per_seed=runs,
        env_ids=envs,
        conditions=conditions
    )
    
    # Run evolution
    harness.run()
    
    logger.info("Evolution Pipeline complete.")

def run_stats_analysis(args):
    """Execute statistical analysis (T036)."""
    logger.info("Starting Statistical Analysis...")
    if not os.path.exists("data/evolution_results.csv"):
        raise FileNotFoundError("evolution_results.csv not found. Run evolution pipeline first.")
    run_stats_analysis_main()
    logger.info("Statistical Analysis complete.")

def run_full_pipeline(args):
    """Orchestrate the full pipeline: Shift -> Validation -> Evolution -> Stats."""
    logger.info("Starting Full Pipeline...")
    
    # 1. Shift Analysis
    run_shift_sensitivity_analysis(args)
    
    # 2. Validation
    run_shift_validation(args)
    
    # 3. Evolution
    run_evolution_pipeline(args)
    
    # 4. Stats
    run_stats_analysis(args)
    
    logger.info("Full Pipeline complete.")

def main():
    parser = argparse.ArgumentParser(description="llmXive Follow-up: EvoPolicyGym Extension Pipeline")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Global args that might be used by all
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to config file')
    parser.add_argument('--seeds', type=int, nargs='+', help='Random seeds to use')
    parser.add_argument('--runs', type=int, help='Number of runs per seed')
    parser.add_argument('--envs', type=str, nargs='+', help='Specific environment IDs to target')
    parser.add_argument('--conditions', type=str, nargs='+', help='Conditions to evaluate (baseline, counterfactual)')

    # Subcommand: Shift Analysis
    parser_shift = subparsers.add_parser('run-shift-analysis', help='Run shift sensitivity analysis')
    
    # Subcommand: Validation
    parser_val = subparsers.add_parser('run-shift-validation', help='Run shift validation')

    # Subcommand: Evolution
    parser_evo = subparsers.add_parser('run-evolution', help='Run evolutionary harness')

    # Subcommand: Stats
    parser_stats = subparsers.add_parser('run-stats', help='Run statistical analysis')

    # Subcommand: Full
    parser_full = subparsers.add_parser('run-full', help='Run full pipeline')

    args = parser.parse_args()

    # Setup logging
    setup_logging(level=logging.INFO)

    if args.command == 'run-shift-analysis':
        run_shift_sensitivity_analysis(args)
    elif args.command == 'run-shift-validation':
        run_shift_validation(args)
    elif args.command == 'run-evolution':
        run_evolution_pipeline(args)
    elif args.command == 'run-stats':
        run_stats_analysis(args)
    elif args.command == 'run-full':
        run_full_pipeline(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()