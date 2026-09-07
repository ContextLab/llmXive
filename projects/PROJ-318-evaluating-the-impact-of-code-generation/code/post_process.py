"""
Post-processing script for User Story 2.
Handles empty/whitespace generated docstrings by flagging them for review.
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
    Check if the docstring is None, empty, or contains only whitespace.
    
    Args:
        docstring: The generated docstring text or None.
        
    Returns:
        True if the docstring is empty/whitespace, False otherwise.
    """
    if docstring is None:
        return True
    if not isinstance(docstring, str):
        logger.warning(f"Non-string docstring encountered: {type(docstring)}")
        return True
    return not docstring.strip()

def find_batch_files(input_dir: Path) -> List[Path]:
    """
    Find all generation batch files in the input directory.
    
    Args:
        input_dir: Path to the directory containing batch files.
        
    Returns:
        List of batch file paths, sorted by filename.
    """
    pattern = "generation_batch_*.json"
    files = list(input_dir.glob(pattern))
    
    # Filter out cleaned files to avoid processing them again
    files = [f for f in files if not f.name.endswith('_cleaned.json')]
    
    if not files:
        logger.warning(f"No batch files found matching pattern '{pattern}' in {input_dir}")
        return []
    
    # Sort by filename for deterministic processing
    files.sort(key=lambda x: x.name)
    return files

def process_batch_file(input_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Process a single batch file, flagging records with empty/whitespace docstrings.
    
    Args:
        input_path: Path to the input batch file.
        output_path: Path to the output cleaned batch file.
        
    Returns:
        Dictionary with processing statistics.
    """
    logger.info(f"Processing batch file: {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            records = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {input_path}: {e}")
        raise
    
    if not isinstance(records, list):
        raise ValueError(f"Expected a list of records in {input_path}, got {type(records)}")
    
    processed_count = 0
    flagged_count = 0
    total_count = len(records)
    
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            logger.warning(f"Record {i} in {input_path} is not a dict, skipping")
            continue
        
        # Check for generated docstring field
        generated_docstring = record.get('generated_docstring')
        
        # Flag if empty or whitespace
        if is_empty_or_whitespace(generated_docstring):
            record['needs_review'] = True
            flagged_count += 1
            logger.debug(f"Flagged record {i} for review (empty/whitespace docstring)")
        else:
            # Ensure needs_review is explicitly False if not flagged
            record['needs_review'] = False
        
        processed_count += 1
    
    # Write output file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote {len(records)} records to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write output file {output_path}: {e}")
        raise
    
    return {
        'input_file': str(input_path),
        'output_file': str(output_path),
        'total_records': total_count,
        'processed_records': processed_count,
        'flagged_records': flagged_count,
        'flagged_percentage': (flagged_count / total_count * 100) if total_count > 0 else 0.0
    }

def save_processed_batch(output_path: Path, stats: Dict[str, Any]) -> None:
    """
    Save processing statistics to a log file.
    
    Args:
        output_path: Path to the output file (for context).
        stats: Processing statistics dictionary.
    """
    stats_file = output_path.parent / f"{output_path.stem}_stats.json"
    try:
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Saved processing stats to {stats_file}")
    except IOError as e:
        logger.error(f"Failed to save stats file {stats_file}: {e}")
        # Non-fatal, continue

def main() -> int:
    """
    Main entry point for the post-processing script.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    logger.info("Starting post-processing for empty/whitespace docstrings")
    
    # Define input and output directories
    input_dir = Path("data/processed")
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return 1
    
    # Find all batch files
    batch_files = find_batch_files(input_dir)
    
    if not batch_files:
        logger.warning("No batch files found to process. Exiting.")
        return 0
    
    logger.info(f"Found {len(batch_files)} batch files to process")
    
    total_flagged = 0
    total_records = 0
    
    for batch_file in batch_files:
        # Determine output filename
        output_filename = batch_file.stem + "_cleaned.json"
        output_path = input_dir / output_filename
        
        try:
            stats = process_batch_file(batch_file, output_path)
            save_processed_batch(output_path, stats)
            
            total_flagged += stats['flagged_records']
            total_records += stats['total_records']
            
            logger.info(
                f"Completed {batch_file.name}: "
                f"{stats['flagged_records']}/{stats['total_records']} flagged for review "
                f"({stats['flagged_percentage']:.2f}%)"
            )
            
        except Exception as e:
            logger.error(f"Failed to process {batch_file}: {e}", exc_info=True)
            return 1
    
    logger.info(
        f"Post-processing complete. "
        f"Total records: {total_records}, "
        f"Total flagged: {total_flagged}, "
        f"Overall rate: {(total_flagged/total_records*100) if total_records > 0 else 0:.2f}%"
    )
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
