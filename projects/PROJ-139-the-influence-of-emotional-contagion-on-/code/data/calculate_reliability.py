"""
Reliability calculation module for inter-rater reliability metrics.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)

def load_annotations(annotations_path: Path) -> List[Dict[str, Any]]:
    """
    Load annotations from a JSON file.
    
    Args:
        annotations_path: Path to the annotations file.
        
    Returns:
        List of annotation dictionaries.
    """
    if not annotations_path.exists():
        raise FileNotFoundError(f"Annotations file not found at {annotations_path}")
    
    with open(annotations_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def prepare_ratings(
    annotations: List[Dict[str, Any]], 
    annotator_1_label: str = 'vader_label',
    annotator_2_label: str = 'ground_truth'
) -> List[Dict[str, Any]]:
    """
    Prepare ratings for Kappa calculation.
    
    Args:
        annotations: List of annotation dictionaries.
        annotator_1_label: Label for first annotator's ratings.
        annotator_2_label: Label for second annotator's ratings.
        
    Returns:
        List of prepared ratings.
    """
    ratings = []
    for ann in annotations:
        if annotator_1_label in ann and annotator_2_label in ann:
            ratings.append({
                'comment_id': ann.get('comment_id', ''),
                annotator_1_label: ann[annotator_1_label],
                annotator_2_label: ann[annotator_2_label]
            })
    return ratings

def compute_cohen_kappa(
    ratings: List[Dict[str, Any]], 
    annotator_1: str, 
    annotator_2: str
) -> Optional[float]:
    """
    Compute Cohen's Kappa for two annotators.
    
    Args:
        ratings: List of rating dictionaries.
        annotator_1: Key for first annotator's ratings.
        annotator_2: Key for second annotator's ratings.
        
    Returns:
        Cohen's Kappa value or None if computation fails.
    """
    if len(ratings) < 2:
        return None
    
    # Count agreements and total
    total = len(ratings)
    agreement = sum(1 for r in ratings if r[annotator_1] == r[annotator_2])
    p_o = agreement / total
    
    # Calculate expected agreement
    label_counts_1 = defaultdict(int)
    label_counts_2 = defaultdict(int)
    
    for r in ratings:
        label_counts_1[r[annotator_1]] += 1
        label_counts_2[r[annotator_2]] += 1
    
    p_e = 0.0
    all_labels = set(label_counts_1.keys()) | set(label_counts_2.keys())
    for label in all_labels:
        p_e += (label_counts_1[label] / total) * (label_counts_2[label] / total)
    
    if p_e == 1.0:
        return 1.0
    
    kappa = (p_o - p_e) / (1 - p_e)
    return float(kappa)

def compute_cohen_kappa_aggregated(
    ratings: List[Dict[str, Any]]
) -> Optional[float]:
    """
    Compute aggregated Cohen's Kappa across all annotator pairs.
    
    Args:
        ratings: List of rating dictionaries.
        
    Returns:
        Aggregated Kappa value or None.
    """
    # For simplicity, assume we have two annotators
    if len(ratings) < 2:
        return None
    
    return compute_cohen_kappa(ratings, 'annotator_1', 'annotator_2')

def interpret_kappa(kappa: float) -> str:
    """
    Interpret Kappa value according to standard guidelines.
    
    Args:
        kappa: Kappa value.
        
    Returns:
        Interpretation string.
    """
    if kappa < 0:
        return "No agreement"
    elif kappa < 0.2:
        return "Slight agreement"
    elif kappa < 0.4:
        return "Fair agreement"
    elif kappa < 0.6:
        return "Moderate agreement"
    elif kappa < 0.8:
        return "Substantial agreement"
    else:
        return "Almost perfect agreement"

def generate_report(
    kappa_value: float,
    ratings_count: int
) -> Dict[str, Any]:
    """
    Generate a reliability report.
    
    Args:
        kappa_value: Computed Kappa value.
        ratings_count: Number of ratings.
        
    Returns:
        Report dictionary.
    """
    return {
        'kappa': kappa_value,
        'interpretation': interpret_kappa(kappa_value),
        'ratings_count': ratings_count,
        'reliability_status': 'acceptable' if kappa_value >= 0.6 else 'needs_improvement'
    }

def main():
    """
    Main function for reliability calculation (standalone test).
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Reliability calculation module loaded successfully")

if __name__ == "__main__":
    main()
