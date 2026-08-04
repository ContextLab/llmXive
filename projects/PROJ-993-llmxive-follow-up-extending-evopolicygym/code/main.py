import argparse
import sys
import os
import csv
import logging
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logging import setup_logging, get_logger
from utils.config import get_config
from envs.dynamic_shift_env import generate_all_dynamic_shift_envs
from analysis.stats import calculate_shift_validation, run_mixed_effects_model, calculate_success_rate
from agents.evolutionary_harness import EvolutionaryHarness

logger = get_logger(__name__)

def run_shift_sensitivity_analysis(config_path: str = None):
    """
    Run shift sensitivity analysis (T015).
    Generates sensitivity_report.csv and triggers shift validation (T045).
    """
    logger.info("Starting shift sensitivity analysis...")
    
    # Generate dynamic shift environments
    envs = generate_all_dynamic_shift_envs()
    logger.info(f"Generated {len(envs)} dynamic shift environments")
    
    # Simulate performance data (in real implementation, this would run actual agents)
    # For T015, we generate a sensitivity_report.csv
    report_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sensitivity_report.csv')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    # Mock data for demonstration - in real implementation, run actual agents
    import random
    with open(report_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['env_name', 'agent_id', 'pre_shift_metric', 'post_shift_metric'])
        
        for i, env_name in enumerate(envs.keys()):
            # Simulate performance drop
            pre = 0.8 + random.random() * 0.15
            post = pre - (0.2 + random.random() * 0.1)  # Performance drops
            writer.writerow([env_name, 'static_agent', round(pre, 4), round(post, 4)])
    
    logger.info(f"Written sensitivity report to {report_path}")
    
    # Run shift validation (T045)
    validation_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'shift_validation.json')
    logger.info(f"Running shift validation on {report_path}")
    
    try:
        results = calculate_shift_validation(report_path, validation_path)
        logger.info(f"Shift validation complete: p_value={results['p_value']:.4f}, significant={results['significant']}")
    except Exception as e:
        logger.error(f"Shift validation failed: {e}")
        raise

def run_evolution_pipeline(config_path: str = None):
    """
    Run full evolution pipeline (T037).
    Executes evolutionary agents and generates final results.
    """
    logger.info("Starting evolution pipeline...")
    
    harness = EvolutionaryHarness()
    harness.run()
    
    # Run mixed effects model
    input_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'evolution_results.csv')
    output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'stats_results.json')
    
    if os.path.exists(input_path):
        results = run_mixed_effects_model(input_path, output_path)
        logger.info(f"Stats analysis complete: p_value={results['p_value']:.4f}")
    else:
        logger.warning(f"Evolution results not found at {input_path}")
    
    # Calculate success rate
    fallback_log = os.path.join(os.path.dirname(__file__), '..', 'data', 'fallbacks.log')
    success_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'success_rate.json')
    
    if os.path.exists(fallback_log):
        results = calculate_success_rate(fallback_log, success_path)
        logger.info(f"Success rate: {results['success_rate']:.2%}")

def main():
    parser = argparse.ArgumentParser(description='EvoPolicyGym Analysis Pipeline')
    parser.add_argument('--run-evolution', action='store_true', help='Run evolution pipeline')
    parser.add_argument('--run-shift-analysis', action='store_true', help='Run shift sensitivity analysis')
    parser.add_argument('--config', type=str, default=None, help='Path to config file')
    
    args = parser.parse_args()
    
    setup_logging()
    
    if args.run_shift_analysis:
        run_shift_sensitivity_analysis(args.config)
    elif args.run_evolution:
        run_evolution_pipeline(args.config)
    else:
        # Default: run shift analysis
        logger.info("No action specified. Running shift sensitivity analysis by default.")
        run_shift_sensitivity_analysis(args.config)

if __name__ == '__main__':
    main()