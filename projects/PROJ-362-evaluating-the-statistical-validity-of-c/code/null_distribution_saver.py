"""
Module to save null distribution CSVs to disk.

This module handles the serialization of permutation test results
into CSV format as required by T017.
"""
import os
import csv
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import config to ensure directories exist
# The API surface indicates 'ensure_dirs' is available in config
try:
    from config import RESULTS_DIR, ensure_dirs
except ImportError:
    # Fallback if config is not yet fully populated in the environment
    # This should not happen in a correctly set up project
    RESULTS_DIR = Path("results")
    def ensure_dirs(path: Path):
        path.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

def save_null_distribution_csv(
    query_id: int,
    metric: str,
    scores: List[float],
    output_dir: Optional[Path] = None
) -> Path:
    """
    Save the null distribution for a single query and metric to a CSV file.
    
    Args:
        query_id: The unique identifier for the query.
        metric: The name of the metric (e.g., 'NDCG@10', 'MAP').
        scores: List of scores from the permuted distributions.
        output_dir: Optional directory path. Defaults to RESULTS_DIR / 'null_distributions'.
        
    Returns:
        Path to the created CSV file.
    """
    if output_dir is None:
        output_dir = RESULTS_DIR / "null_distributions"
    
    ensure_dirs(output_dir)
    
    filename = f"q{query_id}_{metric}.csv"
    file_path = output_dir / filename
    
    logger.info(f"Saving null distribution for Query {query_id}, Metric {metric} to {file_path}")
    
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write header as required by T017: query_id, metric, score
        writer.writerow(['query_id', 'metric', 'score'])
        
        # Write each score
        for score in scores:
            writer.writerow([query_id, metric, f"{score:.6f}"])
    
    logger.info(f"Successfully saved {len(scores)} scores to {file_path}")
    return file_path

def save_all_null_distributions(
    distributions: Dict[str, List[float]],
    query_id: int,
    metrics: List[str],
    output_dir: Optional[Path] = None
) -> List[Path]:
    """
    Save null distributions for multiple metrics for a single query.
    
    Args:
        distributions: Dictionary mapping metric names to lists of scores.
                       e.g., {'NDCG@10': [0.1, 0.2, ...], 'MAP': [0.05, ...]}
        query_id: The query identifier.
        metrics: List of metric names to process.
        output_dir: Optional output directory.
        
    Returns:
        List of paths to the created CSV files.
    """
    if output_dir is None:
        output_dir = RESULTS_DIR / "null_distributions"
        
    ensure_dirs(output_dir)
    saved_paths = []
    
    for metric in metrics:
        if metric in distributions:
            scores = distributions[metric]
            if not scores:
                logger.warning(f"No scores generated for Query {query_id}, Metric {metric}. Skipping save.")
                continue
            
            path = save_null_distribution_csv(query_id, metric, scores, output_dir)
            saved_paths.append(path)
        else:
            logger.warning(f"Metric {metric} not found in distributions for Query {query_id}.")
            
    return saved_paths