"""
Scoring Saver Service
Implements T017: Save scored and filtered data to data/processed/scoring_results.csv
"""
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from code.config import CONFIG
from code.services.anxiety_scoring import run_full_scoring_pipeline

logger = logging.getLogger(__name__)


def save_scoring_results(
    data: pd.DataFrame,
    output_path: Optional[Path] = None
) -> Path:
    """
    Save the scored and filtered anxiety data to a CSV file.

    This function implements T017 requirements:
    - Input: DataFrame containing text, anxiety_score, and confidence_score
    - Output: data/processed/scoring_results.csv with exactly these three columns
    - Filtering: Assumes data is already filtered by confidence >= 0.6 (T016)

    Args:
        data: DataFrame with at least columns: 'text', 'anxiety_score', 'confidence_score'
        output_path: Optional path for output. Defaults to CONFIG.OUTPUT_DIR / 'scoring_results.csv'

    Returns:
        Path to the saved file

    Raises:
        ValueError: If required columns are missing from input data
        FileNotFoundError: If output directory does not exist
    """
    if output_path is None:
        output_path = CONFIG.OUTPUT_DIR / "scoring_results.csv"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Validate required columns
    required_columns = {'text', 'anxiety_score', 'confidence_score'}
    if not required_columns.issubset(data.columns):
        missing = required_columns - set(data.columns)
        raise ValueError(f"Input data missing required columns: {missing}")

    # Select only the required columns in the specified order
    output_df = data[list(required_columns)].copy()

    # Ensure no null values in critical columns
    if output_df['anxiety_score'].isnull().any() or output_df['confidence_score'].isnull().any():
        null_count = output_df['anxiety_score'].isnull().sum() + output_df['confidence_score'].isnull().sum()
        logger.warning(f"Found {null_count} null values in score columns. Dropping rows.")
        output_df = output_df.dropna(subset=['anxiety_score', 'confidence_score'])

    # Save to CSV
    output_df.to_csv(output_path, index=False)
    
    logger.info(
        f"Saved {len(output_df)} scored records to {output_path} "
        f"with columns: {list(output_df.columns)}"
    )
    
    return output_path


def run_scoring_saver_pipeline() -> Path:
    """
    Orchestrates the full scoring save pipeline:
    1. Runs the full anxiety scoring pipeline (T013-T016) to generate scored data
    2. Saves the results to data/processed/scoring_results.csv (T017)

    This function ensures that T017 is executed after T016 filtering is applied.

    Returns:
        Path to the saved scoring_results.csv file
    """
    logger.info("Starting scoring saver pipeline (T017)")

    # Run the full scoring pipeline to get processed data
    # This includes: ingestion -> filtering -> scoring -> confidence filtering
    scored_data = run_full_scoring_pipeline()

    if scored_data is None or scored_data.empty:
        logger.error("No scored data available to save. Pipeline may have failed or filtered everything.")
        raise RuntimeError("No scored data available to save")

    logger.info(f"Received {len(scored_data)} records from scoring pipeline")

    # Save the results
    output_path = save_scoring_results(scored_data)

    logger.info("Scoring saver pipeline completed successfully")
    return output_path