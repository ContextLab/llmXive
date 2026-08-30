"""
Module to handle empty or whitespace-only generated docstrings.

Reads generation batch files, identifies records with empty/whitespace docstrings,
sets coverage_score to 0.0 and needs_review to true, and saves the processed file.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from utils.exceptions import GenerationException

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


def is_empty_or_whitespace(docstring: str) -> bool:
    """
    Check if a docstring is empty or contains only whitespace.
    
    Args:
        docstring: The docstring content to check.
        
    Returns:
        True if the docstring is None, empty string, or only whitespace.
    """
    if docstring is None:
        return True
    if not isinstance(docstring, str):
        # Non-string values (e.g., lists, dicts) are considered invalid/empty
        return True
    return docstring.strip() == ""


def process_batch_file(batch_file_path: Path) -> List[Dict[str, Any]]:
    """
    Process a single generation batch file to handle empty docstrings.
    
    Iterates over records in the batch file. If a record's 'generated_docstring'
    is empty or whitespace, sets 'coverage_score' to 0.0 and 'needs_review' to True.
    
    Args:
        batch_file_path: Path to the generation batch JSON file.
        
    Returns:
        List of processed records with updated coverage scores and flags.
        
    Raises:
        GenerationException: If the file cannot be read or parsed.
    """
    if not batch_file_path.exists():
        raise GenerationException(f"Batch file not found: {batch_file_path}")
    
    try:
        with open(batch_file_path, 'r', encoding='utf-8') as f:
            records = json.load(f)
    except json.JSONDecodeError as e:
        raise GenerationException(f"Failed to parse JSON in {batch_file_path}: {e}")
    except Exception as e:
        raise GenerationException(f"Error reading {batch_file_path}: {e}")
    
    if not isinstance(records, list):
        raise GenerationException(f"Expected a list of records in {batch_file_path}, got {type(records)}")
    
    processed_count = 0
    updated_count = 0
    
    for record in records:
        processed_count += 1
        
        generated_docstring = record.get('generated_docstring')
        
        if is_empty_or_whitespace(generated_docstring):
            # Set coverage_score to 0.0
            record['coverage_score'] = 0.0
            # Set needs_review to True
            record['needs_review'] = True
            updated_count += 1
            logger.debug(f"Updated record for method '{record.get('method_name', 'unknown')}': "
                         f"empty docstring detected. Set coverage_score=0.0, needs_review=True")
        else:
            # Ensure needs_review is False if not already set and docstring is valid
            if 'needs_review' not in record:
                record['needs_review'] = False
            
            # Ensure coverage_score is set (even if not 0.0) if not present
            # Note: Actual coverage calculation might happen later in T033, 
            # but we ensure the field exists.
            if 'coverage_score' not in record:
                # Placeholder: We don't calculate real coverage here, just mark as non-empty.
                # The actual coverage calculation is done in T033 (analyze.py).
                # For now, we leave it unset or set to a placeholder if the pipeline expects it.
                # However, T027 specifically says "set coverage_score to 0.0" for empty ones.
                # For non-empty ones, we don't touch it unless it's missing and we need a default.
                # Let's leave it missing if it was missing, or keep existing value.
                pass
    
    logger.info(f"Processed {processed_count} records in {batch_file_path.name}. "
                f"Updated {updated_count} records with empty/whitespace docstrings.")
    
    return records


def save_processed_batch(processed_records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the processed records to a new JSON file.
    
    Args:
        processed_records: List of processed records.
        output_path: Path where the processed file should be saved.
        
    Raises:
        GenerationException: If the file cannot be written.
    """
    try:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_records, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully saved processed batch to {output_path}")
    except Exception as e:
        raise GenerationException(f"Failed to write processed batch to {output_path}: {e}")


def main() -> None:
    """
    Main entry point to process all generation batch files.
    
    Reads all files matching 'data/processed/generation_batch_*.json',
    processes them to handle empty docstrings, and saves the results
    to 'data/processed/generation_batch_{repo_id}_processed.json'.
    """
    input_dir = Path("data/processed")
    
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        sys.exit(1)
    
    batch_files = list(input_dir.glob("generation_batch_*.json"))
    
    if not batch_files:
        logger.warning(f"No generation batch files found in {input_dir}")
        sys.exit(0)
    
    logger.info(f"Found {len(batch_files)} generation batch files to process.")
    
    processed_files = []
    
    for batch_file in sorted(batch_files):
        logger.info(f"Processing {batch_file.name}...")
        
        try:
            # Process the batch file
            processed_records = process_batch_file(batch_file)
            
            # Determine output path: add '_processed' before .json extension
            stem = batch_file.stem  # e.g., "generation_batch_repo1"
            output_filename = f"{stem}_processed.json"
            output_path = batch_file.parent / output_filename
            
            # Save the processed records
            save_processed_batch(processed_records, output_path)
            
            processed_files.append(str(output_path))
            
        except GenerationException as e:
            logger.error(f"Error processing {batch_file.name}: {e}")
            # Continue with other files
            continue
        except Exception as e:
            logger.exception(f"Unexpected error processing {batch_file.name}: {e}")
            continue
    
    logger.info(f"Processing complete. Processed {len(processed_files)} files.")
    for pf in processed_files:
        logger.info(f"  - {pf}")


if __name__ == "__main__":
    main()