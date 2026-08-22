import os
import csv
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from config import RESULTS_DIR, ensure_dirs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_null_distribution_csv(
    query_id: int,
    metric: str,
    scores: List[float],
    output_dir: Optional[Path] = None
) -> Path:
    """
    Save a single query's null distribution to a CSV file.
    
    Args:
        query_id: The query identifier.
        metric: The metric name (e.g., 'NDCG@10', 'MAP').
        scores: List of scores from the permutations.
        output_dir: Directory to save the file. Defaults to RESULTS_DIR/null_distributions.
    
    Returns:
        Path to the created CSV file.
    """
    if output_dir is None:
        output_dir = RESULTS_DIR / "null_distributions"
    
    ensure_dirs(output_dir)
    
    filename = f"q{query_id}_{metric}.csv"
    file_path = output_dir / filename
    
    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['query_id', 'metric', 'score'])
        for score in scores:
            writer.writerow([query_id, metric, score])
    
    logger.info(f"Saved null distribution for query {query_id}, metric {metric} to {file_path}")
    return file_path

def save_all_null_distributions(
    distributions: Dict[int, Dict[str, List[float]]],
    output_dir: Optional[Path] = None
) -> List[Path]:
    """
    Save all null distributions to individual CSV files.
    
    Args:
        distributions: Dict mapping query_id -> {metric -> List[scores]}.
        output_dir: Directory to save files.
    
    Returns:
        List of paths to created files.
    """
    if output_dir is None:
        output_dir = RESULTS_DIR / "null_distributions"
    
    ensure_dirs(output_dir)
    created_files = []
    
    for query_id, metrics_data in distributions.items():
        for metric, scores in metrics_data.items():
            file_path = save_null_distribution_csv(query_id, metric, scores, output_dir)
            created_files.append(file_path)
    
    logger.info(f"Saved {len(created_files)} null distribution files.")
    return created_files

def run_null_distribution_saving(
    distributions: Dict[int, Dict[str, List[float]]],
    output_dir: Optional[Path] = None
) -> List[Path]:
    """
    Entry point for saving null distributions, typically called from main.py.
    
    Args:
        distributions: Dict of query_id -> metric -> scores.
        output_dir: Optional output directory override.
    
    Returns:
        List of created file paths.
    """
    return save_all_null_distributions(distributions, output_dir)
