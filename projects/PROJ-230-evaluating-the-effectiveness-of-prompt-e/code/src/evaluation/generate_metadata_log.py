"""
Generate a version-controlled metadata log for reproducibility.

This script scans the translation output directories created by run_inference.py,
extracts deterministic metadata (prompt_condition, seed, timestamp, input_id),
and aggregates them into a single CSV file at data/evaluation/metadata_log.csv.

CRITICAL: This file contains NO raw LLM outputs, only metadata required for
reproducibility tracking. It is intended to be committed to git.

Dependencies:
- T021 (run_inference.py): Creates the directory structure and JSON files
- T022 (determinism_utils): Ensures seeds and timestamps are logged in JSON
"""
import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TRANSLATIONS_BASE_DIR = PROJECT_ROOT / "data" / "evaluation" / "raw_translations"
OUTPUT_CSV_PATH = PROJECT_ROOT / "data" / "evaluation" / "metadata_log.csv"

def scan_translation_dirs(base_dir: Path) -> List[Path]:
    """
    Recursively scan the base directory for all JSON translation files.
    
    Args:
        base_dir: Root directory containing condition subdirectories
        
    Returns:
        List of paths to all .json files found
    """
    if not base_dir.exists():
        logger.warning(f"Translations directory does not exist: {base_dir}")
        return []
        
    json_files = []
    for path in base_dir.rglob("*.json"):
        # Skip hidden files or system files
        if path.name.startswith('.'):
            continue
        json_files.append(path)
        
    logger.info(f"Found {len(json_files)} translation files in {base_dir}")
    return json_files

def extract_metadata(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract metadata from a single translation JSON file.
    
    Expected JSON structure (from run_inference.py):
    {
        "input_id": "unique_identifier",
        "prompt_condition": "zero_shot_basic",
        "seed": 42,
        "timestamp": "2023-10-27T10:00:00Z",
        "raw_output": "...",  // EXCLUDED from metadata log
        "python_code": "...",
        "javascript_code": "..."
    }
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dictionary with metadata fields, or None if parsing fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract ONLY the required metadata fields
        # Explicitly exclude 'raw_output' to ensure this file is safe for git
        metadata = {
            'input_id': data.get('input_id', ''),
            'prompt_condition': data.get('prompt_condition', ''),
            'seed': data.get('seed', ''),
            'timestamp': data.get('timestamp', ''),
            'file_path': str(file_path.relative_to(PROJECT_ROOT))
        }
        
        # Validate required fields
        if not metadata['input_id']:
            logger.warning(f"Missing input_id in {file_path}")
            return None
            
        return metadata
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

def aggregate_metadata(file_paths: List[Path]) -> List[Dict[str, Any]]:
    """
    Aggregate metadata from multiple JSON files.
    
    Args:
        file_paths: List of paths to JSON files
        
    Returns:
        List of metadata dictionaries, sorted by timestamp
    """
    metadata_list = []
    success_count = 0
    failure_count = 0
    
    for path in file_paths:
        metadata = extract_metadata(path)
        if metadata:
            metadata_list.append(metadata)
            success_count += 1
        else:
            failure_count += 1
            
    logger.info(f"Aggregated {success_count} valid entries, {failure_count} failed")
    
    # Sort by timestamp for reproducibility
    metadata_list.sort(key=lambda x: (x.get('timestamp', ''), x.get('input_id', '')))
    
    return metadata_list

def save_metadata_log(metadata_list: List[Dict[str, Any]], output_path: Path) -> bool:
    """
    Save aggregated metadata to a CSV file.
    
    Args:
        metadata_list: List of metadata dictionaries
        output_path: Path to the output CSV file
        
    Returns:
        True if successful, False otherwise
    """
    if not metadata_list:
        logger.warning("No metadata to save")
        # Still create an empty file with headers
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['input_id', 'prompt_condition', 'seed', 'timestamp', 'file_path'])
            writer.writeheader()
        return True
        
    fieldnames = ['input_id', 'prompt_condition', 'seed', 'timestamp', 'file_path']
    
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(metadata_list)
            
        logger.info(f"Saved metadata log with {len(metadata_list)} entries to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save metadata log: {e}")
        return False

def main():
    """Main entry point for generating the metadata log."""
    logger.info("Starting metadata log generation...")
    
    # Scan for translation files
    json_files = scan_translation_dirs(TRANSLATIONS_BASE_DIR)
    
    if not json_files:
        logger.warning("No translation files found. Creating empty metadata log.")
        save_metadata_log([], OUTPUT_CSV_PATH)
        return
    
    # Aggregate metadata
    metadata_list = aggregate_metadata(json_files)
    
    # Save to CSV
    success = save_metadata_log(metadata_list, OUTPUT_CSV_PATH)
    
    if success:
        logger.info("Metadata log generation completed successfully.")
        print(f"Output written to: {OUTPUT_CSV_PATH}")
    else:
        logger.error("Metadata log generation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()