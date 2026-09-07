"""
Divergence Check (Task T050)

Computes the percentage of trajectories where the final state hash differs
between the Dynamic and Static simulation runs.

Logic:
1. Load simulation logs for 'dynamic' and 'static' modes from data/processed/.
2. Extract the final_state_hash for each trajectory_id from both sets.
3. Identify trajectories present in BOTH sets (paired).
4. Compare hashes: if dynamic_hash != static_hash, it is a divergence.
5. Calculate divergence percentage: (divergent_count / total_paired) * 100.
6. Flag if percentage > 10%.
7. Write result to data/processed/divergence_report.json.

Constraints:
- Must use REAL data from existing simulation logs.
- If files are missing or empty, raise FileNotFoundError (fail loudly).
- No synthetic data generation.
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DYNAMIC_LOG_PATH = DATA_PROCESSED_DIR / "simulation_logs_dynamic.json"
STATIC_LOG_PATH = DATA_PROCESSED_DIR / "simulation_logs_static.json"
OUTPUT_PATH = DATA_PROCESSED_DIR / "divergence_report.json"

THRESHOLD_PERCENT = 10.0


def load_simulation_logs(mode: str) -> Dict[str, Any]:
    """
    Load simulation logs for a specific mode (dynamic or static).
    Raises FileNotFoundError if the file does not exist or is empty.
    """
    if mode == "dynamic":
        path = DYNAMIC_LOG_PATH
    elif mode == "static":
        path = STATIC_LOG_PATH
    else:
        raise ValueError(f"Unknown mode: {mode}. Expected 'dynamic' or 'static'.")
    
    if not path.exists():
        raise FileNotFoundError(f"Simulation log file not found: {path}")
    
    logger.info(f"Loading simulation logs from {path}...")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data:
        raise ValueError(f"Simulation log file is empty: {path}")
    
    # Expected format: list of trajectory records or a dict with a 'trajectories' key
    if isinstance(data, list):
        return {rec['trajectory_id']: rec for rec in data}
    elif isinstance(data, dict):
        if 'trajectories' in data:
            return {rec['trajectory_id']: rec for rec in data['trajectories']}
        else:
            # Assume the dict itself is keyed by trajectory_id or contains relevant data
            # For safety, try to find a list of records
            for key, val in data.items():
                if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                    return {rec['trajectory_id']: rec for rec in val}
            raise ValueError(f"Unexpected structure in {path}. Expected list of trajectories.")
    else:
        raise ValueError(f"Unexpected data type in {path}: {type(data)}")

def extract_final_state_hash(record: Dict[str, Any]) -> Optional[str]:
    """
    Extract the final_state_hash from a trajectory record.
    Handles nested structures if necessary.
    """
    # Try direct key
    if 'final_state_hash' in record:
        return record['final_state_hash']
    
    # Try nested in 'state' or 'result'
    for key in ['state', 'result', 'metadata']:
        if key in record and isinstance(record[key], dict):
            if 'final_state_hash' in record[key]:
                return record[key]['final_state_hash']
    
    # Fallback: compute hash of the final state if raw state exists
    if 'final_state' in record:
        state_str = json.dumps(record['final_state'], sort_keys=True)
        return hashlib.sha256(state_str.encode('utf-8')).hexdigest()
    
    logger.warning(f"Could not find final_state_hash in record: {record.get('trajectory_id', 'unknown')}")
    return None

def calculate_divergence(
    dynamic_logs: Dict[str, Any], 
    static_logs: Dict[str, Any]
) -> Tuple[int, int, List[str], Dict[str, str]]:
    """
    Compare dynamic and static logs to find divergences.
    Returns:
        total_paired: number of trajectories present in both sets
        divergent_count: number of trajectories where hashes differ
        divergent_ids: list of trajectory_ids that diverged
        details: dict mapping trajectory_id to {"dynamic_hash": ..., "static_hash": ...}
    """
    common_ids = set(dynamic_logs.keys()) & set(static_logs.keys())
    total_paired = len(common_ids)
    
    if total_paired == 0:
        raise ValueError("No common trajectories found between dynamic and static logs. "
                         "Cannot compute divergence.")
    
    divergent_ids = []
    details = {}
    
    for tid in common_ids:
        dyn_rec = dynamic_logs[tid]
        stat_rec = static_logs[tid]
        
        dyn_hash = extract_final_state_hash(dyn_rec)
        stat_hash = extract_final_state_hash(stat_rec)
        
        if dyn_hash is None or stat_hash is None:
            logger.warning(f"Skipping {tid} due to missing hash.")
            continue
        
        if dyn_hash != stat_hash:
            divergent_ids.append(tid)
            details[tid] = {
                "dynamic_hash": dyn_hash,
                "static_hash": stat_hash
            }
    
    return total_paired, len(divergent_ids), divergent_ids, details

def run_divergence_check() -> Dict[str, Any]:
    """
    Main logic for T050.
    """
    logger.info("Starting Divergence Check (T050)...")
    
    # 1. Load Data
    try:
        dynamic_logs = load_simulation_logs("dynamic")
        static_logs = load_simulation_logs("static")
    except FileNotFoundError as e:
        logger.critical(str(e))
        raise
    
    # 2. Calculate Divergence
    total_paired, divergent_count, divergent_ids, details = calculate_divergence(
        dynamic_logs, static_logs
    )
    
    # 3. Compute Percentage
    divergence_percentage = (divergent_count / total_paired) * 100
    threshold_met = divergence_percentage > THRESHOLD_PERCENT
    
    # 4. Construct Report
    report = {
        "task_id": "T050",
        "description": "Divergence Check: Percentage of trajectories where final state hash differs between Dynamic and Static modes.",
        "metrics": {
            "total_paired_trajectories": total_paired,
            "divergent_trajectories": divergent_count,
            "divergence_percentage": round(divergence_percentage, 4),
            "threshold_percent": THRESHOLD_PERCENT,
            "threshold_met": threshold_met
        },
        "flag": "WARNING: High divergence detected" if threshold_met else "OK: Divergence within threshold",
        "sample_divergent_ids": divergent_ids[:10],  # Limit sample for readability
        "details_count": len(details),
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }
    
    if threshold_met:
        logger.warning(f"Threshold exceeded! Divergence: {divergence_percentage:.2f}% > {THRESHOLD_PERCENT}%")
    else:
        logger.info(f"Divergence check passed: {divergence_percentage:.2f}% <= {THRESHOLD_PERCENT}%")
    
    return report

def main():
    """
    Entry point for the script.
    Writes the report to data/processed/divergence_report.json.
    """
    try:
        report = run_divergence_check()
        
        # Ensure output directory exists
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Write report
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Divergence report written to {OUTPUT_PATH}")
        print(f"SUCCESS: {OUTPUT_PATH} created.")
        
    except FileNotFoundError as e:
        logger.error(f"DATA MISSING: {e}")
        raise
    except Exception as e:
        logger.error(f"ERROR during divergence check: {e}")
        raise

if __name__ == "__main__":
    main()