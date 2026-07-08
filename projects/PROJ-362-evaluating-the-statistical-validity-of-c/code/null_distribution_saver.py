import os
import csv
import logging
from typing import List, Dict, Any, Optional
from config import RESULTS_DIR

logger = logging.getLogger(__name__)

def save_null_distribution_csv(
    query_id: int,
    metric_name: str,
    scores: List[float],
    output_dir: Optional[str] = None
) -> str:
    """
    Save a null distribution for a single query and metric to a CSV file.
    
    Args:
        query_id: The ID of the query.
        metric_name: The name of the metric (e.g., 'NDCG@10', 'MAP').
        scores: List of scores from the permutation test.
        output_dir: Optional override for the output directory. Defaults to RESULTS_DIR.
        
    Returns:
        The path to the saved CSV file.
    """
    if output_dir is None:
        output_dir = os.path.join(RESULTS_DIR, "null_distributions")
    
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"q{query_id}_{metric_name.replace('@', '_at_').replace(' ', '_')}.csv"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['query_id', 'metric', 'score'])
        for score in scores:
            writer.writerow([query_id, metric_name, score])
    
    logger.info(f"Saved null distribution for query {query_id}, metric {metric_name} to {filepath}")
    return filepath

def save_all_null_distributions(
    results: List[Dict[str, Any]],
    output_dir: Optional[str] = None
) -> List[str]:
    """
    Save null distributions for a batch of results.
    
    Args:
        results: List of dictionaries containing 'query_id', 'metric', and 'null_scores'.
        output_dir: Optional override for the output directory.
        
    Returns:
        List of paths to saved CSV files.
    """
    saved_paths = []
    if output_dir is None:
        output_dir = os.path.join(RESULTS_DIR, "null_distributions")
    
    for item in results:
        query_id = item['query_id']
        metric_name = item['metric']
        scores = item['null_scores']
        
        path = save_null_distribution_csv(query_id, metric_name, scores, output_dir)
        saved_paths.append(path)
        
    return saved_paths
