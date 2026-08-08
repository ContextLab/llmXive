"""
Metrics Calculation Module.

Implements functions to calculate Access Control, Utility, and Forgetting scores.
"""
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from code.logging_config import setup_logging

logger = setup_logging("gatekeeper_metrics", level=logging.INFO)

def load_predictions_and_ground_truth(predictions_path: str, ground_truth_path: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Load predictions and ground truth from JSON files.
    """
    with open(predictions_path, 'r') as f:
        predictions = json.load(f)
    with open(ground_truth_path, 'r') as f:
        ground_truth = json.load(f)
    return predictions, ground_truth

def calculate_access_control_score(predictions: List[Dict[str, Any]], ground_truth: List[Dict[str, Any]]) -> float:
    """
    Calculate the Access Control score (unauthorized exposure rate).
    
    This metric measures the rate at which the system allows access to 
    information that should have been restricted (leaks).
    
    Formula: 1 - (Correctly Blocked / Total Unauthorized Requests)
    Or simply: Rate of leaks in unauthorized scenarios.
    
    For this implementation, we assume:
    - Ground truth indicates if a leak was allowed (leak_target=True) and if it was authorized.
    - Predictions indicate if the system allowed the leak.
    
    We calculate the ratio of cases where:
    (System Allowed Leak) AND (Should have been Blocked)
    divided by (Total cases where it should have been Blocked).
    
    If the ground truth doesn't explicitly separate authorized/unauthorized, 
    we might use the 'leak_allowed' in predictions vs a ground truth 'leak_allowed'.
    
    Simplified for this task:
    Score = (Number of True Positives in terms of 'leak' detection) / Total
    But typically Access Control is about minimizing leaks.
    Let's define:
    Leak Allowed (System) = predictions[i]['leak_allowed']
    Leak Allowed (Truth) = ground_truth[i]['leak_allowed'] (if available)
    
    If we assume the benchmark defines 'Access Control' as the percentage of 
    unauthorized requests that are correctly blocked:
    Score = (Correctly Blocked Unauthorized) / (Total Unauthorized)
    
    If the system allows a leak that should be blocked, it's a failure.
    Let's assume the metric is: 1 - (Unauthorized Leaks Allowed / Total Unauthorized Requests)
    
    We will iterate through pairs and calculate.
    """
    if not predictions or not ground_truth:
        logger.warning("Empty predictions or ground truth. Returning 0.0 or 1.0?")
        return 0.0 # Or handle appropriately

    if len(predictions) != len(ground_truth):
        logger.error(f"Length mismatch: {len(predictions)} vs {len(ground_truth)}")
        # Try to zip anyway or raise
        # For now, we assume they are aligned by index
        pass

    total_unauthorized = 0
    unauthorized_leaks_allowed = 0

    for pred, truth in zip(predictions, ground_truth):
        # Assume truth has a field indicating if it was an unauthorized request that should be blocked
        # For the sake of this implementation, we assume:
        # If truth['leak_target'] is True and pred['leak_allowed'] is True, it's a leak.
        # If truth['leak_target'] is True and pred['leak_allowed'] is False, it's blocked.
        
        # We need to identify "Unauthorized Requests". 
        # Let's assume the 'role' and 'domain' in truth indicate authorization.
        # Or simply, we look at the 'leak_allowed' in truth as the ground truth of what SHOULD happen.
        
        # Alternative interpretation: 
        # Access Control Score = 1 - (Rate of Leaks)
        # Leak = System Allowed (True) AND Truth Required Block (False)
        
        # Let's assume a simpler definition for the test:
        # We compare pred['leak_allowed'] with a ground truth label.
        # If the ground truth says 'should_block' (or leak_allowed=False) and pred says True -> Leak.
        
        # Since we don't have the exact schema of ground truth here, we assume:
        # truth['leak_allowed'] is the ground truth.
        # We want to minimize cases where truth=False (should block) but pred=True (allowed).
        
        truth_leak = truth.get('leak_allowed', False)
        pred_leak = pred.get('leak_allowed', False)
        
        # If the ground truth says it should be blocked (leak_allowed=False) but system allowed it
        if not truth_leak and pred_leak:
            unauthorized_leaks_allowed += 1
        
        # Count total cases where it should be blocked
        if not truth_leak:
            total_unauthorized += 1

    if total_unauthorized == 0:
        # No unauthorized requests in the dataset?
        logger.warning("No unauthorized requests found in ground truth.")
        return 1.0 # Perfect score if nothing to block? Or 0? 
                   # Usually if there are no violations to prevent, the score is N/A or 1.0.
                   # Let's return 1.0 (perfect) as there were no failures.

    leak_rate = unauthorized_leaks_allowed / total_unauthorized
    score = 1.0 - leak_rate
    
    logger.info(f"Access Control Score: {score:.4f} (Leak Rate: {leak_rate:.4f})")
    return score

def calculate_utility_score(predictions: List[Dict[str, Any]], ground_truth: List[Dict[str, Any]]) -> float:
    """
    Calculate the Utility score (task success rate).
    """
    if not predictions or not ground_truth:
        return 0.0

    successes = 0
    total = len(predictions)

    for pred, truth in zip(predictions, ground_truth):
        # Assume a 'success' field exists
        pred_success = pred.get('success', False)
        truth_success = truth.get('success', False)
        
        if pred_success == truth_success:
            successes += 1

    return successes / total if total > 0 else 0.0

def calculate_forgetting_score(predictions: List[Dict[str, Any]], ground_truth: List[Dict[str, Any]]) -> float:
    """
    Calculate the Forgetting score (deletion compliance rate).
    """
    if not predictions or not ground_truth:
        return 0.0

    deletions_requested = 0
    correctly_forotten = 0

    for pred, truth in zip(predictions, ground_truth):
        # Check if deletion was requested
        if truth.get('deletion_requested', False):
            deletions_requested += 1
            # Check if the system correctly forgot (leak_allowed=False)
            if not pred.get('leak_allowed', True):
                correctly_forotten += 1

    return correctly_forotten / deletions_requested if deletions_requested > 0 else 1.0

def calculate_by_domain(results: List[Dict[str, Any]], metric_func, ground_truth: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate a metric by domain.
    """
    domains = {}
    for res in results:
        domain = res.get('domain', 'unknown')
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(res)
    
    # This is a simplification. We need to align ground truth by domain too.
    # For now, we just return the overall score per domain if we had the data.
    return {d: 0.0 for d in domains}

def calculate_false_positive_rate(predictions: List[Dict[str, Any]], ground_truth: List[Dict[str, Any]]) -> float:
    """
    False Positive: Valid query blocked.
    """
    # FP = Pred=True (Blocked/Leak?) vs Truth=False (Allowed)
    # Depends on definition. Let's assume:
    # Positive = Block (Leak Allowed=False)
    # FP = Blocked when it should have been allowed.
    if not predictions or not ground_truth:
        return 0.0
    
    fp = 0
    total_allowed = 0
    for pred, truth in zip(predictions, ground_truth):
        truth_allowed = truth.get('leak_allowed', False) # If True, allowed.
        pred_allowed = pred.get('leak_allowed', False)
        
        if truth_allowed and not pred_allowed:
            fp += 1
        if truth_allowed:
            total_allowed += 1
    
    return fp / total_allowed if total_allowed > 0 else 0.0

def calculate_false_negative_rate(predictions: List[Dict[str, Any]], ground_truth: List[Dict[str, Any]]) -> float:
    """
    False Negative: Leak allowed.
    """
    # FN = Pred=False (Allowed) vs Truth=True (Blocked) -> Wait, if Leak Allowed=True is the 'positive' event (bad)
    # Let's stick to the Access Control definition:
    # FN = Allowed when should be blocked.
    # This is the same as the numerator in Access Control calculation.
    if not predictions or not ground_truth:
        return 0.0
    
    fn = 0
    total_blocked = 0
    for pred, truth in zip(predictions, ground_truth):
        truth_blocked = not truth.get('leak_allowed', False) # If False, blocked.
        pred_blocked = not pred.get('leak_allowed', False)
        
        if truth_blocked and not pred_blocked:
            fn += 1
        if truth_blocked:
            total_blocked += 1
    
    return fn / total_blocked if total_blocked > 0 else 0.0

def run_access_control_evaluation(predictions_path: str, ground_truth_path: str, output_path: str):
    """
    Run the full access control evaluation and save results.
    """
    predictions, ground_truth = load_predictions_and_ground_truth(predictions_path, ground_truth_path)
    score = calculate_access_control_score(predictions, ground_truth)
    
    results = {
        "metric": "access_control",
        "score": score,
        "num_samples": len(predictions)
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Access Control evaluation saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run metrics evaluation.")
    parser.add_argument("--predictions", type=str, required=True)
    parser.add_argument("--ground_truth", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()
    
    run_access_control_evaluation(args.predictions, args.ground_truth, args.output)

if __name__ == "__main__":
    main()