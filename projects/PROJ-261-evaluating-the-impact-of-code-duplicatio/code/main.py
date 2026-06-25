"""
Main pipeline orchestration for User Story 1.

Joins clone-density and perplexity metrics, saves to processed CSV files.
"""
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from data_loader import load_raw_data
from ast_cloner import compute_clone_density
from model_metrics import compute_perplexity
from parse_failure_logger import init_logger, log_parse_failure

# Configure logging
logger = logging.getLogger(__name__)

# Output paths
OUTPUT_CLONE_METRICS = Path("data/processed/clone_metrics.csv")
OUTPUT_PERPLEXITY_SCORES = Path("data/processed/perplexity_scores.csv")

def setup_logging():
    """Configure logging for pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("data/pipeline.log")
        ]
    )

def save_results(clone_metrics: List[Dict[str, Any]], 
                 perplexity_scores: List[Dict[str, Any]]):
    """Save metrics to CSV files."""
    # Ensure output directory exists
    OUTPUT_CLONE_METRICS.parent.mkdir(parents=True, exist_ok=True)
    
    # Save clone metrics
    clone_df = pd.DataFrame(clone_metrics)
    clone_df.to_csv(OUTPUT_CLONE_METRICS, index=False)
    logger.info(f"Saved {len(clone_metrics)} clone metrics to {OUTPUT_CLONE_METRICS}")
    
    # Save perplexity scores
    perplexity_df = pd.DataFrame(perplexity_scores)
    perplexity_df.to_csv(OUTPUT_PERPLEXITY_SCORES, index=False)
    logger.info(f"Saved {len(perplexity_scores)} perplexity scores to {OUTPUT_PERPLEXITY_SCORES}")
    
    return len(clone_df), len(perplexity_df)

def main():
    """Main pipeline orchestration."""
    setup_logging()
    logger.info("Starting US1 pipeline orchestration")
    
    # Ensure output directories exist
    OUTPUT_CLONE_METRICS.parent.mkdir(parents=True, exist_ok=True)
    
    # Load raw data
    logger.info("Loading raw data from data/raw/github-code-sample.csv")
    raw_data = load_raw_data()
    
    if not raw_data:
        logger.error("No raw data loaded, exiting")
        return 1
    
    logger.info(f"Loaded {len(raw_data)} records from raw data")
    
    # Initialize metrics lists
    clone_metrics = []
    perplexity_scores = []
    
    # Process each record
    for idx, record in enumerate(raw_data):
        file_path = record.get('path', record.get('file_path', f'unknown_{idx}'))
        code_content = record.get('code', '')
        
        if not code_content:
            log_parse_failure(file_path, "Empty code content", "main.py")
            continue
        
        try:
            # Compute clone density
            clone_metric = compute_clone_density(code_content, file_path)
            if clone_metric:
                clone_metrics.append(clone_metric)
            
            # Compute perplexity
            perplexity = compute_perplexity(code_content, file_path)
            if perplexity:
                perplexity_scores.append(perplexity)
            
        except Exception as e:
            log_parse_failure(file_path, f"Processing error: {str(e)}", "main.py")
            logger.warning(f"Failed to process {file_path}: {e}")
            continue
        
        if (idx + 1) % 10 == 0:
            logger.info(f"Processed {idx + 1}/{len(raw_data)} records")
    
    # Save results
    clone_count, perplexity_count = save_results(clone_metrics, perplexity_scores)
    
    # Log summary
    logger.info(f"Pipeline complete: {clone_count} clone metrics, {perplexity_count} perplexity scores")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())