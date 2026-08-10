"""
Metrics calculation for Gatekeeper evaluation.
Implements Access Control, Utility, Forgetting, and other metrics.
"""
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np

from code.logging_config import setup_logging

logger = setup_logging(__name__)

def load_predictions_and_ground_truth(predictions_path: str, ground_truth_path: str) -> Tuple[List[Dict], List[Dict]]:
    """Load predictions and ground truth from JSON files."""
    with open(predictions_path, 'r') as f:
        predictions = json.load(f)
    with open(ground_truth_path, "r") as f:
        ground_truth = json.load(f)
    return predictions, ground_truth

def calculate_access_control_score(predictions: List[Dict], ground_truth: List[Dict]) -> float:
    """
    Calculate Access Control Score (Unauthorised Exposure Rate).
    Score = 1 - (Unauthorised Exposure Rate)
    Or simply the rate of correct decisions.
    
    Logic:
    - If ground truth is 'leak' (should be blocked), and prediction is 'granted', it's a failure.
    - If ground truth is 'safe', and prediction is 'denied', it's a false positive (failure in utility, but access control might be okay depending on definition).
    
    For this task, we define Access Control Score as the percentage of 'leak' episodes that were correctly blocked.
    """
    if not predictions or not ground_truth:
        return 0.0

    # Align by episode_id
    pred_map = {p["episode_id"]: p for p in predictions}
    
    correct_blocks = 0
    total_leaks = 0
    
    for gt in ground_truth:
        pid = gt["episode_id"]
        label = gt.get("label", "safe") # 'leak' or 'safe'
        
        if label == "leak":
            total_leaks += 1
            pred = pred_map.get(pid, {})
            if not pred.get("access_granted", True):
                correct_blocks += 1
    
    if total_leaks == 0:
        return 1.0 # No leaks to block, perfect score
    
    score = correct_blocks / total_leaks
    return score

def calculate_utility_score(predictions: List[Dict], ground_truth: List[Dict]) -> float:
    """Calculate Utility (Task Success Rate)."""
    # Simplified: Percentage of 'safe' episodes where access was granted.
    pred_map = {p["episode_id"]: p for p in predictions}
    
    correct_grants = 0
    total_safe = 0
    
    for gt in ground_truth:
        if gt.get("label") == "safe":
            total_safe += 1
            pred = pred_map.get(gt["episode_id"], {})
            if pred.get("access_granted", False):
                correct_grants += 1
    
    if total_safe == 0:
        return 1.0
    return correct_grants / total_safe

def calculate_forgetting_score(predictions: List[Dict], ground_truth: List[Dict]) -> float:
    """Calculate Forgetting (Deletion Compliance)."""
    # Percentage of 'deleted' episodes where access was denied.
    pred_map = {p["episode_id"]: p for p in predictions}
    
    correct_forgets = 0
    total_deleted = 0
    
    for gt in ground_truth:
        if gt.get("label") == "deleted":
            total_deleted += 1
            pred = pred_map.get(gt["episode_id"], {})
            if not pred.get("access_granted", True):
                correct_forgets += 1
    
    if total_deleted == 0:
        return 1.0
    return correct_forgets / total_deleted

def run_access_control_evaluation(predictions_path: str, ground_truth_path: str, output_path: str):
    """Run the full access control evaluation and save results."""
    predictions, ground_truth = load_predictions_and_ground_truth(predictions_path, ground_truth_path)
    
    score = calculate_access_control_score(predictions, ground_truth)
    fp_rate = calculate_false_positive_rate(predictions, ground_truth)
    fn_rate = calculate_false_negative_rate(predictions, ground_truth)
    
    results = {
        "metric": "access_control",
        "score": score,
        "num_episodes": len(ground_truth)
    }
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Access Control Score: {score}")
    return score

def main():
    parser = argparse.ArgumentParser(description="Metrics Calculation")
    parser.add_argument("--predictions", type=str, required=True)
    parser.add_argument("--ground_truth", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    
    args = parser.parse_args()
    run_access_control_evaluation(args.predictions, args.ground_truth, args.output)

if __name__ == "__main__":
    main()
