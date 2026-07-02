"""
Calculate inter-rater reliability (Cohen's Kappa) on the human-annotated corpus.

This script implements T007b:
- Reads the annotations generated in T007a (data/raw/annotations.json).
- Computes Cohen's Kappa for the sentiment labels provided by multiple annotators.
- Generates a validation report at data/processed/vader_validation_report.json.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

import numpy as np
from scipy.stats import kappa2

from utils.logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ANNOTATIONS_PATH = PROJECT_ROOT / "data" / "raw" / "annotations.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_PATH = OUTPUT_DIR / "vader_validation_report.json"

def load_annotations(path: Path) -> List[Dict[str, Any]]:
    """Load the annotations JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Annotations file not found at {path}. "
                                "Ensure T007a has completed successfully.")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def prepare_ratings(annotations: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    """
    Extract pairs of ratings from the annotations.
    
    Expects annotations to be a list of dicts where each dict has:
    - 'comment_id': str
    - 'annotations': list of dicts with 'annotator_id' and 'label'
    
    Returns two lists: ratings_a and ratings_b, paired by comment_id.
    """
    comment_ratings = defaultdict(list)
    
    for entry in annotations:
        comment_id = entry.get('comment_id')
        if not comment_id:
            logger.warning(f"Skipping entry without comment_id: {entry}")
            continue
        
        annotator_labels = entry.get('annotations', [])
        if len(annotator_labels) < 2:
            logger.warning(f"Skipping comment_id {comment_id}: insufficient annotators ({len(annotator_labels)}).")
            continue
        
        # Sort by annotator_id to ensure consistent pairing if there are exactly 2
        sorted_labels = sorted(annotator_labels, key=lambda x: x.get('annotator_id', ''))
        
        # Take the first two annotators for Cohen's Kappa (requires exactly 2 raters)
        rater_a = sorted_labels[0].get('label')
        rater_b = sorted_labels[1].get('label')
        
        if rater_a is None or rater_b is None:
            logger.warning(f"Skipping comment_id {comment_id}: missing label.")
            continue
        
        comment_ratings[comment_id].append((rater_a, rater_b))
    
    # Flatten into two lists
    ratings_a = []
    ratings_b = []
    
    for comment_id, pairs in comment_ratings.items():
        for a, b in pairs:
            ratings_a.append(a)
            ratings_b.append(b)
    
    if len(ratings_a) == 0:
        raise ValueError("No valid rating pairs found in annotations.")
    
    return ratings_a, ratings_b

def compute_cohen_kappa(ratings_a: List[str], ratings_b: List[str]) -> Dict[str, Any]:
    """
    Compute Cohen's Kappa and summary statistics.
    
    Returns a dict with:
    - kappa: float
    - n_pairs: int
    - agreement_observed: float
    - agreement_expected: float
    - categories: list of unique categories observed
    """
    # Convert to numpy arrays for calculation
    arr_a = np.array(ratings_a)
    arr_b = np.array(ratings_b)
    
    n = len(arr_a)
    if n == 0:
        raise ValueError("Empty rating arrays provided.")
    
    # Calculate observed agreement
    agreement_observed = np.mean(arr_a == arr_b)
    
    # Calculate expected agreement
    # Get unique categories
    categories = sorted(list(set(arr_a) | set(arr_b)))
    n_cats = len(categories)
    
    # Calculate marginal probabilities
    p_a = np.array([np.sum(arr_a == cat) / n for cat in categories])
    p_b = np.array([np.sum(arr_b == cat) / n for cat in categories])
    
    agreement_expected = np.dot(p_a, p_b)
    
    # Calculate Kappa
    if agreement_expected == 1.0:
        kappa = 0.0  # Avoid division by zero if perfect agreement by chance
    else:
        kappa = (agreement_observed - agreement_expected) / (1 - agreement_expected)
    
    return {
        "kappa": float(kappa),
        "n_pairs": int(n),
        "agreement_observed": float(agreement_observed),
        "agreement_expected": float(agreement_expected),
        "categories": categories
    }

def generate_report(kappa_stats: Dict[str, Any]) -> Dict[str, Any]:
    """Generate the final validation report structure."""
    return {
        "status": "completed",
        "metric": "Cohen's Kappa",
        "description": "Inter-rater reliability on human-annotated sentiment corpus",
        "results": kappa_stats,
        "validation": {
            "is_valid": kappa_stats["kappa"] is not None,
            "threshold_info": "Corpus considered INVALID if Kappa is not calculated or report missing."
        },
        "metadata": {
            "script": "calculate_reliability.py",
            "task_id": "T007b"
        }
    }

def main():
    """Main entry point for T007b."""
    logger.info("Starting inter-rater reliability calculation (T007b).")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. Load annotations
        logger.info(f"Loading annotations from {ANNOTATIONS_PATH}")
        annotations = load_annotations(ANNOTATIONS_PATH)
        logger.info(f"Loaded {len(annotations)} annotation entries.")
        
        # 2. Prepare ratings
        logger.info("Preparing rating pairs...")
        ratings_a, ratings_b = prepare_ratings(annotations)
        logger.info(f"Prepared {len(ratings_a)} valid rating pairs.")
        
        # 3. Compute Kappa
        logger.info("Computing Cohen's Kappa...")
        kappa_stats = compute_cohen_kappa(ratings_a, ratings_b)
        logger.info(f"Kappa calculated: {kappa_stats['kappa']:.4f}")
        
        # 4. Generate Report
        report = generate_report(kappa_stats)
        
        # 5. Write Output
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report written to {OUTPUT_PATH}")
        logger.info("Task T007b completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during reliability calculation: {e}")
        raise

if __name__ == "__main__":
    main()
