"""
Main entry point for the llmXive research pipeline.
Orchestrates data ingestion, validation, and diversity metric calculation.
"""
import os
import sys
import logging
import time
import json
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from ingestion import load_project_data, validate_schema, ingest_and_clean
from metrics import calculate_diversity_score
from config import get_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """
    Orchestrates the full pipeline:
    1. Load configuration
    2. Ingest and validate data
    3. Calculate diversity scores
    4. Save results to Parquet
    """
    start_time = time.time()
    logger.info("Pipeline started.")

    config = get_config()
    logger.info(f"Loaded config: seed={config.seed}, threshold={config.similarity_threshold}")

    # 1. Load and validate data
    logger.info("Loading project data...")
    raw_df = load_project_data()
    
    logger.info(f"Loaded {len(raw_df)} rows. Validating schema...")
    validate_schema(raw_df)
    
    # 2. Ingest and clean
    logger.info("Cleaning data and excluding empty enrollments...")
    cleaned_df = ingest_and_clean(raw_df)
    logger.info(f"Cleaned data shape: {cleaned_df.shape}")

    # 3. Calculate diversity scores
    logger.info("Calculating diversity scores...")
    result_df = calculate_diversity_score(cleaned_df, config.similarity_threshold)
    
    # Verify required columns exist
    required_cols = ['user_id', 'session_id', 'recommendation_diversity_score', 'learner_diversity_score']
    missing_cols = [c for c in required_cols if c not in result_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required output columns: {missing_cols}")

    # 4. Save output
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "diversity_scores.parquet"
    
    logger.info(f"Saving results to {output_path}...")
    result_df.to_parquet(output_path, index=False)
    
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Pipeline completed successfully in {duration:.2f} seconds.")
    logger.info(f"Output saved to: {output_path}")
    
    return result_df

if __name__ == "__main__":
    main()
