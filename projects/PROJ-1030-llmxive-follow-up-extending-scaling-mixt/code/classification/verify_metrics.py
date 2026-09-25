"""
Verification script for T032 to ensure metrics are computed correctly.

This script verifies that:
1. metrics.json exists and contains required fields
2. The baseline calculation uses the same sample IDs as the evaluation set
3. The baseline is actually a majority-class predictor
"""
import json
import argparse
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_metrics_file(metrics_path: str, labels_path: str) -> bool:
    """
    Verify the metrics.json file against the labels.csv.
    
    Args:
        metrics_path: Path to metrics.json
        labels_path: Path to the filtered labels CSV used for evaluation
        
    Returns:
        True if verification passes, False otherwise
    """
    # Load metrics
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    # Check required fields
    required_fields = ['metrics', 'baseline', 'comparison', 'sample_ids']
    missing = [f for f in required_fields if f not in metrics]
    if missing:
        logger.error(f"Missing required fields in metrics.json: {missing}")
        return False
    
    # Check baseline structure
    baseline = metrics['baseline']
    if 'f1_score' not in baseline or 'type' not in baseline:
        logger.error("Baseline missing required fields (f1_score, type)")
        return False
    
    if baseline['type'] != 'majority_class_predictor':
        logger.error(f"Baseline type is not 'majority_class_predictor': {baseline['type']}")
        return False
    
    # Verify sample IDs match
    import pandas as pd
    labels_df = pd.read_csv(labels_path)
    label_ids = set(labels_df['clip_id'].values)
    metric_ids = set(metrics['sample_ids'])
    
    if label_ids != metric_ids:
        logger.error("Sample IDs in metrics.json do not match labels.csv")
        logger.error(f"IDs in metrics but not in labels: {metric_ids - label_ids}")
        logger.error(f"IDs in labels but not in metrics: {label_ids - metric_ids}")
        return False
    
    # Verify comparison fields
    comparison = metrics['comparison']
    required_comp = ['model_f1', 'baseline_f1', 'improvement']
    missing_comp = [f for f in required_comp if f not in comparison]
    if missing_comp:
        logger.error(f"Missing comparison fields: {missing_comp}")
        return False
    
    # Verify improvement calculation
    expected_improvement = comparison['model_f1'] - comparison['baseline_f1']
    if abs(comparison['improvement'] - expected_improvement) > 1e-6:
        logger.error(f"Improvement calculation incorrect: {comparison['improvement']} vs {expected_improvement}")
        return False
    
    logger.info("All verification checks passed!")
    logger.info(f"Model F1: {comparison['model_f1']:.4f}")
    logger.info(f"Baseline F1: {comparison['baseline_f1']:.4f}")
    logger.info(f"Improvement: {comparison['improvement']:.4f}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Verify metrics computation')
    parser.add_argument('--metrics', type=str, required=True, 
                      help='Path to metrics.json')
    parser.add_argument('--labels', type=str, required=True, 
                      help='Path to filtered labels CSV')
    
    args = parser.parse_args()
    
    success = verify_metrics_file(args.metrics, args.labels)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    import sys
    main()
