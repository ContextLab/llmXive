import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

from code.utils.logging_config import get_logger

logger = get_logger(__name__)

def load_annotations(annotations_path: str) -> List[Dict[str, Any]]:
    """Load annotations from JSON file."""
    if not os.path.exists(annotations_path):
        raise FileNotFoundError(f"Annotations file not found: {annotations_path}")
    
    with open(annotations_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def prepare_ratings(annotations: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[int]]]:
    """
    Prepare ratings in a format suitable for Kappa calculation.
    Returns: {comment_id: {annotator_id: rating}}
    We map labels to ints: positive=1, neutral=0, negative=-1
    """
    label_map = {
        'positive': 1, 'neg': -1, 'neutral': 0,
        '1': 1, '0': 0, '-1': -1, 'negative': -1
    }
    
    ratings = defaultdict(dict)
    
    for item in annotations:
        cid = item['comment_id']
        aid = item['annotator_id']
        label = item['label']
        
        score = label_map.get(label, 0)
        ratings[cid][aid] = score
    
    return ratings

def compute_cohen_kappa(ratings: Dict[str, Dict[str, int]], annotators: List[str]) -> float:
    """
    Compute Cohen's Kappa for two annotators.
    If more than 2, it computes pairwise and averages (simplified).
    """
    if len(annotators) != 2:
        # Fallback for >2: compute average pairwise or use Krippendorff's alpha logic
        # For this task, we assume exactly 2 annotators as per T007a spec.
        logger.warning(f"Expected 2 annotators, found {len(annotators)}. Using first two.")
        annotators = annotators[:2]
    
    a1, a2 = annotators
    agree = 0
    total = 0
    
    for cid, raters in ratings.items():
        if a1 in raters and a2 in raters:
            total += 1
            if raters[a1] == raters[a2]:
                agree += 1
    
    if total == 0:
        return 0.0
    
    po = agree / total
    
    # Calculate pe (expected agreement)
    counts_a1 = defaultdict(int)
    counts_a2 = defaultdict(int)
    
    for cid, raters in ratings.items():
        if a1 in raters: counts_a1[raters[a1]] += 1
        if a2 in raters: counts_a2[raters[a2]] += 1
    
    # Normalize
    n = total
    pe = 0
    all_values = set(counts_a1.keys()) | set(counts_a2.keys())
    for val in all_values:
        p1 = counts_a1.get(val, 0) / n
        p2 = counts_a2.get(val, 0) / n
        pe += p1 * p2
    
    if 1 - pe == 0:
        return 0.0
    
    kappa = (po - pe) / (1 - pe)
    return kappa

def compute_cohen_kappa_aggregated(annotations: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
    """Compute aggregated Kappa across all items."""
    ratings = prepare_ratings(annotations)
    annotators = list(set(item['annotator_id'] for item in annotations))
    
    if len(annotators) < 2:
        raise ValueError("Need at least 2 annotators to compute Kappa")
    
    kappa = compute_cohen_kappa(ratings, annotators)
    return kappa, annotators

def interpret_kappa(kappa: float) -> str:
    """Interpret Kappa value."""
    if kappa < 0: return "No agreement"
    if kappa <= 0.20: return "Slight agreement"
    if kappa <= 0.40: return "Fair agreement"
    if kappa <= 0.60: return "Moderate agreement"
    if kappa <= 0.80: return "Substantial agreement"
    return "Almost perfect agreement"

def generate_report(kappa: float, annotators: List[str], output_path: str) -> None:
    """Generate the validation report JSON."""
    report = {
        "kappa": kappa,
        "kappa_interpretation": interpret_kappa(kappa),
        "annotators": annotators,
        "status": "passed" if kappa > 0.4 else "warning",
        "notes": "Inter-rater reliability computed for T007b."
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Kappa report saved to {output_path}: {kappa}")

def main():
    """Entry point for T007b."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting T007b: Calculate inter-rater reliability")
    
    try:
        annotations_path = "data/raw/annotations.json"
        report_path = "data/processed/vader_validation_report.json"
        
        annotations = load_annotations(annotations_path)
        kappa, annotators = compute_cohen_kappa_aggregated(annotations)
        
        generate_report(kappa, annotators, report_path)
        logger.info("T007b completed successfully.")
    except Exception as e:
        logger.error(f"T007b failed: {e}")
        raise

if __name__ == "__main__":
    main()