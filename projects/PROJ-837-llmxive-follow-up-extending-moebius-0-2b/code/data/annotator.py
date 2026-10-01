import os
import json
import csv
import math
import argparse
import random
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from config import get_mode, is_ci_mode, is_research_mode, get_path
from utils.logger import get_logger, setup_project_logger

logger = setup_project_logger("annotator")

def log_validation_result(log_path: str, message: str) -> None:
    """Log a validation result to a file."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'a') as f:
        f.write(f"[{message}]\n")

def validate_sample_size(scores: List[Dict], min_size: int = 50) -> bool:
    """Validate that the sample size is sufficient."""
    if len(scores) < min_size:
        logger.error(f"Sample size {len(scores)} is below minimum {min_size}")
        return False
    return True

def validate_label_independence(scores: List[Dict], metrics: List[Dict]) -> bool:
    """
    Validate that labels are independent of metrics.
    In CI mode, we explicitly decouple them.
    """
    # This is a placeholder check. Real independence is ensured by generation logic.
    return True

def generate_ci_scores(seed: int, sample_size: int = 50) -> List[Dict[str, Any]]:
    """
    Generate decoupled random scores for CI mode.
    Strictly independent of mask metrics.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    scores = []
    for i in range(sample_size):
        # Generate score strictly from random, decoupled from any metrics
        score = np.random.uniform(1.0, 5.0)
        scores.append({
            "image_id": f"ci_img_{i:04d}",
            "score": round(score, 2),
            "mode": "CI_MODE",
            "seed_used": seed,
            "rater_id": "simulated_rater_1" # Add rater_id for structure
        })
    
    return scores

def save_scores(scores: List[Dict], output_path: str) -> None:
    """Save scores to a CSV file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    keys = scores[0].keys() if scores else []
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(scores)

def load_research_annotations(input_path: str) -> List[Dict[str, Any]]:
    """Load human annotations from a CSV file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Human annotation file not found: {input_path}")
    
    scores = []
    with open(input_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['score'] = float(row['score'])
            scores.append(row)
    return scores

def validate_research_annotations(scores: List[Dict]) -> bool:
    """Validate research annotations schema."""
    required_keys = ['image_id', 'score', 'rater_id']
    for s in scores:
        if not all(k in s for k in required_keys):
            return False
    return True

def run_ci_mode(seed: int, sample_size: int, output_path: str, log_path: str) -> List[Dict]:
    """Run CI mode score generation."""
    logger.info("Starting CI Mode score generation.")
    scores = generate_ci_scores(seed, sample_size)
    save_scores(scores, output_path)
    
    # Log independence check
    log_validation_result(log_path, "CI Mode: Scores generated with decoupled random seed.")
    log_validation_result(log_path, f"Sample size: {sample_size}")
    log_validation_result(log_path, f"Seed used: {seed}")
    
    return scores

def run_research_mode(input_path: str, output_path: str, log_path: str) -> List[Dict]:
    """Run Research mode annotation ingestion."""
    logger.info("Starting Research Mode annotation ingestion.")
    
    try:
        scores = load_research_annotations(input_path)
    except FileNotFoundError as e:
        error_msg = f"ERROR: Human annotation file missing. Research mode disabled."
        log_validation_result(log_path, error_msg)
        logger.error(error_msg)
        raise SystemExit(1)
    
    if not validate_research_annotations(scores):
        error_msg = "ERROR: Invalid annotation schema."
        log_validation_result(log_path, error_msg)
        logger.error(error_msg)
        raise SystemExit(1)
    
    # Save validated scores
    save_scores(scores, output_path)
    log_validation_result(log_path, "Research Mode: Human annotations validated and saved.")
    
    return scores

def calculate_krippendorff_alpha(scores: List[Dict]) -> Optional[float]:
    """Placeholder for Krippendorff alpha calculation logic (delegated to stats.py)."""
    # This function is kept for API compatibility but logic is in stats.py
    return None

def run_krippendorff_analysis(scores_path: str, output_path: str, log_path: str) -> Dict:
    """Wrapper to run Krippendorff analysis from stats.py."""
    from eval.stats import calculate_krippendorff_alpha
    return calculate_krippendorff_alpha(scores_path, output_path, log_path)

def main():
    parser = argparse.ArgumentParser(description="Annotator CLI")
    parser.add_argument('--mode', type=str, default='CI', choices=['CI', 'RESEARCH'],
                        help='Run mode')
    parser.add_argument('--participants', action='store_true',
                        help='Flag to indicate participant mode (Research)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for CI mode')
    parser.add_argument('--sample-size', type=int, default=50, help='Sample size for CI mode')
    parser.add_argument('--input', type=str, default='data/annotations/human_scores.csv',
                        help='Input file for Research mode')
    parser.add_argument('--output', type=str, default='data/annotations/validated_scores.csv',
                        help='Output file for scores')
    parser.add_argument('--log', type=str, default='data/results/validation_log.txt',
                        help='Log file path')
    
    args = parser.parse_args()
    
    mode = 'RESEARCH' if args.participants else args.mode
    
    if mode == 'CI':
        scores = run_ci_mode(args.seed, args.sample_size, args.output, args.log)
        logger.info(f"Generated {len(scores)} CI scores.")
    else:
        scores = run_research_mode(args.input, args.output, args.log)
        logger.info(f"Loaded and validated {len(scores)} human scores.")
        
        # Run Krippendorff analysis if in Research mode and we have data
        if len(scores) > 0:
            try:
                result = run_krippendorff_analysis(args.output, 
                                                   args.output.replace('validated_scores.csv', 'krippendorff_raw.json'),
                                                   args.log)
                logger.info(f"Krippendorff Alpha: {result.get('alpha', 'N/A')}")
            except Exception as e:
                logger.error(f"Krippendorff analysis failed: {e}")
                # Do not exit, just log error, as T015 is a separate task
                # But if T015 is required, this might need to exit.
                # For now, we log and continue.

if __name__ == '__main__':
    main()
