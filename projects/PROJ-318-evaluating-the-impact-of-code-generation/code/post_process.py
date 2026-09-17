"""
Post-processing script for User Story 2.

Handles empty/whitespace generated docstrings by flagging them for review
and calculating a Parameter Coverage Score of 0.0 for these records.

Reads from data/processed/generation_batch_{repo_slug}.json
Writes to data/processed/generation_batch_{repo_slug}_cleaned.json
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
        logging.FileHandler('logs/post_process.log')
    ]
)
logger = logging.getLogger(__name__)

def is_empty_or_whitespace(docstring: Optional[str]) -> bool:
    """
    Check if a docstring is None, empty, or contains only whitespace.
    
    Args:
        docstring: The docstring text to check.
        
    Returns:
        True if the docstring is empty/whitespace, False otherwise.
    """
    if docstring is None:
        return True
    if not isinstance(docstring, str):
        logger.warning(f"Non-string docstring type detected: {type(docstring)}")
        return True
    return not docstring.strip()

def find_batch_files(input_dir: str) -> List[Path]:
    """
    Find all generation batch files in the input directory.
    
    Args:
        input_dir: Path to the directory containing batch files.
        
    Returns:
        List of Path objects for found batch files, sorted by filename.
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    
    batch_files = list(input_path.glob("generation_batch_*.json"))
    if not batch_files:
        logger.warning(f"No batch files found in {input_dir}")
        return []
    
    # Sort by filename to ensure deterministic processing order
    return sorted(batch_files, key=lambda p: p.name)

def process_batch_file(batch_file: Path) -> List[Dict[str, Any]]:
    """
    Process a single batch file, flagging empty docstrings and calculating coverage.
    
    For each record:
    - If docstring is empty/whitespace: set needs_review=True, coverage_score=0.0
    - Otherwise: set needs_review=False, coverage_score=0.0 (placeholder for future calculation)
    
    Args:
        batch_file: Path to the input batch JSON file.
        
    Returns:
        List of processed records with added fields.
    """
    logger.info(f"Processing batch file: {batch_file.name}")
    
    try:
        with open(batch_file, 'r', encoding='utf-8') as f:
            records = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {batch_file.name}: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to read {batch_file.name}: {e}")
        raise
    
    processed_records = []
    empty_count = 0
    
    for i, record in enumerate(records):
        # Extract the generated docstring
        # The field name might vary, but based on context it's likely 'generated_docstring' or 'docstring'
        docstring = record.get('generated_docstring') or record.get('docstring')
        
        needs_review = is_empty_or_whitespace(docstring)
        
        # Calculate Parameter Coverage Score
        # For empty docstrings, score is 0.0
        # For non-empty, we could calculate it, but the task specifically says:
        # "calculate Parameter Coverage Score as 0.0 for these records" (the empty ones)
        # We'll set non-empty to 0.0 as a placeholder since the actual calculation
        # happens in T033 (analyze.py --step=coverage)
        coverage_score = 0.0
        
        processed_record = record.copy()
        processed_record['needs_review'] = needs_review
        processed_record['coverage_score'] = coverage_score
        
        processed_records.append(processed_record)
        
        if needs_review:
            empty_count += 1
    
    logger.info(f"Processed {len(records)} records from {batch_file.name}")
    logger.info(f"Found {empty_count} records with empty/whitespace docstrings (needs_review=True)")
    
    return processed_records

def save_processed_batch(records: List[Dict[str, Any]], output_file: Path) -> None:
    """
    Save processed records to a new JSON file.
    
    Args:
        records: List of processed records.
        output_file: Path to the output file.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(records)} records to {output_file.name}")
    except Exception as e:
        logger.error(f"Failed to write {output_file.name}: {e}")
        raise

def main():
    """
    Main entry point for the post-processing script.
    
    Processes all generation batch files in data/processed/,
    flags empty docstrings, and writes cleaned files.
    """
    input_dir = "data/processed"
    
    logger.info(f"Starting post-processing for files in {input_dir}")
    
    batch_files = find_batch_files(input_dir)
    
    if not batch_files:
        logger.warning("No batch files found to process. Exiting.")
        return
    
    logger.info(f"Found {len(batch_files)} batch files to process")
    
    for batch_file in batch_files:
        try:
            # Determine output filename
            stem = batch_file.stem  # e.g., 'generation_batch_requests'
            output_filename = f"{stem}_cleaned.json"
            output_file = batch_file.parent / output_filename
            
            # Process the batch
            processed_records = process_batch_file(batch_file)
            
            # Save the processed batch
            save_processed_batch(processed_records, output_file)
            
            logger.info(f"Successfully processed {batch_file.name} -> {output_file.name}")
            
        except Exception as e:
            logger.error(f"Failed to process {batch_file.name}: {e}")
            raise
    
    logger.info("Post-processing completed successfully")

if __name__ == "__main__":
    main()