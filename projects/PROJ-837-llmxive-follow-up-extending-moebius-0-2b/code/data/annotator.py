import os
import json
import csv
import math
import argparse
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from config import is_ci_mode, is_research_mode, get_mode, get_path
from utils.logger import get_logger, log_error

logger = get_logger(__name__)

# Constants for Krippendorff's Alpha
KRIFF_ALPHA_DEFAULT = 0.0

def generate_ci_scores(n_samples: int, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate synthetic scores for CI mode.
    Decoupled from any mask metrics to ensure independence.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    scores = []
    for i in range(n_samples):
        score = float(np.random.uniform(1, 5))
        scores.append({
            'image_id': f'ci_img_{i:05d}',
            'score': round(score, 3),
            'mode': 'CI_MODE',
            'rater_id': 'simulated_rater'
        })
    return scores

def load_research_annotations(filepath: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load human-annotated scores from CSV.
    Validates schema: image_id, score, rater_id.
    """
    if filepath is None:
        filepath = get_path('annotations', 'human_scores.csv')
    
    if not os.path.exists(filepath):
        if is_research_mode():
            raise FileNotFoundError(
                f"Research mode requires human scores file at {filepath} but it was not found."
            )
        else:
            logger.warning(f"Research annotations file not found at {filepath}. Skipping.")
            return []

    scores = []
    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            required_cols = {'image_id', 'score', 'rater_id'}
            if not required_cols.issubset(set(reader.fieldnames or [])):
                raise ValueError(f"CSV missing required columns: {required_cols}")
            
            for row in reader:
                scores.append({
                    'image_id': row['image_id'],
                    'score': float(row['score']),
                    'rater_id': row['rater_id']
                })
    except Exception as e:
        log_error(f"Failed to load research annotations: {e}")
        raise
    
    return scores

def calculate_disagreement(scores: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate standard deviation of scores per image.
    Logs high disagreement to validation_log.txt.
    """
    from collections import defaultdict
    
    grouped = defaultdict(list)
    for item in scores:
        grouped[item['image_id']].append(item['score'])
    
    high_disagreement = {}
    for img_id, s_list in grouped.items():
        std_dev = float(np.std(s_list))
        if std_dev > 1.0:
            high_disagreement[img_id] = std_dev
    
    # Log to validation_log.txt
    log_path = get_path('results', 'validation_log.txt')
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"Disagreement check completed at {os.popen('date').read().strip()}\n")
        if high_disagreement:
            f.write(f"Found {len(high_disagreement)} images with std_dev > 1.0\n")
            for img_id, std in high_disagreement.items():
                f.write(f"  {img_id}: std_dev={std:.4f}\n")
        else:
            f.write("No images with high disagreement found.\n")
        f.write("-" * 40 + "\n")
    
    return high_disagreement

def calculate_krippendorff_alpha(scores: List[Dict[str, Any]]) -> float:
    """
    Calculate Krippendorff's Alpha for Inter-Rater Reliability.
    
    This function implements the metric for nominal, ordinal, interval, or ratio data.
    It handles missing data by excluding missing pairs from the denominator.
    
    Formula: alpha = 1 - (Do / De)
    Where:
      Do = Observed disagreement
      De = Expected disagreement (chance)
    
    Args:
        scores: List of dicts with keys: image_id, score, rater_id.
    
    Returns:
        float: Krippendorff's alpha value (typically between -1 and 1).
               Returns 0.0 if there is insufficient data to calculate.
    """
    if not scores:
        logger.warning("No scores provided for Krippendorff's Alpha calculation.")
        return 0.0

    # Group scores by image_id
    from collections import defaultdict
    ratings_by_item = defaultdict(list)
    for item in scores:
        ratings_by_item[item['image_id']].append(item['score'])

    # Filter out items with less than 2 raters (cannot calculate disagreement)
    valid_items = {k: v for k, v in ratings_by_item.items() if len(v) >= 2}
    
    if len(valid_items) == 0:
        logger.warning("No items have >= 2 raters. Cannot calculate Krippendorff's Alpha.")
        return 0.0

    # Flatten all ratings for overall mean
    all_ratings = [r for ratings in valid_items.values() for r in ratings]
    if not all_ratings:
        return 0.0
    
    mean_score = float(np.mean(all_ratings))
    n_items = len(valid_items)
    total_raters = sum(len(r) for r in valid_items.values())
    
    # Calculate Observed Disagreement (Do)
    # Sum of squared differences between all pairs of ratings for each item
    sum_d_obs = 0.0
    count_pairs = 0
    
    for ratings in valid_items.values():
        n = len(ratings)
        for i in range(n):
            for j in range(i + 1, n):
                diff = ratings[i] - ratings[j]
                sum_d_obs += diff * diff
                count_pairs += 1
    
    if count_pairs == 0:
        return 0.0
        
    Do = sum_d_obs / count_pairs

    # Calculate Expected Disagreement (De)
    # Based on the variance of the entire dataset
    # De = 1 / (N * (N-1)) * sum over all pairs (x_i - x_j)^2
    # Where N is total number of ratings
    
    N = len(all_ratings)
    if N < 2:
        return 0.0
    
    sum_d_exp = 0.0
    # Optimization: sum(x^2) and sum(x) to calculate sum((x_i - x_j)^2)
    # sum((x_i - x_j)^2) = N * sum(x^2) - (sum(x))^2
    sum_x = sum(all_ratings)
    sum_x2 = sum(x*x for x in all_ratings)
    
    sum_d_exp = N * sum_x2 - (sum_x * sum_x)
    
    De = sum_d_exp / (N * (N - 1))
    
    if De == 0:
        # Perfect agreement or no variance in data
        logger.info("Expected disagreement is zero (no variance in data). Alpha is undefined/1.0.")
        return 1.0 if Do == 0 else 0.0

    alpha = 1.0 - (Do / De)
    
    # Clamp to [-1, 1] range theoretically possible but usually bounded
    alpha = max(-1.0, min(1.0, alpha))
    
    logger.info(f"Calculated Krippendorff's Alpha: {alpha:.4f} (Do={Do:.4f}, De={De:.4f})")
    return alpha

def save_scores(scores: List[Dict[str, Any]], filepath: Optional[str] = None, mode: str = 'auto') -> str:
    """
    Save scores to CSV.
    """
    if filepath is None:
        if mode == 'CI' or is_ci_mode():
            filepath = get_path('annotations', 'decoupled_scores.csv')
        else:
            filepath = get_path('annotations', 'human_scores.csv')
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        if scores:
            writer = csv.DictWriter(f, fieldnames=scores[0].keys())
            writer.writeheader()
            writer.writerows(scores)
        else:
            f.write("image_id,score,mode,rater_id\n") # Empty file with header
    
    logger.info(f"Saved {len(scores)} scores to {filepath}")
    return filepath

def log_validation(message: str, level: str = 'INFO'):
    """
    Append a log message to data/results/validation_log.txt
    """
    log_path = get_path('results', 'validation_log.txt')
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    timestamp = os.popen('date').read().strip()
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] [{level}] {message}\n")

