import os
import sys
import json
import logging
import random
import hashlib
import pandas as pd
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PILOT_DIR = os.path.join(PROJECT_ROOT, 'data', 'pilot')
CODE_SIMULATE_DIR = os.path.join(PROJECT_ROOT, 'code', 'simulate')
REPORT_PATH = os.path.join(DATA_PILOT_DIR, 'calibration_report.json')
PARAMS_PATH = os.path.join(CODE_SIMULATE_DIR, 'bkt_params.yaml')
HUMAN_DATA_PATH = os.path.join(DATA_PILOT_DIR, 'raw_pilot_data.csv')
SYNTHETIC_DATA_PATH = os.path.join(DATA_PILOT_DIR, 'synthetic_pilot_data.csv')

def load_bkt_params(path: str = PARAMS_PATH) -> Dict[str, float]:
    import yaml
    if not os.path.exists(path):
        logger.warning(f"Params file {path} not found. Using defaults.")
        return {"P_G": 0.1, "P_L0": 0.5, "P_S": 0.2, "P_T": 0.1}
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def save_bkt_params(params: Dict[str, float], path: str = PARAMS_PATH) -> None:
    import yaml
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(params, f, default_flow_style=False)
    logger.info(f"Saved BKT params to {path}")

def load_pilot_data() -> pd.DataFrame:
    """
    Load pilot data. Prioritizes human data if available, otherwise synthetic.
    Returns a tuple: (dataframe, has_human, is_synthetic)
    """
    if os.path.exists(HUMAN_DATA_PATH):
        logger.info("Loading human pilot data.")
        return pd.read_csv(HUMAN_DATA_PATH), True, False
    
    if os.path.exists(SYNTHETIC_DATA_PATH):
        logger.info("Loading synthetic pilot data.")
        return pd.read_csv(SYNTHETIC_DATA_PATH), False, True
    
    raise FileNotFoundError("No pilot data found (human or synthetic).")

def calculate_rmse(predictions: List[float], actuals: List[float]) -> float:
    if len(predictions) != len(actuals):
        raise ValueError("Length mismatch")
    mse = sum((p - a) ** 2 for p, a in zip(predictions, actuals)) / len(predictions)
    return mse ** 0.5

def simulate_bkt_performance(params: Dict[str, float], num_students: int, num_problems: int) -> List[float]:
    """
    Simulate BKT performance for a set of students and problems.
    Returns a list of predicted accuracies per student.
    """
    p_g = params['P_G']
    p_l0 = params['P_L0']
    p_s = params['P_S']
    p_t = params['P_T']
    
    accuracies = []
    for _ in range(num_students):
        # Initial state: not learned
        learned = random.random() < p_l0
        correct_count = 0
        
        for _ in range(num_problems):
            if learned:
                if random.random() > p_s:
                    correct_count += 1
                else:
                    # Slip
                    pass
                # Transition
                if random.random() < p_t:
                    learned = True # Already learned, stays learned
            else:
                if random.random() < p_g:
                    correct_count += 1
                if random.random() < p_l0:
                    learned = True
          
        accuracies.append(correct_count / num_problems)
    
    return accuracies

def calculate_bkt_metrics(params: Dict[str, float], pilot_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate BKT metrics against pilot data.
    """
    # Simulate predictions based on current params
    num_students = len(pilot_data)
    # Assume pilot data has 'correct_count' and 'num_problems' or similar
    # If not, we aggregate by student_id if present, or assume row=student
    if 'student_id' in pilot_data.columns:
        # Aggregate by student
        student_acc = pilot_data.groupby('student_id')['correct'].mean().tolist()
    else:
        # Assume each row is a student's summary
        if 'accuracy' in pilot_data.columns:
            student_acc = pilot_data['accuracy'].tolist()
        elif 'correct' in pilot_data.columns and 'total' in pilot_data.columns:
            student_acc = (pilot_data['correct'] / pilot_data['total']).tolist()
        else:
            # Fallback: assume binary correctness per row and aggregate
            # This is a simplification for the calibration step
            raise ValueError("Pilot data must contain accuracy or correct/total columns.")
    
    # Simulate BKT predictions for the same number of students
    # We need to simulate the same number of problems if we want a direct comparison
    # For simplicity, we compare the mean accuracy distribution
    simulated_acc = simulate_bkt_performance(params, num_students, 10) # 10 problems per student
    
    rmse = calculate_rmse(simulated_acc, student_acc)
    
    return {
        "rmse": rmse,
        "mean_predicted": sum(simulated_acc) / len(simulated_acc),
        "mean_actual": sum(student_acc) / len(student_acc)
    }

def run_calibration():
    """
    Main entry point for T031.
    1. Load pilot data (human or synthetic).
    2. Load current BKT params.
    3. Calculate RMSE.
    4. If human data missing and synthetic used, log warning and set limitation_flag.
    5. Save calibration report.
    6. If calibration thresholds fail on valid data, exit 1.
    """
    logger.info("Running Calibration (T031)...")
    
    try:
        pilot_data, has_human, is_synthetic = load_pilot_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    if has_human:
        logger.info("Using human pilot data.")
    elif is_synthetic:
        logger.warning("Human pilot data missing. Using synthetic data for calibration. (Limitation)")
    else:
        logger.error("No data available.")
        sys.exit(1)
    
    params = load_bkt_params()
    metrics = calculate_bkt_metrics(params, pilot_data)
    
    # Thresholds
    RMSE_THRESHOLD = 0.15
    passed = metrics['rmse'] <= RMSE_THRESHOLD
    
    report = {
        "has_human_data": has_human,
        "is_synthetic": is_synthetic,
        "limitation_flag": is_synthetic,
        "rmse": metrics['rmse'],
        "passed": passed,
        "params_used": params,
        "timestamp": os.popen('date -u +"%Y-%m-%dT%H:%M:%SZ"').read().strip()
    }
    
    if not passed and has_human:
        logger.error(f"Calibration failed on human data (RMSE={metrics['rmse']:.4f} > {RMSE_THRESHOLD}).")
        sys.exit(1)
    
    if not passed and is_synthetic:
        logger.warning(f"Calibration failed on synthetic data (RMSE={metrics['rmse']:.4f} > {RMSE_THRESHOLD}). Proceeding with warning.")
    
    os.makedirs(DATA_PILOT_DIR, exist_ok=True)
    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Calibration report saved to {REPORT_PATH}")
    return 0

def main():
    return run_calibration()

if __name__ == "__main__":
    sys.exit(main())
