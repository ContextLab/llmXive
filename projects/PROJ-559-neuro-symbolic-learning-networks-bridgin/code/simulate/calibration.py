"""
Calibration module for BKT (Bayesian Knowledge Tracing) against human pilot data.

This module implements the core calibration logic required by FR-010. It compares
BKT predictions against human pilot data to optimize model parameters (P_G, P_L0, P_S, P_T).
If calibration thresholds fail (RMSE > 0.15 or diff > 0.02), the script exits with code 1.

Dependencies:
    - T031b: Ensures human pilot data exists at data/pilot/raw_pilot_data.csv
    - code/simulate/bkt_params.yaml: Initial parameters
"""
import os
import sys
import json
import logging
import random
import hashlib
import yaml
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CALIBRATION_DATA_PATH = "data/pilot/raw_pilot_data.csv"
REPORT_OUTPUT_PATH = "data/pilot/calibration_report.json"
PARAMS_OUTPUT_PATH = "code/simulate/bkt_params.yaml"
RMSE_THRESHOLD = 0.15
DIFF_THRESHOLD = 0.02

def load_bkt_params(params_path: str = PARAMS_OUTPUT_PATH) -> Dict[str, float]:
    """Load current BKT parameters from YAML file."""
    if not os.path.exists(params_path):
        logger.error(f"BKT params file not found at {params_path}")
        sys.exit(1)
    with open(params_path, 'r') as f:
        return yaml.safe_load(f)

def save_bkt_params(params: Dict[str, float], params_path: str = PARAMS_OUTPUT_PATH) -> None:
    """Save updated BKT parameters to YAML file."""
    with open(params_path, 'w') as f:
        yaml.dump(params, f, default_flow_style=False)
    logger.info(f"Saved updated BKT params to {params_path}")

def load_pilot_data(data_path: str = CALIBRATION_DATA_PATH) -> pd.DataFrame:
    """
    Load human pilot data from CSV.
    Exits with code 1 if file is missing or invalid (per T031b dependency).
    """
    if not os.path.exists(data_path):
        logger.error(f"ERROR: Human pilot data missing at {data_path}. Calibration cannot proceed.")
        sys.exit(1)
    
    df = pd.read_csv(data_path)
    required_cols = ['student_id', 'problem_id', 'correct', 'attempt_num']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"ERROR: Pilot data missing required columns: {missing_cols}")
        sys.exit(1)
    
    if len(df) < 50:
        logger.error(f"ERROR: Human pilot data has insufficient records ({len(df)} < 50).")
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} records from pilot data.")
    return df

def calculate_rmse(predictions: List[float], actuals: List[float]) -> float:
    """Calculate Root Mean Squared Error between predictions and actuals."""
    if len(predictions) != len(actuals):
        raise ValueError("Predictions and actuals must have same length")
    if len(predictions) == 0:
        return 0.0
    squared_errors = [(p - a) ** 2 for p, a in zip(predictions, actuals)]
    return (sum(squared_errors) / len(squared_errors)) ** 0.5

def simulate_bkt_performance(df: pd.DataFrame, params: Dict[str, float]) -> Tuple[List[float], List[float]]:
    """
    Simulate BKT predictions for the given pilot data using provided parameters.
    Returns (predictions, actuals) lists for RMSE calculation.
    
    BKT Model:
    P(L_n) = P(L_{n-1}) + (1 - P(L_{n-1})) * P(T) * I(correct)
    P(correct) = P(L_n) * (1 - P(S)) + (1 - P(L_n)) * P(G)
    """
    P_G = params['P_G']
    P_L0 = params['P_L0']
    P_S = params['P_S']
    P_T = params['P_T']
    
    predictions = []
    actuals = []
    
    # Group by student and problem to simulate learning curve
    grouped = df.groupby(['student_id', 'problem_id'])
    
    for (student_id, problem_id), group in grouped:
        group = group.sort_values('attempt_num')
        p_learner = P_L0
        
        for _, row in group.iterrows():
            correct = row['correct']
            # Predict probability of correctness
            p_correct = p_learner * (1 - P_S) + (1 - p_learner) * P_G
            predictions.append(p_correct)
            actuals.append(float(correct))
            
            # Update belief based on observation
            if correct == 1:
                p_learner = p_learner + (1 - p_learner) * P_T
            else:
                # No update on incorrect guess (simplified)
                pass
    
    return predictions, actuals

