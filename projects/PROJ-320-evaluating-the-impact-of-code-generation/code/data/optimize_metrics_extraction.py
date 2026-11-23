"""
Optimized metrics extraction with memory management for large PR datasets.

This module provides an optimized version of metrics extraction that processes
PRs in batches to avoid memory overflow, leveraging the batch processing
utilities from code/utils/batch_processor.py.
"""
import os
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

from utils.logging import get_logger, setup_logging
from utils.config import get_config_summary
from utils.batch_processor import (
    chunked_reader,
    process_in_batches,
    force_gc_if_needed,
    memory_monitor,
    DEFAULT_CHUNK_SIZE
)
from data.extract_metrics import (
    load_prs_labeled,
    load_complexity_scores,
    parse_timestamp,
    calculate_time_to_merge_minutes,
    calculate_review_cycles,
    extract_comment_count
)

logger = get_logger(__name__)

def process_metrics_batch(row: Dict[str, Any], complexity_lookup: Dict[int, float]) -> Dict[str, Any]:
    """
    Process a single PR row to extract metrics.
    
    Args:
        row: Dictionary containing PR data.
        complexity_lookup: Dictionary mapping pr_id to complexity_score.
        
    Returns:
        Dictionary with PR metrics.
    """
    pr_id = int(row.get('pr_id', 0))
    
    # Extract basic metrics
    comment_count = extract_comment_count(row)
    time_to_merge = calculate_time_to_merge_minutes(row)
    review_cycles = calculate_review_cycles(row)
    
    # Get complexity score from lookup
    complexity_score = complexity_lookup.get(pr_id, 0.0)
    
    return {
        'pr_id': pr_id,
        'source_type': row.get('source_type', 'unknown'),
        'comment_count': comment_count,
        'time_to_merge_minutes': time_to_merge,
        'review_cycles': review_cycles,
        'complexity_score': complexity_score
    }

def run_optimized_metrics_extraction(
    labeled_path: Path,
    complexity_path: Path,
    output_path: Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE
) -> int:
    """
    Run metrics extraction on a large dataset using batch processing.
    
    Args:
        labeled_path: Path to prs_labeled.csv.
        complexity_path: Path to complexity_scores.csv.
        output_path: Path to output metrics CSV.
        chunk_size: Number of rows per batch.
        
    Returns:
        int: Total number of PRs processed.
    """
    logger.info(f"Starting optimized metrics extraction...")
    
    if not labeled_path.exists():
        raise FileNotFoundError(f"Labeled file not found: {labeled_path}")
    if not complexity_path.exists():
        raise FileNotFoundError(f"Complexity file not found: {complexity_path}")
        
    # Load complexity scores into memory (usually smaller dataset)
    logger.info(f"Loading complexity scores from {complexity_path}...")
    complexity_lookup = {}
    with open(complexity_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
          pr_id = int(row['pr_id'])
          complexity_lookup[pr_id] = float(row['complexity_score'])
    logger.info(f"Loaded {len(complexity_lookup)} complexity scores.")
    
    with memory_monitor():
        total_processed = process_in_batches(
            input_path=labeled_path,
            output_path=output_path,
            processor_func=lambda row: process_metrics_batch(row, complexity_lookup),
            chunk_size=chunk_size
        )
        
    logger.info(f"Optimized metrics extraction complete. Processed {total_processed} PRs.")
    return total_processed

def main():
    """
    Main entry point for optimized metrics extraction.
    """
    setup_logging()
    config = get_config_summary()
    
    labeled_file = Path("data/processed/prs_labeled.csv")
    complexity_file = Path("data/processed/complexity_scores.csv")
    output_file = Path("data/processed/prs_metrics.csv")
    
    if not labeled_file.exists():
        logger.error(f"Input file {labeled_file} does not exist. Cannot run extraction.")
        return
        
    logger.info(f"Running optimized metrics extraction...")
    logger.info(f"Labeled input: {labeled_file}")
    logger.info(f"Complexity input: {complexity_file}")
    logger.info(f"Output: {output_file}")
    
    try:
        count = run_optimized_metrics_extraction(labeled_file, complexity_file, output_file)
        logger.info(f"Successfully processed {count} PRs.")
    except Exception as e:
        logger.error(f"Error during optimized metrics extraction: {e}")
        raise

if __name__ == "__main__":
    main()