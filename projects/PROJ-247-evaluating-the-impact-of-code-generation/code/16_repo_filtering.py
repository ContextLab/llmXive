"""
Task T016: Enforce repository inclusion criteria.

Excludes repos with <5 LLM and <5 Human blocks after tagging.
Filters matched_pairs.csv to matched_pairs_filtered.csv.
Logs excluded repos to repo_exclusions.csv.
"""
import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict

# Import from existing API surface
from utils.logging_config import setup_logging, get_logger
from utils.models import MatchedPair
from utils.repo_filter import (
    load_matched_pairs,
    count_blocks_by_repo_and_label,
    identify_excluded_repos,
    filter_matched_pairs,
    save_exclusions_log,
    save_filtered_pairs,
    run_repo_filtering_pipeline
)

# Constants
MIN_LLm_BLOCKS = 5
MIN_HUMAN_BLOCKS = 5

def main():
    """Main entry point for T016 repository filtering."""
    logger = setup_logging("repo_filtering")
    logger.info("Starting T016: Repository inclusion criteria enforcement")
    
    # Define paths
    input_path = Path("data/processed/matched_pairs.csv")
    output_path = Path("data/processed/matched_pairs_filtered.csv")
    exclusions_log_path = Path("data/logs/repo_exclusions.csv")
    
    # Validate input file exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Prerequisite T015 (matching) must be completed first.")
        sys.exit(1)
    
    try:
        # Run the filtering pipeline
        filtered_pairs, excluded_repos = run_repo_filtering_pipeline(
            input_path=input_path,
            output_path=output_path,
            exclusions_log_path=exclusions_log_path,
            min_llm_blocks=MIN_LLm_BLOCKS,
            min_human_blocks=MIN_HUMAN_BLOCKS
        )
        
        # Log results
        logger.info(f"Processed {input_path}")
        logger.info(f"Excluded {len(excluded_repos)} repositories")
        logger.info(f"Filtered pairs saved to: {output_path}")
        logger.info(f"Exclusions log saved to: {exclusions_log_path}")
        
        # Summary statistics
        if filtered_pairs:
            total_pairs = len(filtered_pairs)
            llm_pairs = sum(1 for p in filtered_pairs if p.llm_block_id)
            human_pairs = sum(1 for p in filtered_pairs if p.human_block_id)
            logger.info(f"Total matched pairs after filtering: {total_pairs}")
            logger.info(f"LLM blocks: {llm_pairs}, Human blocks: {human_pairs}")
        else:
            logger.warning("No matched pairs passed the filtering criteria.")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during repository filtering: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
