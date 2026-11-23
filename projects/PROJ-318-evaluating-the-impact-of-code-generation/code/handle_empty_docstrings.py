"""
Post-processing script to handle empty/whitespace generated docstrings.

Reads batch files from data/processed/, identifies empty docstrings,
calculates coverage_score as 0.0 for those records, sets needs_review flag,
and writes cleaned output files.
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
        logging.FileHandler('logs/handle_empty_docstrings.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def is_empty_or_whitespace(docstring: Optional[str]) -> bool:
    """
    Check if a docstring is empty or contains only whitespace.
    
    Args:
        docstring: The docstring to check, or None
        
    Returns:
        True if docstring is None, empty string, or whitespace-only
    """
    if docstring is None:
        return True
    if not isinstance(docstring, str):
        return True
    return len(docstring.strip()) == 0


def calculate_coverage_score_for_empty(ast_params: List[Dict[str, Any]]) -> float:
    """
    Calculate coverage score for an empty docstring.
    
    Per task requirements: coverage_score = (0 matched params / total AST params) = 0.0
    
    Args:
        ast_params: List of AST-defined parameters from the method signature
        
    Returns:
        0.0 (explicitly verifying the formula: 0 / total = 0)
    """
    total_params = len(ast_params)
    matched_params = 0  # Empty docstring matches no parameters
    
    # Explicitly verify the formula as required by task specification
    if total_params > 0:
        coverage = matched_params / total_params
    else:
        # No parameters defined, coverage is technically 0 (or undefined, but we use 0)
        coverage = 0.0
        
    # Verify the formula explicitly
    expected = 0.0
    assert coverage == expected, f"Coverage calculation error: expected {expected}, got {coverage}"
    
    logger.debug(f"Coverage calculation: {matched_params} matched / {total_params} total = {coverage}")
    return coverage


def process_batch_file(input_path: Path) -> List[Dict[str, Any]]:
    """
    Process a single batch file to handle empty docstrings.
    
    Args:
        input_path: Path to the input JSON file
        
    Returns:
        List of processed records with updated fields
    """
    logger.info(f"Processing batch file: {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        records = json.load(f)
    
    logger.info(f"Loaded {len(records)} records from {input_path}")
    
    processed_records = []
    empty_count = 0
    
    for i, record in enumerate(records):
        generated_docstring = record.get('generated_docstring')
        ast_params = record.get('ast_params', [])
        
        # Check if docstring is empty or whitespace
        if is_empty_or_whitespace(generated_docstring):
            empty_count += 1
            
            # Calculate coverage score as 0.0
            coverage_score = calculate_coverage_score_for_empty(ast_params)
            
            # Set needs_review flag
            record['needs_review'] = True
            record['coverage_score'] = coverage_score
            
            logger.debug(f"Record {i}: Empty docstring detected, needs_review=True, coverage={coverage_score}")
        else:
            # Not empty, but still calculate coverage if not already present
            # (for consistency, though task focuses on empty ones)
            if 'coverage_score' not in record:
                # We don't have the parsing logic here, so skip for non-empty
                # The task specifically focuses on empty docstrings
                pass
            record['needs_review'] = record.get('needs_review', False)
        
        processed_records.append(record)
    
    logger.info(f"Processed {len(processed_records)} records, found {empty_count} empty docstrings")
    return processed_records


def save_processed_batch(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save processed records to a new JSON file.
    
    Args:
        records: List of processed records
        output_path: Path to the output JSON file
    """
    logger.info(f"Saving {len(records)} records to {output_path}")
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Successfully saved cleaned batch to {output_path}")


def find_batch_files(data_dir: Path) -> List[Path]:
    """
    Find all generation batch files in the data directory.
    
    Args:
        data_dir: Path to the data/processed directory
        
    Returns:
        List of batch file paths matching the pattern generation_batch_*.json
    """
    pattern = "generation_batch_*.json"
    batch_files = list(data_dir.glob(pattern))
    
    # Filter out already cleaned files
    batch_files = [f for f in batch_files if not f.name.endswith('_cleaned.json')]
    
    logger.info(f"Found {len(batch_files)} batch files: {[f.name for f in batch_files]}")
    return batch_files


def main() -> int:
    """
    Main entry point for post-processing empty docstrings.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    logger.info("Starting empty docstring post-processing")
    
    try:
        # Define paths
        data_dir = Path("data/processed")
        
        if not data_dir.exists():
            logger.error(f"Data directory not found: {data_dir}")
            return 1
        
        # Find all batch files
        batch_files = find_batch_files(data_dir)
        
        if not batch_files:
            logger.warning("No batch files found to process")
            return 0
        
        # Process each batch file
        for input_path in sorted(batch_files):
            try:
                # Process the batch
                processed_records = process_batch_file(input_path)
                
                # Create output path (append _cleaned before .json)
                output_path = input_path.with_name(input_path.stem + "_cleaned.json")
                
                # Save processed records
                save_processed_batch(processed_records, output_path)
                
            except Exception as e:
                logger.error(f"Error processing {input_path}: {str(e)}")
                raise
        
        logger.info("Empty docstring post-processing completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Post-processing failed: {str(e)}")
        logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
