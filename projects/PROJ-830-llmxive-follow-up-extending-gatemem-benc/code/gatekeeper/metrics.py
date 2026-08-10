import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np

from code.logging_config import setup_logging

logger = logging.getLogger(__name__)

def load_predictions_and_ground_truth(predictions_path: str, ground_truth_path: str) -> Tuple[List[Dict], List[Dict]]:
    """Load predictions and ground truth data."""
    with open(predictions_path, "r") as f:
        predictions = json.load(f)
    with open(ground_truth_path, "r") as f:
        ground_truth = json.load(f)
    return predictions, ground_truth

def calculate_access_control_score(predictions: List[Dict], ground_truth: List[Dict]) -> float:
    """Calculate access control score (unauthorized exposure rate)."""
    if not predictions or not ground_truth:
        return 0.0
    
    correct = 0
    total = len(predictions)
    
    for pred, truth in zip(predictions, ground_truth):
        if pred.get("allowed") == truth.get("expected_allowed"):
            correct += 1
    
    return correct / total if total > 0 else 0.0

def calculate_utility_score(predictions: List[Dict], ground_truth: List[Dict]) -> float:
    """Calculate utility score (task success rate)."""
    if not predictions or not ground_truth:
        return 0.0
    
    successful = 0
    total = len(predictions)
    
    for pred, truth in zip(predictions, ground_truth):
        if pred.get("success", False) == truth.get("expected_success", False):
            successful += 1
    
    return successful / total if total > 0 else 0.0

def calculate_forgetting_score(predictions: List[Dict], ground_truth: List[Dict]) -> float:
    """Calculate forgetting score (deletion compliance rate)."""
    if not predictions or not ground_truth:
        return 0.0
    
    compliant = 0
    total = len(predictions)
    
    for pred, truth in zip(predictions, ground_truth):
        if pred.get("deleted", False) == truth.get("expected_deleted", False):
            compliant += 1
    
    return compliant / total if total > 0 else 0.0

def calculate_by_domain(predictions: List[Dict], ground_truth: List[Dict], metric_func) -> Dict[str, float]:
    """Calculate metric by domain."""
    domain_scores = {}
    domains = set(p.get("domain") for p in predictions)
    
    for domain in domains:
        domain_preds = [p for p in predictions if p.get("domain") == domain]
        domain_truth = [t for t in ground_truth if t.get("domain") == domain]
        domain_scores[domain] = metric_func(domain_preds, domain_truth)
    
    return domain_scores

def calculate_false_positive_rate(predictions: List[Dict], ground_truth: List[Dict]) -> float:
    """Calculate false positive rate (valid query blocked)."""
    if not predictions or not ground_truth:
        return 0.0
    
    false_positives = 0
    valid_queries = 0
    
    for pred, truth in zip(predictions, ground_truth):
        if truth.get("expected_allowed", False):
            valid_queries += 1
            if not pred.get("allowed", False):
                false_positives += 1
    
    return false_positives / valid_queries if valid_queries > 0 else 0.0

def calculate_false_negative_rate(predictions: List[Dict], ground_truth: List[Dict]) -> float:
    """Calculate false negative rate (leak allowed)."""
    if not predictions or not ground_truth:
        return 0.0
    
    false_negatives = 0
    invalid_queries = 0
    
    for pred, truth in zip(predictions, ground_truth):
        if not truth.get("expected_allowed", True):
            invalid_queries += 1
            if pred.get("allowed", False):
                false_negatives += 1
    
    return false_negatives / invalid_queries if invalid_queries > 0 else 0.0

def run_access_control_evaluation(predictions_path: str, ground_truth_path: str, output_path: str):
    """Run full access control evaluation."""
    predictions, ground_truth = load_predictions_and_ground_truth(predictions_path, ground_truth_path)
    
    score = calculate_access_control_score(predictions, ground_truth)
    fp_rate = calculate_false_positive_rate(predictions, ground_truth)
    fn_rate = calculate_false_negative_rate(predictions, ground_truth)
    
    results = {
        "access_control_score": score,
        "false_positive_rate": fp_rate,
        "false_negative_rate": fn_rate,
        "total_episodes": len(predictions)
    }
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Access control evaluation saved to {output_path}")
    return results

def main():
    """Test metrics module."""
    logger.info("Testing metrics module...")
    # Dummy test
    preds = [{"allowed": True}, {"allowed": False}]
    truth = [{"expected_allowed": True}, {"expected_allowed": False}]
    score = calculate_access_control_score(preds, truth)
    logger.info(f"Dummy score: {score}")

if __name__ == "__main__":
    setup_logging(level=logging.INFO)
    main()