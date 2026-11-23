"""
Validate dataset uniqueness to ensure no duplicate puzzle instances exist.

This script hashes all puzzle definitions in the raw dataset directory
and ensures uniqueness before proceeding to final distribution reporting.

Constraint: Must fail loudly if duplicates are found (no silent handling).
"""
import json
import hashlib
import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_puzzle_hash(puzzle_data: Dict[str, Any]) -> str:
    """
    Compute a deterministic hash for a puzzle instance.
    
    Args:
        puzzle_data: Dictionary containing puzzle definition.
        
    Returns:
        SHA-256 hex digest of the puzzle content.
    """
    # Sort keys to ensure deterministic hashing
    normalized = json.dumps(puzzle_data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def load_puzzles_from_directory(raw_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all puzzle instances from JSON files in the raw directory.
    
    Args:
        raw_dir: Path to the data/raw directory.
        
    Returns:
        List of puzzle dictionaries.
        
    Raises:
        FileNotFoundError: If the raw directory does not exist.
        ValueError: If a puzzle file is invalid JSON.
    """
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw dataset directory not found: {raw_dir}")
    
    puzzles = []
    json_files = list(raw_dir.glob('*.json'))
    
    if not json_files:
        logger.warning(f"No JSON files found in {raw_dir}")
        return puzzles
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle both single puzzle and list of puzzles
                if isinstance(data, list):
                    puzzles.extend(data)
                elif isinstance(data, dict):
                    puzzles.append(data)
                else:
                    logger.warning(f"Unexpected format in {json_file}: {type(data)}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {json_file}: {e}")
    
    return puzzles

def validate_uniqueness(puzzles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check for duplicate puzzle instances using hashing.
    
    Args:
        puzzles: List of puzzle dictionaries.
        
    Returns:
        Dictionary with validation results:
        - is_unique: bool
        - total_count: int
        - unique_count: int
        - duplicates: list of duplicate hashes and their counts
        - status: 'PASS' or 'FAIL'
    """
    hash_map: Dict[str, List[int]] = {}
    
    for idx, puzzle in enumerate(puzzles):
        puzzle_hash = compute_puzzle_hash(puzzle)
        if puzzle_hash not in hash_map:
            hash_map[puzzle_hash] = []
        hash_map[puzzle_hash].append(idx)
    
    duplicates = []
    for puzzle_hash, indices in hash_map.items():
        if len(indices) > 1:
            duplicates.append({
                'hash': puzzle_hash,
                'count': len(indices),
                'indices': indices
            })
    
    is_unique = len(duplicates) == 0
    status = 'PASS' if is_unique else 'FAIL'
    
    return {
        'is_unique': is_unique,
        'total_count': len(puzzles),
        'unique_count': len(hash_map),
        'duplicates': duplicates,
        'status': status,
        'timestamp': datetime.utcnow().isoformat()
    }

def save_validation_result(result: Dict[str, Any], output_path: Path) -> None:
    """
    Save the validation result to a JSON file.
    
    Args:
        result: Validation result dictionary.
        output_path: Path to save the result.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Validation result saved to {output_path}")

def main() -> int:
    """
    Main entry point for the uniqueness validation script.
    
    Returns:
        0 if validation passes, 1 if duplicates found or error occurs.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    raw_dir = project_root / 'data' / 'raw'
    output_path = project_root / 'data' / 'processed' / 'uniqueness_validation.json'
    
    logger.info(f"Starting uniqueness validation for dataset in {raw_dir}")
    
    try:
        # Load puzzles
        puzzles = load_puzzles_from_directory(raw_dir)
        logger.info(f"Loaded {len(puzzles)} puzzle instances")
        
        if len(puzzles) == 0:
            logger.warning("No puzzles found to validate. Creating empty validation result.")
            result = {
                'is_unique': True,
                'total_count': 0,
                'unique_count': 0,
                'duplicates': [],
                'status': 'PASS',
                'notes': 'No puzzles found in raw directory',
                'timestamp': datetime.utcnow().isoformat()
            }
        else:
            # Validate uniqueness
            result = validate_uniqueness(puzzles)
            
            if not result['is_unique']:
                logger.error(f"DUPLICATES DETECTED: {len(result['duplicates'])} duplicate groups found")
                for dup in result['duplicates']:
                    logger.error(f"  Hash: {dup['hash']}, Count: {dup['count']}, Indices: {dup['indices']}")
        
        # Save result
        save_validation_result(result, output_path)
        
        # Fail loudly if duplicates found
        if result['status'] == 'FAIL':
            logger.error("VALIDATION FAILED: Dataset contains duplicates. Halting pipeline.")
            return 1
        
        logger.info("VALIDATION PASSED: All puzzle instances are unique.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Directory not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())