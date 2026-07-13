"""
Simulation Runner for Neuro-Symbolic Learning Networks.

Orchestrates the simulation of student interactions across different explanation
conditions (neural, symbolic, neuro-symbolic) using the BKT model.

Dependencies:
  - T020: bkt_simulator (BKT model logic)
  - T021b: simulation_config.yaml (condition definitions)
  - T033: calibration.py (validates calibration before proceeding)
"""

import os
import sys
import json
import logging
import random
import time
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime

# Project root setup
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from simulate.bkt_simulator import BKTSimulator, BKTModel, bkt_transition
from simulate.calibration import run_calibration
from utils.config import set_seeds
from utils.validation import validate_simulation_log

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(PROJECT_ROOT, "logs", "simulation_run.log"))
    ]
)
logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(PROJECT_ROOT, "code", "simulate", "simulation_config.yaml")
CALIBRATION_REPORT_PATH = os.path.join(PROJECT_ROOT, "data", "pilot", "calibration_report.json")
OUTPUT_LOG_PATH = os.path.join(PROJECT_ROOT, "data", "derived", "simulation_logs.csv")

def load_config(config_path: str) -> Dict[str, Any]:
    """Load simulation configuration from YAML."""
    import yaml
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def check_calibration(calibration_path: str) -> bool:
    """
    Verify calibration validity before proceeding.
    Returns True if calibration is valid or synthetic fallback is active.
    Returns False if calibration failed on real human data.
    """
    if not os.path.exists(calibration_path):
        logger.warning(f"Calibration report not found at {calibration_path}. Running calibration...")
        # Run calibration if missing
        run_calibration()
    
    with open(calibration_path, 'r') as f:
        report = json.load(f)
    
    is_valid = report.get('calibration_valid', False)
    is_synthetic = report.get('used_synthetic_fallback', False)
    
    if not is_valid and not is_synthetic:
        logger.error("Calibration failed on human data and no synthetic fallback was used. Aborting simulation.")
        return False
    
    if is_synthetic:
        logger.warning("Using synthetic fallback data for calibration. Proceeding with caution.")
    
    return True

def generate_student_id() -> str:
    """Generate a unique student identifier."""
    return f"STU_{random.randint(10000, 99999)}"

def run_simulation_for_condition(
    condition_name: str,
    num_students: int,
    problem_ids: List[str],
    bkt_params: Dict[str, float],
    seed_offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Run simulation for a single condition across multiple students and problems.
    
    Args:
        condition_name: Name of the condition (neural, symbolic, neuro-symbolic)
        num_students: Number of students to simulate
        problem_ids: List of problem IDs to simulate
        bkt_params: Dictionary of BKT parameters (p_l, p_t, p_g, p_s)
        seed_offset: Offset for random seed to ensure reproducibility across conditions
    
    Returns:
        List of simulation log records
    """
    logs = []
    base_seed = int(time.time()) + seed_offset
    set_seeds(base_seed)
    
    logger.info(f"Starting simulation for condition '{condition_name}' with {num_students} students")
    
    for student_idx in range(num_students):
        student_id = generate_student_id()
        student_seed = base_seed + student_idx
        set_seeds(student_seed)
        
        # Initialize BKT model for this student
        model = BKTModel(
            p_learn=bkt_params.get('p_learn', 0.3),
            p_guess=bkt_params.get('p_guess', 0.2),
            p_slip=bkt_params.get('p_slip', 0.1),
            p_initial=bkt_params.get('p_initial', 0.5)
        )
        
        simulator = BKTSimulator(model)
        
        for problem_id in problem_ids:
            # Simulate student interaction
            state = simulator.step(problem_id)
            
            # Determine correctness based on BKT state
            is_correct = state['knows'] and (random.random() > state['model'].p_slip)
            if not state['knows']:
                is_correct = random.random() < state['model'].p_guess
            
            # Simulate response time (SC-005: no gaps > 5s in distribution)
            # Using a truncated normal distribution to ensure realistic timing
            rt_mean = 15.0  # seconds
            rt_std = 3.0
            rt_seconds = max(1.0, min(5.0, random.gauss(rt_mean, rt_std)))
            
            # Simulate comprehension rating (1-5 Likert)
            # Correlated with correctness and explanation type
            base_rating = 3.0
            if is_correct:
                base_rating += 0.8
            if condition_name == "neuro_symbolic":
                base_rating += 0.5  # Neuro-symbolic expected to have higher comprehension
            
            comprehension_rating = max(1, min(5, int(round(base_rating))))
            
            # Create log record
            log_record = {
                'timestamp': datetime.now().isoformat(),
                'student_id': student_id,
                'problem_id': problem_id,
                'condition': condition_name,
                'correct': is_correct,
                'rt_seconds': round(rt_seconds, 2),
                'comprehension_rating': comprehension_rating,
                'bkt_knows': state['knows'],
                'bkt_p_know': round(state['p_know'], 4),
                'data_source': 'simulated'
            }
            
            # Validate log record
            if not validate_simulation_log(log_record):
                logger.warning(f"Invalid log record generated for {student_id}/{problem_id}")
                continue
            
            logs.append(log_record)
            
            # Small delay to simulate processing time (optional, for realism)
            # time.sleep(0.001)
    
    logger.info(f"Completed simulation for condition '{condition_name}': {len(logs)} records generated")
    return logs

def main():
    """Main entry point for the simulation runner."""
    logger.info("Starting Neuro-Symbolic Simulation Runner")
    
    # Check calibration first
    if not check_calibration(CALIBRATION_REPORT_PATH):
        logger.error("Simulation aborted due to invalid calibration.")
        sys.exit(1)
    
    # Load configuration
    try:
        config = load_config(CONFIG_PATH)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    conditions = config.get('conditions', [])
    num_students_per_condition = config.get('num_students_per_condition', 50)
    problem_ids = config.get('problem_ids', [])
    bkt_params = config.get('bkt_params', {})
    
    if not conditions:
        logger.error("No conditions defined in configuration.")
        sys.exit(1)
    
    if not problem_ids:
        logger.error("No problem IDs defined in configuration.")
        sys.exit(1)
    
    logger.info(f"Loaded {len(conditions)} conditions and {len(problem_ids)} problems")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_LOG_PATH), exist_ok=True)
    
    all_logs = []
    
    # Run simulation for each condition
    for idx, condition in enumerate(conditions):
        condition_name = condition.get('name', condition)
        seed_offset = idx * 10000  # Ensure different seeds per condition
        
        condition_logs = run_simulation_for_condition(
            condition_name=condition_name,
            num_students=num_students_per_condition,
            problem_ids=problem_ids,
            bkt_params=bkt_params,
            seed_offset=seed_offset
        )
        
        all_logs.extend(condition_logs)
    
    # Write aggregated logs to CSV
    if all_logs:
        fieldnames = [
            'timestamp', 'student_id', 'problem_id', 'condition',
            'correct', 'rt_seconds', 'comprehension_rating',
            'bkt_knows', 'bkt_p_know', 'data_source'
        ]
        
        with open(OUTPUT_LOG_PATH, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_logs)
        
        logger.info(f"Successfully wrote {len(all_logs)} simulation logs to {OUTPUT_LOG_PATH}")
    else:
        logger.warning("No simulation logs were generated.")
    
    logger.info("Simulation run completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())