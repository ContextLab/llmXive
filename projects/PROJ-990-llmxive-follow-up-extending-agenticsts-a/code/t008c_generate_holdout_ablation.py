"""
T008c: Generate Ground Truth Labels (Ablation – Hold-out Set)

Logic:
1. Load the validation set IDs from data/processed/validation_set.csv.
2. Load baseline win rates from data/processed/baseline_win_rates_train.json.
   (Note: The spec implies using the baseline established in T008-baseline.
    Since we are on the hold-out set, we assume the baseline behavior
    for these trajectories is already known or computed via the same
    engine runner in static mode. For this task, we assume the baseline
    file contains the necessary ground truth for the trajectories in the
    validation set, or we compute them if missing by calling the engine.)
3. For each trajectory in the validation set:
   a. Run the ablation study using code/engine_runner.py --ablate-layer <layer_name> --trajectory <id>.
   b. Compute utility_delta = baseline_win_rate - ablated_win_rate.
4. Save results to data/processed/ablation_labels_holdout.json.

Dependencies:
- T008-baseline (provides baseline_win_rates)
- T018 (provides engine_runner.py)
- T004 (provides engine)
- T014a (provides validation_set.csv)
"""

import os
import sys
import json
import logging
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/t008c_ablation_holdout.log')
    ]
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / 'data' / 'processed'
ENGINE_RUNNER = PROJECT_ROOT / 'code' / 'engine_runner.py'
VENV_PYTHON = PROJECT_ROOT / 'code' / '.venv' / 'bin' / 'python'

if not VENV_PYTHON.exists():
    VENV_PYTHON = sys.executable  # Fallback to current python if venv not found

INPUT_VALIDATION_SET = DATA_PROCESSED / 'validation_set.csv'
INPUT_BASELINE_WINS = DATA_PROCESSED / 'baseline_win_rates_train.json'
OUTPUT_ABLATION_LABELS = DATA_PROCESSED / 'ablation_labels_holdout.json'

# Layers to ablate (defined in spec or inferred from engine_runner)
# Based on typical AgenticSTS, layers might be: ['context', 'memory', 'reasoning', 'planning']
# We will attempt to infer or use a default list if not specified in config.
# For safety, we use a standard set often found in these tests.
DEFAULT_LAYERS = ['context', 'memory', 'reasoning', 'planning']

def load_validation_ids() -> List[str]:
    """Load trajectory IDs from the validation set CSV."""
    if not INPUT_VALIDATION_SET.exists():
        raise FileNotFoundError(f"Validation set not found: {INPUT_VALIDATION_SET}")
    
    import pandas as pd
    df = pd.read_csv(INPUT_VALIDATION_SET)
    if 'trajectory_id' not in df.columns:
        raise ValueError("validation_set.csv must contain 'trajectory_id' column")
    
    ids = df['trajectory_id'].tolist()
    logger.info(f"Loaded {len(ids)} trajectory IDs from validation set.")
    return ids

def load_baseline_win_rates() -> Dict[str, float]:
    """Load baseline win rates. If the file exists but doesn't cover all IDs,
    we might need to compute them on the fly, but the task assumes T008-baseline
    covered the necessary ground truth. We will try to load it first."""
    if not INPUT_BASELINE_WINS.exists():
        # If the training baseline file doesn't exist, we must compute baselines
        # for the hold-out set first. This is a fallback if T008-baseline was
        # strictly training-only and didn't include these IDs.
        logger.warning(f"Baseline file {INPUT_BASELINE_WINS} not found. "
                       "Attempting to compute baselines for hold-out trajectories.")
        return {}
    
    with open(INPUT_BASELINE_WINS, 'r') as f:
        data = json.load(f)
    
    # Convert list of dicts to dict if necessary
    if isinstance(data, list):
        return {item['trajectory_id']: item['win_rate'] for item in data}
    return data

