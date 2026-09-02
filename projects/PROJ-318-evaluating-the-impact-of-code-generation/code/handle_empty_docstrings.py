"""
Post-processing module for User Story 2: Handle empty/whitespace generated docstrings.

This module reads intermediate generation batch files, identifies records with
empty or whitespace-only generated docstrings, calculates a coverage_score of 0.0
for them, sets the needs_review flag to True, and writes the updated records
back to the same batch files.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/handle_empty_docstrings.log')
    ]
)
logger = logging.getLogger(__name__)


def is_empty_or_whitespace(docstring: Optional[str]) -> bool:
    """
    Check if a docstring is None, empty, or contains only whitespace.
    
    Args:
        docstring: The generated docstring to check.
        
    Returns:
        True if the docstring is empty/whitespace, False otherwise.
    """
    if docstring is None:
        return True
    return docstring.strip() == ""


def calculate_coverage_score_for_empty(ast_params: List[str]) -> float:
    """
    Calculate coverage score for an empty docstring.
    
    According to the task specification, for empty/whitespace docstrings,
    the coverage_score is explicitly calculated as:
    (0 matched params / total AST params) = 0.0
    
    Args:
        ast_params: List of parameters extracted from the AST.
        
    Returns:
        0.0 as the coverage score.
    """
    total_params = len(ast_params)
    matched_params = 0
    
    # Explicitly verify the formula as per task requirement
    if total_params > 0:
        score = matched_params / total_params
    else:
        # If no AST params, score is 0.0 by definition for empty docstring
        score = 0.0
        
    logger.debug(f"Coverage score calculation: {matched_params} matched / {total_params} total = {score}")
    return 0.0  # Explicitly return 0.0 as required


def process_batch_file(batch_file_path: Path) -> List[Dict[str, Any]]:
    """
    Process a single batch file to handle empty/whitespace docstrings.
    
    Args:
        batch_file_path: Path to the batch JSON file.
        
    Returns:
        List of updated records.
        
    Raises:
        FileNotFoundError: If the batch file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not batch_file_path.exists():
        raise FileNotFoundError(f"Batch file not found: {batch_file_path}")
    
    logger.info(f"Processing batch file: {batch_file_path}")
    
    with open(batch_file_path, 'r', encoding='utf-8') as f:
        records = json.load(f)
    
    updated_count = 0
    total_count = len(records)
    
    logger.info(f"Loaded {total_count} records from {batch_file_path}")
    
    for i, record in enumerate(records):
        generated_docstring = record.get('generated_docstring')
        ast_params = record.get('ast_params', [])
        
        if is_empty_or_whitespace(generated_docstring):
            # Calculate coverage score as 0.0 explicitly
            coverage_score = calculate_coverage_score_for_empty(ast_params)
            
            # Update the record
            record['coverage_score'] = coverage_score
            record['needs_review'] = True
            record['empty_docstring_reason'] = 'empty_or_whitespace'
            
            updated_count += 1
            
            if updated_count <= 5:  # Log first few updates for visibility
                logger.debug(f"Updated record {i}: function={record.get('function_name', 'unknown')}, "
                           f"coverage_score={coverage_score}, needs_review=True")
    
    logger.info(f"Processed {total_count} records, updated {updated_count} with empty/whitespace docstrings")
    return records


def save_processed_batch(records: List[Dict[str, Any]], batch_file_path: Path) -> None:
    """
    Save the processed records back to the same batch file.
    
    Args:
        records: List of processed records.
        batch_file_path: Path to the batch JSON file to write.
    """
    logger.info(f"Saving {len(records)} records back to {batch_file_path}")
    
    with open(batch_file_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Successfully saved updated batch file: {batch_file_path}")


def main() -> int:
    """
    Main entry point for the post-processing script.
    
    Reads all generation batch files from data/processed/, processes them
    to handle empty/whitespace docstrings, and saves the updated records
    back to the same files.
    
    Returns:
        0 on success, non-zero on failure.
    """
    logger.info("Starting empty docstring post-processing")
    
    # Define the directory containing batch files
    processed_dir = Path("data/processed")
    
    if not processed_dir.exists():
        logger.error(f"Processed directory not found: {processed_dir}")
        return 1
    
    # Find all batch files
    batch_files = list(processed_dir.glob("generation_batch_*.json"))
    
    if not batch_files:
        logger.warning(f"No batch files found in {processed_dir}")
        return 0
    
    logger.info(f"Found {len(batch_files)} batch files to process")
    
    success_count = 0
    failure_count = 0
    
    for batch_file in sorted(batch_files):
        try:
            # Process the batch file
            updated_records = process_batch_file(batch_file)
            
            # Save back to the same file
            save_processed_batch(updated_records, batch_file)
            
            success_count += 1
            logger.info(f"Successfully processed: {batch_file.name}")
            
        except FileNotFoundError as e:
            logger.error(f"File not found error for {batch_file}: {e}")
            failure_count += 1
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {batch_file}: {e}")
            failure_count += 1
        except Exception as e:
            logger.error(f"Unexpected error processing {batch_file}: {e}")
            failure_count += 1
    
    logger.info(f"Post-processing complete: {success_count} succeeded, {failure_count} failed")
    
    if failure_count > 0:
        logger.error(f"Failed to process {failure_count} batch files")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())