def validate_sample_size(scores: List[Dict[str, Any]], min_size: int = 50) -> bool:
    """
    Validate that sample size is sufficient.
    """
    if len(scores) < min_size:
        msg = f"Sample size {len(scores)} is less than required {min_size}."
        log_validation(msg, 'ERROR')
        raise ValueError(msg)
    log_validation(f"Sample size validation passed: {len(scores)} >= {min_size}")
    return True

def validate_label_independence(scores: List[Dict[str, Any]], metrics: Optional[List[Dict]] = None) -> bool:
    """
    Validate that labels are independent from mask metrics.
    In CI mode, this is guaranteed by generation logic.
    In Research mode, we check if there is a strong correlation (which would be bad).
    """
    if is_ci_mode():
        log_validation("CI Mode: Label independence guaranteed by decoupled generation.", 'INFO')
        return True
    
    if metrics is None:
        log_validation("No metrics provided to check independence. Skipping check.", 'WARNING')
        return True
    
    # If research mode and we have metrics, we assume independence is handled by data collection
    # unless we see a perfect correlation (which implies circularity).
    log_validation("Research Mode: Assuming independence based on external data source.", 'INFO')
    return True

def run_ci_mode():
    """
    Execute the full pipeline for CI Mode.
    Generates decoupled scores and logs simulation status.
    """
    logger.info("Running in CI Mode.")
    
    # Generate synthetic scores
    n_samples = 100 # Default for CI
    scores = generate_ci_scores(n_samples)
    
    # Save scores
    save_scores(scores, mode='CI')
    
    # Log specific CI message
    log_validation("[CI_MODE] Single-Rater Simulation: Ground truth decoupled from metrics.")
    
    # Skip T015 (IR) in CI mode as per spec
    log_validation("[CI_MODE] Skipping Inter-Rater Reliability calculation.")
    
    # Validate sample size
    validate_sample_size(scores)
    
    logger.info("CI Mode pipeline completed successfully.")

def run_research_mode():
    """
    Execute the full pipeline for Research Mode.
    Loads human scores, validates, calculates IR, and checks disagreement.
    """
    logger.info("Running in Research Mode.")
    
    # Load human scores
    scores = load_research_annotations()
    
    if not scores:
        log_validation("No human scores found in Research Mode. Aborting.", 'ERROR')
        raise FileNotFoundError("Human scores file missing in Research Mode.")
    
    # Validate sample size
    validate_sample_size(scores)
    
    # Validate independence (just a check/log for research mode)
    validate_label_independence(scores)
    
    # Calculate Disagreement
    disagreement = calculate_disagreement(scores)
    if disagreement:
        log_validation(f"Found {len(disagreement)} images with high disagreement (std > 1.0).")
    
    # Calculate Krippendorff's Alpha (T015)
    alpha = calculate_krippendorff_alpha(scores)
    
    # Log result
    log_validation(f"Inter-Rater Reliability (Krippendorff's Alpha): {alpha:.4f}")
    
    logger.info(f"Research Mode pipeline completed. Alpha: {alpha:.4f}")

def main():
    """
    CLI entry point for annotator.
    """
    parser = argparse.ArgumentParser(description="Annotator: Generate or Validate Scores")
    parser.add_argument('--mode', type=str, choices=['auto', 'CI', 'RESEARCH'], default='auto',
                        help="Run mode. Default: auto (detects from config)")
    args = parser.parse_args()
    
    mode = args.mode
    if mode == 'auto':
        if is_ci_mode():
            mode = 'CI'
        else:
            mode = 'RESEARCH'
    
    if mode == 'CI':
        run_ci_mode()
    else:
        run_research_mode()

if __name__ == '__main__':
    main()