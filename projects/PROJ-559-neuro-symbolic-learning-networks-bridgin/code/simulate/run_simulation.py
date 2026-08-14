import os
import sys
import json
import logging
import random
import time
import argparse
import pandas as pd
from typing import Dict, Any, List, Optional

from simulate.bkt_simulator import BKTSimulator
from simulate.response_metrics import generate_response_metrics
from simulate.validate_rt_distribution import validate_rt_distribution

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: str = 'code/simulate/simulation_config.yaml') -> Dict[str, Any]:
    """Load simulation configuration from YAML file."""
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = {}
        current_section = None
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.endswith(':') and ':' not in line[:-1]:
                current_section = line[:-1]
                config[current_section] = {}
            elif current_section and ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                # Try to convert to int/float
                try:
                    if '.' in value:
                        config[current_section][key] = float(value)
                    else:
                        config[current_section][key] = int(value)
                except ValueError:
                    config[current_section][key] = value
        return config

def check_calibration(calibration_path: str = 'data/pilot/calibration_report.json') -> bool:
    """Check if calibration is valid."""
    if not os.path.exists(calibration_path):
        logger.error("Calibration report not found. Run calibration first.")
        return False
    
    try:
        with open(calibration_path, 'r') as f:
            report = json.load(f)
        # Check for the specific flag set by calibration logic
        return report.get('calibration_valid', False)
    except Exception as e:
        logger.error(f"Error reading calibration report: {e}")
        return False

def check_rt_distribution_valid(validation_path: str = 'data/derived/rt_distribution_validation.json') -> bool:
    """Check if RT distribution validation passed."""
    if not os.path.exists(validation_path):
        logger.error("RT distribution validation file not found. Run T023 first.")
        return False
    
    try:
        with open(validation_path, 'r') as f:
            validation = json.load(f)
        return validation.get('valid', False)
    except Exception as e:
        logger.error(f"Error reading RT distribution validation: {e}")
        return False

def generate_student_id() -> str:
    """Generate a unique student ID."""
    return f"STU-{random.randint(10000, 99999)}"

def run_simulation_for_condition(
    condition: str,
    num_students: int,
    problem_id: str,
    explanation_artifacts: Dict[str, str],
    bkt_params: Dict[str, float],
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Run simulation for a single condition."""
    if seed is not None:
        random.seed(seed)
    
    logs = []
    simulator = BKTSimulator(bkt_params)
    
    for i in range(num_students):
        student_id = generate_student_id()
        state = simulator.simulate_student(problem_id)
        
        log = {
            'student_id': student_id,
            'condition': condition,
            'problem_id': problem_id,
            'explanation_type': condition,
            'correct': state['correct'],
            'attempts': state['attempts'],
            'learning_occurred': state['learning_occurred'],
            'final_knowledge': round(state['knowledge'], 3),
            'timestamp': time.time(),
            'rt_seconds': None,  # Will be filled by response_metrics
            'comprehension_rating': None  # Will be filled by response_metrics
        }
        logs.append(log)
    
    return logs

def main():
    """Main entry point for running the simulation."""
    parser = argparse.ArgumentParser(description='Run student simulation')
    parser.add_argument('--config', type=str, default='code/simulate/simulation_config.yaml', help='Config file path')
    parser.add_argument('--output', type=str, default='data/derived/simulation_logs.csv', help='Output CSV path')
    parser.add_argument('--seed', type=int, default=None, help='Random seed')
    
    args = parser.parse_args()
    
    # Check calibration (T033b dependency)
    if not check_calibration():
        logger.error("Calibration check failed. Cannot proceed with simulation.")
        sys.exit(1)
    
    logger.info("Calibration check passed.")

    # Check RT distribution validation (T023 dependency)
    # Note: In a strict pipeline, T023 runs after T022 (initial logs). 
    # However, per T021 task description: "T021 will not start if T023 exits with code 1".
    # This implies a pre-check or a loop. Since T022 generates the logs T023 checks,
    # and T021 calls T022 (via generate_response_metrics), we assume T023 has run 
    # on a previous iteration or we are in a setup phase where T023 passed.
    # If T023 is meant to block the *entire* run before any simulation, we check here.
    if not check_rt_distribution_valid():
        logger.error("RT distribution validation failed (T023). Simulation blocked.")
        sys.exit(1)
    
    logger.info("RT distribution validation passed.")
    
    # Load config
    config = load_config(args.config)
    
    # Get simulation parameters
    conditions = config.get('conditions', ['neural', 'symbolic', 'neuro_symbolic'])
    # FR-009: Process at least 2,000 students per condition
    sample_size = config.get('sample_size_per_condition', 2000)
    if sample_size < 2000:
        logger.warning(f"Config sample_size ({sample_size}) is less than FR-009 requirement (2000). Enforcing 2000.")
        sample_size = 2000
        
    problem_id = config.get('problem_id', 'PROB-001')
    bkt_params = config.get('bkt_params', {
        'initial_knowledge': 0.3,
        'learn': 0.3,
        'guess': 0.2,
        'slip': 0.1
    })
    
    # Load explanation artifacts
    explanation_artifacts = {
        'neural': 'data/explanations/explanation_neural.txt',
        'symbolic': 'data/explanations/explanation_symbolic.txt',
        'neuro_symbolic': 'data/explanations/explanation_neuro_symbolic.txt'
    }
    
    # Verify artifact existence (optional but good practice)
    for key, path in explanation_artifacts.items():
        if not os.path.exists(path):
            logger.warning(f"Explanation artifact missing for {key}: {path}")
    
    # Run simulation for each condition
    all_logs = []
    for condition in conditions:
        logger.info(f"Running simulation for condition: {condition} (N={sample_size})")
        logs = run_simulation_for_condition(
            condition=condition,
            num_students=sample_size,
            problem_id=problem_id,
            explanation_artifacts=explanation_artifacts,
            bkt_params=bkt_params,
            seed=args.seed
        )
        all_logs.extend(logs)
        logger.info(f"Generated {len(logs)} logs for {condition}")
    
    # Generate response metrics (T022 logic integrated here to produce final CSV)
    logger.info("Generating response metrics (response times and comprehension ratings)...")
    output_path = generate_response_metrics(all_logs, args.output, args.seed)
    
    logger.info(f"Simulation completed. Logs saved to {output_path}")

if __name__ == '__main__':
    main()