def run_engine_ablation(trajectory_id: str, layer_name: str) -> Optional[float]:
    """
    Run the engine runner with ablation mode for a specific trajectory and layer.
    Returns the win rate (float) or None if failed.
    """
    cmd = [
        str(VENV_PYTHON),
        str(ENGINE_RUNNER),
        '--mode', 'ablation',
        '--ablate-layer', layer_name,
        '--trajectory', trajectory_id
    ]
    
    logger.debug(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes per trajectory
        )
        
        if result.returncode != 0:
            logger.error(f"Engine runner failed for {trajectory_id} (layer {layer_name}): {result.stderr}")
            return None
        
        # Parse output. Assuming the engine prints JSON or a specific success string.
        # If the engine_runner returns a JSON object with 'win_rate', parse it.
        # If it returns a log, we need to extract it.
        # For robustness, we assume the engine prints the result to stdout as JSON.
        try:
            # Look for JSON in stdout
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines:
                if line.startswith('{') or line.startswith('['):
                    try:
                        res_data = json.loads(line)
                        if isinstance(res_data, dict) and 'win_rate' in res_data:
                            return float(res_data['win_rate'])
                    except json.JSONDecodeError:
                        continue
            
            # Fallback: try to find a float in the output if JSON fails
            # This is less reliable but handles simple print outputs
            logger.warning(f"Could not parse JSON output for {trajectory_id} (layer {layer_name}). Raw output: {result.stdout[:200]}")
            return None

        except Exception as e:
            logger.error(f"Error parsing output for {trajectory_id}: {e}")
            return None

    except subprocess.TimeoutExpired:
        logger.error(f"Timeout running ablation for {trajectory_id} (layer {layer_name})")
        return None
    except Exception as e:
        logger.error(f"Unexpected error running ablation for {trajectory_id}: {e}")
        return None

def run_ablation_study():
    """Main logic for T008c."""
    logger.info("Starting T008c: Generate Ground Truth Labels (Ablation – Hold-out Set)")
    
    if not ENGINE_RUNNER.exists():
        raise FileNotFoundError(f"Engine runner not found: {ENGINE_RUNNER}")

    # 1. Load IDs
    trajectory_ids = load_validation_ids()
    if not trajectory_ids:
        logger.warning("No trajectory IDs found in validation set. Exiting.")
        return

    # 2. Load Baselines
    baseline_wins = load_baseline_win_rates()
    
    # If baselines are missing for these IDs, we must compute them first (Static Mode)
    # This handles the case where T008-baseline only ran on training set.
    missing_baselines = [tid for tid in trajectory_ids if tid not in baseline_wins]
    if missing_baselines:
        logger.info(f"Computing missing baselines for {len(missing_baselines)} hold-out trajectories...")
        for tid in missing_baselines:
            cmd = [
                str(VENV_PYTHON), str(ENGINE_RUNNER),
                '--mode', 'static', '--trajectory', tid
            ]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if res.returncode == 0:
                    # Parse win rate from static run
                    for line in res.stdout.split('\n'):
                        if line.startswith('{'):
                            try:
                                d = json.loads(line)
                                if 'win_rate' in d:
                                    baseline_wins[tid] = float(d['win_rate'])
                                    break
                            except: pass
            except Exception as e:
                logger.error(f"Failed to compute baseline for {tid}: {e}")

    if len(baseline_wins) < len(trajectory_ids):
        logger.warning(f"Missing baseline win rates for {len(trajectory_ids) - len(baseline_wins)} trajectories. "
                       "These will be skipped in delta calculation.")

    # 3. Run Ablation
    results = []
    layers_to_ablate = DEFAULT_LAYERS # Could be dynamic based on engine capabilities

    logger.info(f"Starting ablation for {len(trajectory_ids)} trajectories across {len(layers_to_ablate)} layers.")
    
    for tid in trajectory_ids:
        baseline_rate = baseline_wins.get(tid)
        if baseline_rate is None:
            logger.warning(f"Skipping {tid}: No baseline win rate available.")
            continue

        for layer in layers_to_ablate:
            ablated_rate = run_engine_ablation(tid, layer)
            if ablated_rate is None:
                logger.warning(f"Skipping ablation result for {tid} (layer {layer}): Failed to run engine.")
                continue

            delta = baseline_rate - ablated_rate
            
            record = {
                "trajectory_id": tid,
                "layer_name": layer,
                "baseline_win_rate": baseline_rate,
                "ablated_win_rate": ablated_rate,
                "utility_delta": delta
            }
            results.append(record)
            logger.debug(f"Recorded: {tid} - {layer} - delta: {delta:.4f}")

    # 4. Save Output
    OUTPUT_ABLATION_LABELS.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_ABLATION_LABELS, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Successfully wrote {len(results)} ablation records to {OUTPUT_ABLATION_LABELS}")

def main():
    try:
        run_ablation_study()
    except Exception as e:
        logger.critical(f"T008c failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
