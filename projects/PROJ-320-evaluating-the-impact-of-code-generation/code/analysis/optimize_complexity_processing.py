"""
Optimized complexity analysis with memory management for large PR datasets.

This module provides an optimized version of complexity analysis that processes
PR diffs in batches to avoid memory overflow, leveraging the batch processing
utilities from code/utils/batch_processor.py.
"""
import os
import json
import ast
import tokenize
import io
from pathlib import Path
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
from analysis.complexity import calculate_loc, calculate_cyclomatic_complexity, analyze_diff_complexity

logger = get_logger(__name__)

def process_complexity_batch(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single PR row to calculate complexity scores.
    
    Args:
        row: Dictionary containing PR data including 'pr_id' and 'diff'.
        
    Returns:
        Dictionary with 'pr_id' and 'complexity_score'.
    """
    pr_id = int(row.get('pr_id', 0))
    diff_text = row.get('diff', '')
    
    if not diff_text or diff_text.strip() == '':
        # If no diff, assign a default low complexity
        return {
            'pr_id': pr_id,
            'complexity_score': 0.0
        }
        
    try:
        # Analyze the diff for complexity
        loc, cc = analyze_diff_complexity(diff_text)
        
        # Normalize complexity score (0-10 scale based on CC)
        # CC <= 1: 0, CC 2-5: 2, CC 6-10: 5, CC 11-20: 7, CC > 20: 10
        if cc <= 1:
            score = 0.0
        elif cc <= 5:
            score = 2.0
        elif cc <= 10:
            score = 5.0
        elif cc <= 20:
            score = 7.0
        else:
            score = 10.0
            
        return {
            'pr_id': pr_id,
            'complexity_score': score,
            'loc': loc,
            'cyclomatic_complexity': cc
        }
    except Exception as e:
        logger.error(f"Error calculating complexity for PR {pr_id}: {e}")
        # Fallback to default
        return {
            'pr_id': pr_id,
            'complexity_score': 0.0,
            'loc': 0,
            'cyclomatic_complexity': 0
        }

def run_optimized_complexity_analysis(
    input_path: Path,
    output_path: Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE
) -> int:
    """
    Run complexity analysis on a large dataset using batch processing.
    
    Args:
        input_path: Path to input CSV (prs_labeled.csv).
        output_path: Path to output CSV (complexity_scores.csv).
        chunk_size: Number of rows per batch.
        
    Returns:
        int: Total number of PRs processed.
    """
    logger.info(f"Starting optimized complexity analysis on {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    with memory_monitor():
        total_processed = process_in_batches(
            input_path=input_path,
            output_path=output_path,
            processor_func=process_complexity_batch,
            chunk_size=chunk_size
        )
        
    logger.info(f"Optimized complexity analysis complete. Processed {total_processed} PRs.")
    return total_processed

def main():
    """
    Main entry point for optimized complexity analysis.
    """
    setup_logging()
    config = get_config_summary()
    
    input_file = Path("data/processed/prs_labeled.csv")
    output_file = Path("data/processed/complexity_scores.csv")
    
    if not input_file.exists():
        logger.error(f"Input file {input_file} does not exist. Cannot run analysis.")
        return
        
    logger.info(f"Running optimized complexity analysis...")
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_file}")
    
    try:
        count = run_optimized_complexity_analysis(input_file, output_file)
        logger.info(f"Successfully processed {count} PRs.")
    except Exception as e:
        logger.error(f"Error during optimized complexity analysis: {e}")
        raise

if __name__ == "__main__":
    main()