def calculate_bkt_metrics(predictions: List[float], actuals: List[float], current_params: Dict[str, float]) -> Dict[str, Any]:
    """Calculate calibration metrics: RMSE and difference from baseline."""
    rmse = calculate_rmse(predictions, actuals)
    
    # Baseline RMSE (using fixed naive guess rate)
    naive_guess = 0.5
    naive_rmse = calculate_rmse([naive_guess] * len(actuals), actuals)
    diff = abs(rmse - naive_rmse)
    
    return {
        'rmse': round(rmse, 4),
        'diff': round(diff, 4),
        'num_samples': len(predictions)
    }

def run_calibration(params: Dict[str, float], df: pd.DataFrame, max_iter: int = 100) -> Tuple[Dict[str, float], Dict[str, Any], bool]:
    """
    Run calibration loop to optimize BKT parameters.
    Uses a simple grid search / local optimization approach.
    
    Returns: (optimized_params, metrics, passed_thresholds)
    """
    best_params = params.copy()
    best_rmse = float('inf')
    best_metrics = None
    
    # Simple grid search around current params
    # In a real system, this might use gradient descent or Bayesian optimization
    step = 0.05
    ranges = {
        'P_G': [0.01, 0.05, 0.1, 0.15, 0.2],
        'P_L0': [0.3, 0.4, 0.5, 0.6, 0.7],
        'P_S': [0.05, 0.1, 0.15, 0.2, 0.25],
        'P_T': [0.05, 0.1, 0.15, 0.2, 0.25]
    }
    
    logger.info("Starting calibration grid search...")
    
    # Limit iterations to prevent timeout
    iterations = 0
    for p_g in ranges['P_G']:
        for p_l0 in ranges['P_L0']:
            for p_s in ranges['P_S']:
                for p_t in ranges['P_T']:
                    if iterations >= max_iter:
                        break
                    iterations += 1
                    
                    test_params = {
                        'P_G': p_g,
                        'P_L0': p_l0,
                        'P_S': p_s,
                        'P_T': p_t
                    }
                    
                    preds, acts = simulate_bkt_performance(df, test_params)
                    metrics = calculate_bkt_metrics(preds, acts, test_params)
                    
                    if metrics['rmse'] < best_rmse:
                        best_rmse = metrics['rmse']
                        best_params = test_params
                        best_metrics = metrics
    
    logger.info(f"Calibration complete. Best RMSE: {best_rmse:.4f}")
    return best_params, best_metrics, best_metrics['rmse'] <= RMSE_THRESHOLD and best_metrics['diff'] <= DIFF_THRESHOLD

def main():
    """Main entry point for calibration task."""
    logger.info("Starting BKT calibration against human pilot data...")
    
    # Step 1: Load current BKT parameters
    current_params = load_bkt_params()
    logger.info(f"Loaded initial params: {current_params}")
    
    # Step 2: Load human pilot data (will exit if missing/invalid per T031b)
    pilot_df = load_pilot_data()
    
    # Step 3: Run calibration
    optimized_params, metrics, passed = run_calibration(current_params, pilot_df)
    
    # Step 4: Generate report
    report = {
        'has_human_data': True,
        'is_synthetic': False,
        'limitation_flag': not passed,
        'rmse': metrics['rmse'],
        'diff': metrics['diff'],
        'passed': passed,
        'params_used': optimized_params,
        'original_params': current_params,
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    # Step 5: Save report and updated params
    os.makedirs(os.path.dirname(REPORT_OUTPUT_PATH), exist_ok=True)
    with open(REPORT_OUTPUT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved calibration report to {REPORT_OUTPUT_PATH}")
    
    if passed:
        save_bkt_params(optimized_params)
        logger.info("Calibration PASSED. Updated parameters saved.")
        sys.exit(0)
    else:
        logger.error(f"Calibration FAILED. RMSE={metrics['rmse']:.4f} (threshold: {RMSE_THRESHOLD}), "
                    f"Diff={metrics['diff']:.4f} (threshold: {DIFF_THRESHOLD}).")
        logger.error("Pipeline halted per FR-010: Calibration thresholds not met.")
        sys.exit(1)

if __name__ == "__main__":
    main()
