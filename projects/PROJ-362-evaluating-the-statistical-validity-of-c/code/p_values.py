"""
P-value calculation logic for permutation tests.
Implements the rank-based estimator: (r + 1) / (N + 1).
"""
import os
import csv
import logging
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from config import RESULTS_DIR, ensure_dirs

logger = logging.getLogger(__name__)

def calculate_p_value(null_scores: List[float], observed_score: float) -> float:
    """
    Calculate the p-value using the rank-based estimator.
    
    Formula: (r + 1) / (N + 1)
    where:
      - r is the count of null scores >= observed_score
      - N is the total number of permutations (len(null_scores))
    
    Args:
        null_scores: List of scores from the null distribution.
        observed_score: The observed metric score to test against.
    
    Returns:
        The calculated p-value.
    """
    if not null_scores:
        logger.warning("Null scores list is empty. Returning 1.0.")
        return 1.0
    
    N = len(null_scores)
    # Count how many null scores are greater than or equal to the observed score
    r = sum(1 for score in null_scores if score >= observed_score)
    
    p_val = (r + 1) / (N + 1)
    return p_val

def process_null_distributions(null_distributions_path: str, 
                               observed_scores_path: str) -> Dict[str, Dict[str, float]]:
    """
    Process null distribution files and observed scores to calculate p-values.
    
    Args:
        null_distributions_path: Path to directory containing null distribution CSVs.
        observed_scores_path: Path to CSV containing observed scores.
    
    Returns:
        Dictionary mapping (query_id, metric) -> p_value.
    """
    logger.info(f"Processing null distributions from {null_distributions_path}")
    
    # Load observed scores
    observed_scores = {}
    if os.path.exists(observed_scores_path):
        with open(observed_scores_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row['query_id'], row['metric'])
                observed_scores[key] = float(row['score'])
    else:
        logger.warning(f"Observed scores file not found: {observed_scores_path}")
    
    p_values = {}
    
    # Iterate over null distribution files
    # Assuming files are named like: qrels_{query_id}_ndcg.csv or similar
    # We'll read all CSVs in the directory
    if not os.path.exists(null_distributions_path):
        logger.error(f"Null distributions path does not exist: {null_distributions_path}")
        return p_values
        
    for filename in os.listdir(null_distributions_path):
        if filename.endswith('.csv'):
            file_path = os.path.join(null_distributions_path, filename)
            try:
                with open(file_path, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    # Group scores by metric
                    scores_by_metric = {}
                    query_id = None
                    
                    for row in reader:
                        qid = row.get('query_id')
                        if qid:
                            query_id = qid
                        metric = row.get('metric')
                        score = float(row.get('score', 0))
                        
                        if metric not in scores_by_metric:
                            scores_by_metric[metric] = []
                        scores_by_metric[metric].append(score)
                    
                    if not query_id:
                        continue
                        
                    for metric, scores in scores_by_metric.items():
                        key = (query_id, metric)
                        if key in observed_scores:
                            obs = observed_scores[key]
                            p_val = calculate_p_value(scores, obs)
                            p_values[key] = p_val
                            logger.debug(f"Query {query_id}, Metric {metric}: Obs={obs:.4f}, P={p_val:.4f}")
                        else:
                            logger.warning(f"No observed score found for {key}")
            except Exception as e:
                logger.error(f"Error processing file {filename}: {e}")
    
    return p_values

def run_p_value_calculation():
    """
    Main entry point to run p-value calculation.
    Reads null distributions and observed scores, calculates p-values, and saves them.
    """
    ensure_dirs()
    
    null_dist_path = os.path.join(RESULTS_DIR, 'null_distributions')
    obs_scores_path = os.path.join(RESULTS_DIR, 'config', 'observed_scores.csv')
    output_path = os.path.join(RESULTS_DIR, 'p_values', 'raw_p_values.csv')
    
    p_values = process_null_distributions(null_dist_path, obs_scores_path)
    
    if not p_values:
        logger.warning("No p-values calculated. Check input files.")
        return
    
    # Save p-values
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['query_id', 'metric', 'raw_p'])
        for (qid, metric), p_val in p_values.items():
            writer.writerow([qid, metric, p_val])
    
    logger.info(f"Saved p-values to {output_path}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_p_value_calculation()