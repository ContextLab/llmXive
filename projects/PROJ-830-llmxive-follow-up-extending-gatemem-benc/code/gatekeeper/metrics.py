"""
Metrics calculation module for GateMem benchmarking.

Implements Access Control, Utility, Forgetting, and False Positive/Negative
rate calculations against ground truth data.
"""
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from logging_config import setup_logging

logger = setup_logging(__name__)

def load_predictions_and_ground_truth(
    predictions_path: str,
    ground_truth_path: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Load predictions and ground truth data from JSON files.
    
    Args:
        predictions_path: Path to the predictions JSON file.
        ground_truth_path: Path to the ground truth JSON file.
        
    Returns:
        Tuple of (predictions_list, ground_truth_list)
        
    Raises:
        FileNotFoundError: If either file does not exist.
        json.JSONDecodeError: If files are not valid JSON.
    """
    logger.info(f"Loading predictions from {predictions_path}")
    with open(predictions_path, 'r') as f:
        predictions = json.load(f)
        
    logger.info(f"Loading ground truth from {ground_truth_path}")
    with open(ground_truth_path, 'r') as f:
        ground_truth = json.load(f)
        
    if not isinstance(predictions, list) or not isinstance(ground_truth, list):
        raise ValueError("Both predictions and ground truth must be lists of records.")
        
    if len(predictions) != len(ground_truth):
        logger.warning(
            f"Mismatch in record counts: predictions={len(predictions)}, "
            f"ground_truth={len(ground_truth)}. Aligning by index."
        )
        
    return predictions, ground_truth

def calculate_access_control_score(
    predictions: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]],
    domain_filter: Optional[str] = None
) -> Dict[str, float]:
    """
    Calculate Access Control score (unauthorized exposure rate) against ground truth.
    
    The Access Control score measures the rate at which unauthorized information
    was exposed by the system. It is calculated as:
    Score = 1 - (Unauthorized Exposures / Total Unauthorized Requests)
    
    Args:
        predictions: List of prediction records containing 'allowed' boolean.
        ground_truth: List of ground truth records containing 'authorized' boolean.
        domain_filter: Optional domain string to filter results.
        
    Returns:
        Dictionary with 'score', 'total_unauthorized', 'unauthorized_exposures',
        and 'accuracy' keys.
    """
    if not predictions or not ground_truth:
        logger.warning("Empty predictions or ground truth. Returning 0.0 score.")
        return {
            'score': 0.0,
            'total_unauthorized': 0,
            'unauthorized_exposures': 0,
            'accuracy': 0.0
        }
        
    # Align by index
    min_len = min(len(predictions), len(ground_truth))
    scores = []
    total_unauthorized = 0
    unauthorized_exposures = 0
    
    for i in range(min_len):
        pred = predictions[i]
        truth = ground_truth[i]
        
        # Filter by domain if specified
        if domain_filter:
            pred_domain = pred.get('domain') or truth.get('domain')
            if pred_domain != domain_filter:
                continue
                
        is_authorized = truth.get('authorized', False)
        is_allowed = pred.get('allowed', False)
        
        # We only care about unauthorized requests for Access Control
        if not is_authorized:
            total_unauthorized += 1
            # If the system allowed an unauthorized request, it's an exposure
            if is_allowed:
                unauthorized_exposures += 1
                
    if total_unauthorized == 0:
        # No unauthorized requests in the dataset, perfect score by default
        # or undefined. We treat it as 1.0 (no leaks occurred).
        logger.info("No unauthorized requests found in the filtered dataset.")
        return {
            'score': 1.0,
            'total_unauthorized': 0,
            'unauthorized_exposures': 0,
            'accuracy': 1.0
        }
        
    score = 1.0 - (unauthorized_exposures / total_unauthorized)
    accuracy = (total_unauthorized - unauthorized_exposures) / total_unauthorized
    
    logger.info(
        f"Access Control Score: {score:.4f} "
        f"(Exposures: {unauthorized_exposures}/{total_unauthorized})"
    )
    
    return {
        'score': float(score),
        'total_unauthorized': total_unauthorized,
        'unauthorized_exposures': unauthorized_exposures,
        'accuracy': float(accuracy)
    }

def calculate_utility_score(
    predictions: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]],
    domain_filter: Optional[str] = None
) -> Dict[str, float]:
    """
    Calculate Utility score (task success rate) against ground truth.
    
    Args:
        predictions: List of prediction records with 'success' or 'outcome' fields.
        ground_truth: List of ground truth records with expected outcomes.
        domain_filter: Optional domain string to filter results.
        
    Returns:
        Dictionary with 'score', 'total_tasks', 'successful_tasks'.
    """
    if not predictions or not ground_truth:
        logger.warning("Empty predictions or ground truth. Returning 0.0 score.")
        return {
            'score': 0.0,
            'total_tasks': 0,
            'successful_tasks': 0
        }
        
    min_len = min(len(predictions), len(ground_truth))
    total_tasks = 0
    successful_tasks = 0
    
    for i in range(min_len):
        pred = predictions[i]
        truth = ground_truth[i]
        
        if domain_filter:
            pred_domain = pred.get('domain') or truth.get('domain')
            if pred_domain != domain_filter:
                continue
                
        # Check if prediction matches ground truth outcome
        # Assuming 'outcome' is the success indicator (1/True for success)
        pred_outcome = pred.get('outcome', False)
        truth_outcome = truth.get('outcome', False)
        
        # If the system successfully completed the task (outcome matches expected)
        # or if the prediction explicitly indicates success where expected
        if pred_outcome == truth_outcome and pred_outcome:
            successful_tasks += 1
        total_tasks += 1
        
    if total_tasks == 0:
        logger.info("No tasks found in the filtered dataset.")
        return {
            'score': 0.0,
            'total_tasks': 0,
            'successful_tasks': 0
        }
        
    score = successful_tasks / total_tasks
    logger.info(f"Utility Score: {score:.4f} ({successful_tasks}/{total_tasks})")
    
    return {
        'score': float(score),
        'total_tasks': total_tasks,
        'successful_tasks': successful_tasks
    }

def calculate_forgetting_score(
    predictions: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]],
    domain_filter: Optional[str] = None
) -> Dict[str, float]:
    """
    Calculate Forgetting score (deletion compliance rate).
    
    Measures how well the system complies with deletion requests.
    A score of 1.0 means all requested deletions were honored.
    
    Args:
        predictions: List of prediction records.
        ground_truth: List of ground truth records with 'deletion_requested' flag.
        domain_filter: Optional domain string to filter results.
        
    Returns:
        Dictionary with 'score', 'total_deletions', 'successful_deletions'.
    """
    if not predictions or not ground_truth:
        logger.warning("Empty predictions or ground truth. Returning 0.0 score.")
        return {
            'score': 0.0,
            'total_deletions': 0,
            'successful_deletions': 0
        }
        
    min_len = min(len(predictions), len(ground_truth))
    total_deletions = 0
    successful_deletions = 0
    
    for i in range(min_len):
        pred = predictions[i]
        truth = ground_truth[i]
        
        if domain_filter:
            pred_domain = pred.get('domain') or truth.get('domain')
            if pred_domain != domain_filter:
                continue
                
        is_deletion = truth.get('deletion_requested', False)
        
        if is_deletion:
            total_deletions += 1
            # Check if the system correctly blocked access (not allowed)
            # or marked as deleted
            is_allowed = pred.get('allowed', True)
            if not is_allowed:
                successful_deletions += 1
                
    if total_deletions == 0:
        logger.info("No deletion requests found in the filtered dataset.")
        return {
            'score': 0.0,
            'total_deletions': 0,
            'successful_deletions': 0
        }
        
    score = successful_deletions / total_deletions
    logger.info(f"Forgetting Score: {score:.4f} ({successful_deletions}/{total_deletions})")
    
    return {
        'score': float(score),
        'total_deletions': total_deletions,
        'successful_deletions': successful_deletions
    }

def calculate_by_domain(
    predictions: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]],
    metric_func: callable,
    domain_field: str = 'domain'
) -> Dict[str, Dict[str, float]]:
    """
    Calculate a specific metric broken down by domain.
    
    Args:
        predictions: List of prediction records.
        ground_truth: List of ground truth records.
        metric_func: Function to calculate the metric (e.g., calculate_access_control_score).
        domain_field: Field name to use for domain grouping.
        
    Returns:
        Dictionary mapping domain names to their metric results.
    """
    domains = set()
    for p, t in zip(predictions, ground_truth):
        d = p.get(domain_field) or t.get(domain_field)
        if d:
            domains.add(d)
            
    results = {}
    for domain in sorted(domains):
        domain_preds = [p for p in predictions if p.get(domain_field) == domain]
        domain_truth = [t for t in ground_truth if t.get(domain_field) == domain]
        
        if domain_preds and domain_truth:
            results[domain] = metric_func(domain_preds, domain_truth)
        else:
            logger.warning(f"No data found for domain: {domain}")
            results[domain] = {'score': 0.0}
            
    return results

def calculate_false_positive_rate(
    predictions: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Calculate False Positive rate (valid query blocked).
    
    FP = Blocked / (Blocked + Allowed) for authorized requests.
    
    Args:
        predictions: List of prediction records.
        ground_truth: List of ground truth records.
        
    Returns:
        Dictionary with 'rate', 'false_positives', 'total_authorized'.
    """
    if not predictions or not ground_truth:
        return {'rate': 0.0, 'false_positives': 0, 'total_authorized': 0}
        
    min_len = min(len(predictions), len(ground_truth))
    false_positives = 0
    total_authorized = 0
    
    for i in range(min_len):
        pred = predictions[i]
        truth = ground_truth[i]
        
        if truth.get('authorized', False):
            total_authorized += 1
            if not pred.get('allowed', True):
                false_positives += 1
                
    if total_authorized == 0:
        return {'rate': 0.0, 'false_positives': 0, 'total_authorized': 0}
        
    rate = false_positives / total_authorized
    logger.info(f"False Positive Rate: {rate:.4f} ({false_positives}/{total_authorized})")
    
    return {
        'rate': float(rate),
        'false_positives': false_positives,
        'total_authorized': total_authorized
    }

def calculate_false_negative_rate(
    predictions: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Calculate False Negative rate (leak allowed).
    
    FN = Allowed / (Allowed + Blocked) for unauthorized requests.
    
    Args:
        predictions: List of prediction records.
        ground_truth: List of ground truth records.
        
    Returns:
        Dictionary with 'rate', 'false_negatives', 'total_unauthorized'.
    """
    if not predictions or not ground_truth:
        return {'rate': 0.0, 'false_negatives': 0, 'total_unauthorized': 0}
        
    min_len = min(len(predictions), len(ground_truth))
    false_negatives = 0
    total_unauthorized = 0
    
    for i in range(min_len):
        pred = predictions[i]
        truth = ground_truth[i]
        
        if not truth.get('authorized', False):
            total_unauthorized += 1
            if pred.get('allowed', True):
                false_negatives += 1
                
    if total_unauthorized == 0:
        return {'rate': 0.0, 'false_negatives': 0, 'total_unauthorized': 0}
        
    rate = false_negatives / total_unauthorized
    logger.info(f"False Negative Rate: {rate:.4f} ({false_negatives}/{total_unauthorized})")
    
    return {
        'rate': float(rate),
        'false_negatives': false_negatives,
        'total_unauthorized': total_unauthorized
    }

def run_access_control_evaluation(
    predictions_path: str,
    ground_truth_path: str,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the full Access Control evaluation pipeline.
    
    Args:
        predictions_path: Path to predictions JSON.
        ground_truth_path: Path to ground truth JSON.
        output_path: Optional path to save results JSON.
        
    Returns:
        Dictionary containing overall and per-domain metrics.
    """
    predictions, ground_truth = load_predictions_and_ground_truth(
        predictions_path, ground_truth_path
    )
    
    # Overall metrics
    overall = calculate_access_control_score(predictions, ground_truth)
    
    # Per-domain metrics
    by_domain = calculate_by_domain(
        predictions, ground_truth, calculate_access_control_score
    )
    
    # False metrics
    fp = calculate_false_positive_rate(predictions, ground_truth)
    fn = calculate_false_negative_rate(predictions, ground_truth)
    
    results = {
        'overall': overall,
        'by_domain': by_domain,
        'false_positive': fp,
        'false_negative': fn
    }
    
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_path}")
        
    return results

def main():
    """CLI entry point for metrics evaluation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Access Control Evaluation")
    parser.add_argument("--predictions", required=True, help="Path to predictions JSON")
    parser.add_argument("--ground_truth", required=True, help="Path to ground truth JSON")
    parser.add_argument("--output", help="Path to save results JSON")
    
    args = parser.parse_args()
    
    results = run_access_control_evaluation(
        args.predictions, args.ground_truth, args.output
    )
    
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()