"""
Scoring Saver Service for User Story 1.

Responsible for saving the scored and filtered anxiety data to disk.
This module implements Task T017.
"""
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from code.config import CONFIG
from code.services.anxiety_scoring import run_full_scoring_pipeline

logger = logging.getLogger(__name__)


def save_scoring_results(
    input_data: pd.DataFrame,
    output_path: Optional[Path] = None
) -> Path:
    """
    Save scored and filtered data to CSV.
    
    Args:
        input_data: DataFrame containing 'text', 'anxiety_score', and 'confidence_score'
        output_path: Optional path to save the file. Defaults to CONFIG.OUTPUT_SCORING_RESULTS.
        
    Returns:
        Path to the saved file.
        
    Raises:
        ValueError: If input data is empty or missing required columns.
        IOError: If writing to disk fails.
    """
    if output_path is None:
        output_path = CONFIG.OUTPUT_SCORING_RESULTS
        
    logger.info(f"Saving scoring results to {output_path}")
    
    # Validate input
    if input_data.empty:
        raise ValueError("Input data is empty. Cannot save empty results.")
        
    required_columns = {'text', 'anxiety_score', 'confidence_score'}
    if not required_columns.issubset(input_data.columns):
        missing = required_columns - set(input_data.columns)
        raise ValueError(f"Input data missing required columns: {missing}")
        
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Select and order columns exactly as required by T017
    output_df = input_data[list(required_columns)].copy()
    
    # Save to CSV
    output_df.to_csv(output_path, index=False)
    
    logger.info(f"Successfully saved {len(output_df)} rows to {output_path}")
    return output_path


def run_scoring_saver_pipeline() -> Path:
    """
    Orchestrates the full scoring save pipeline:
    1. Runs the anxiety scoring pipeline (T015/T016) to get scored/filtered data.
    2. Saves the results to the configured output path.
    
    Returns:
        Path to the saved scoring results file.
    """
    logger.info("Starting scoring saver pipeline (T017)")
    
    # Run the upstream scoring pipeline to get the processed data
    # This ensures we are using the data that has already been filtered by confidence (T016)
    scored_data = run_full_scoring_pipeline()
    
    if scored_data is None or scored_data.empty:
        logger.error("Upstream scoring pipeline returned no data. Aborting save.")
        raise RuntimeError("Scoring pipeline produced no results to save.")
        
    # Save the results
    output_path = save_scoring_results(scored_data)
    
    logger.info("Scoring saver pipeline completed successfully.")
    return output_path
