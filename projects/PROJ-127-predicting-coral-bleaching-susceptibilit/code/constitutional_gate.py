import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

import config

# Constants
ROC_AUC_THRESHOLD = 0.80
RESULTS_PATH = Path("data/processed/results.json")
DATA_GAP_STATUS_PATH = Path("data_gap_status.json")
PERFORMANCE_STATUS_KEY = "performance_status"
ROC_AUC_KEY = "roc_auc"


def load_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if it doesn't exist or is invalid."""
    if not path.exists():
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load JSON from {path}: {e}")
        return None


def check_data_gap_status() -> str:
    """
    Check the data gap status from data_gap_status.json.
    Returns 'PASS', 'FAIL', or 'UNKNOWN' if the file is missing.
    """
    status_data = load_json_safe(DATA_GAP_STATUS_PATH)
    if status_data is None:
        print("Warning: data_gap_status.json not found. Assuming data gap check was not run or failed.")
        return "UNKNOWN"
    
    status = status_data.get("status", "UNKNOWN")
    if status not in ["PASS", "FAIL"]:
        print(f"Warning: Unexpected status '{status}' in data_gap_status.json. Treating as UNKNOWN.")
        return "UNKNOWN"
    return status


def evaluate_constitutional_gate(roc_auc: Optional[float]) -> str:
    """
    Evaluate the ROC-AUC score against the constitutional threshold.
    
    Args:
        roc_auc: The ROC-AUC score to evaluate.
    
    Returns:
        'PASS' if roc_auc >= threshold, 'FAIL' if roc_auc < threshold,
        'N/A' if data gap status is FAIL or ROC-AUC is missing.
    """
    if roc_auc is None:
        return "N/A"
    
    if roc_auc >= ROC_AUC_THRESHOLD:
        return "PASS"
    else:
        return "FAIL"


def main():
    """
    Main function to execute the Constitutional Gate evaluation.
    
    1. Checks data gap status.
    2. If PASS, reads ROC-AUC from results.json.
    3. Evaluates against threshold.
    4. Updates results.json with performance_status.
    5. Logs the result but does NOT halt the pipeline.
    """
    print("--- Constitutional Gate Evaluation (T017) ---")
    
    # 1. Check Data Gap Status
    data_gap_status = check_data_gap_status()
    print(f"Data Gap Status: {data_gap_status}")
    
    performance_status = "N/A"
    roc_auc_value = None
    
    if data_gap_status == "FAIL":
        print("Data gap check failed. Skipping ROC-AUC evaluation.")
        performance_status = "N/A"
    elif data_gap_status == "UNKNOWN":
        print("Data gap status file missing. Skipping ROC-AUC evaluation.")
        performance_status = "N/A"
    else:
        # 2. Read ROC-AUC from results.json
        results_data = load_json_safe(RESULTS_PATH)
        if results_data is None:
            print(f"Warning: {RESULTS_PATH} not found. Cannot evaluate ROC-AUC.")
            performance_status = "N/A"
        else:
            roc_auc_value = results_data.get(ROC_AUC_KEY)
            if roc_auc_value is None:
                print(f"Warning: '{ROC_AUC_KEY}' key not found in {RESULTS_PATH}.")
                performance_status = "N/A"
            else:
                # 3. Evaluate against threshold
                performance_status = evaluate_constitutional_gate(roc_auc_value)
                print(f"ROC-AUC Score: {roc_auc_value}")
                print(f"Threshold: {ROC_AUC_THRESHOLD}")
                print(f"Performance Status: {performance_status}")
    
    # 4. Update results.json with performance_status
    if RESULTS_PATH.exists():
        try:
            with open(RESULTS_PATH, "r") as f:
                current_results = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading {RESULTS_PATH}: {e}")
            current_results = {}
        
        current_results[PERFORMANCE_STATUS_KEY] = performance_status
        
        try:
            with open(RESULTS_PATH, "w") as f:
                json.dump(current_results, f, indent=2)
            print(f"Updated {RESULTS_PATH} with performance_status: {performance_status}")
        except IOError as e:
            print(f"Error writing to {RESULTS_PATH}: {e}")
    else:
        # If results.json doesn't exist, create it with just the status
        print(f"Warning: {RESULTS_PATH} does not exist. Creating a new one with performance_status.")
        new_results = {PERFORMANCE_STATUS_KEY: performance_status}
        if roc_auc_value is not None:
            new_results[ROC_AUC_KEY] = roc_auc_value
        
        try:
            RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(RESULTS_PATH, "w") as f:
                json.dump(new_results, f, indent=2)
            print(f"Created {RESULTS_PATH} with performance_status: {performance_status}")
        except IOError as e:
            print(f"Error creating {RESULTS_PATH}: {e}")
    
    # 5. Log result and proceed (Do NOT halt)
    print("--- Constitutional Gate Evaluation Complete ---")
    print(f"Proceeding to next task regardless of performance status ({performance_status}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())