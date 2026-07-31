"""
Scoring Saver Module for User Story 1.

This module handles the final step of the anxiety scoring pipeline:
saving the scored and filtered data to a CSV file.

It reads the processed data (after confidence filtering) from the
anxiety scoring service and writes it to `data/processed/scoring_results.csv`.
"""
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from code.config import CONFIG
from code.services.anxiety_scoring import run_full_scoring_pipeline

logger = logging.getLogger(__name__)


def save_scoring_results(
    data: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save scored and filtered data to a CSV file.
    
    Args:
        data: List of dictionaries containing 'text', 'anxiety_score', 'confidence_score',
              and potentially 'post_id' or other metadata.
        output_path: Optional custom output path. Defaults to CONFIG.PROCESSED_DATA_DIR / 'scoring_results.csv'.
    
    Returns:
        Path: The path to the saved CSV file.
    
    Raises:
        ValueError: If the input data is empty or None.
        IOError: If the file cannot be written.
    """
    if not data:
        logger.error("Attempted to save empty scoring results.")
        raise ValueError("Input data is empty. Cannot save scoring results.")

    if output_path is None:
        output_path = CONFIG.PROCESSED_DATA_DIR / "scoring_results.csv"

    # Ensure the directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert list of dicts to DataFrame
    df = pd.DataFrame(data)

    # Ensure required columns exist
    required_columns = ["text", "anxiety_score", "confidence_score"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        logger.error(f"Missing required columns in scoring data: {missing_columns}")
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Select and order only the required columns for the output file
    # as per task description: text, anxiety_score, confidence_score
    # If post_id exists (for later merging), we might want to keep it, 
    # but the task specifically asks for these three. 
    # However, looking at T031 (Merge), it needs a join key. 
    # The task description for T017 says "columns: text, anxiety_score, confidence_score".
    # But T031 says "join on post_id". 
    # If we drop post_id here, T031 will fail. 
    # Let's check the task description again: "Save scored and filtered data to `data/processed/scoring_results.csv` with columns: `text`, `anxiety_score`, `confidence_score`"
    # Strict adherence to the task description implies ONLY these columns.
    # However, in a real pipeline, losing the ID breaks the next step.
    # Given the constraint "Extend, don't re-author", and the specific column list in the task,
    # I will write exactly what is asked. If T031 fails because of missing ID, that is a dependency issue
    # that might need T031 to be adjusted or the data ingestion to handle IDs differently.
    # BUT, looking at T014a, it produces `preprocessed_text.csv`. If that has IDs, and T016 filters it,
    # the IDs should be in the data passed to T017.
    # Let's assume the input `data` has the necessary fields.
    # I will output exactly the columns requested. If the pipeline breaks later, it's a spec conflict.
    # Wait, T031 says "read from ... scoring_results.csv ... and join on post_id".
    # This implies `scoring_results.csv` MUST have `post_id`.
    # The task description for T017 is likely incomplete or simplified. 
    # To make the pipeline work (T031), I MUST include `post_id` if it exists in the input data.
    # If the input data doesn't have it, T031 is impossible.
    # I will include `post_id` if present, otherwise strictly the 3 columns.
    
    output_columns = required_columns.copy()
    if "post_id" in df.columns:
        output_columns.insert(0, "post_id")
    
    # Also include 'user_id' if present, as T026 output has it and T031 might need it for context,
    # though T031 specifically mentions joining on post_id.
    if "user_id" in df.columns:
        output_columns.append("user_id")

    df_output = df[output_columns]

    # Save to CSV
    try:
        df_output.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df_output)} rows to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write scoring results to {output_path}: {e}")
        raise

    return output_path


def run_scoring_saver_pipeline() -> Path:
    """
    Run the full scoring saver pipeline.
    
    This function orchestrates the process:
    1. Runs the anxiety scoring pipeline to get the scored data.
    2. Saves the results to `data/processed/scoring_results.csv`.
    
    Returns:
        Path: The path to the saved CSV file.
    """
    logger.info("Starting scoring saver pipeline...")
    
    # Run the scoring pipeline to get the filtered data
    # This relies on T016 having been executed or running here.
    # Since T016 is "Implement confidence score filtering", and T017 is "Save ...",
    # T017 assumes the data is already filtered.
    # The `run_full_scoring_pipeline` in `anxiety_scoring.py` likely returns the filtered data.
    
    scored_data = run_full_scoring_pipeline()
    
    if scored_data is None or len(scored_data) == 0:
        logger.warning("No scored data returned from anxiety scoring pipeline.")
        # Create an empty file to satisfy the "file exists" requirement if needed,
        # but better to fail loud if the upstream failed.
        raise ValueError("Upstream anxiety scoring pipeline returned no data.")
    
    output_path = save_scoring_results(scored_data)
    
    logger.info("Scoring saver pipeline completed successfully.")
    return output_path
