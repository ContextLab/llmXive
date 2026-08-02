import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_prompt_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load the prompt manifest JSON file.
    
    Args:
        manifest_path: Path to the prompt manifest JSON file
        
    Returns:
        Dictionary containing the manifest data
        
    Raises:
        FileNotFoundError: If the manifest file does not exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    logger.info(f"Loading prompt manifest from {manifest_path}")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
        
    logger.info(f"Loaded manifest with {len(manifest.get('entries', []))} entries")
    return manifest

def extract_ordering_key(entry: Dict[str, Any]) -> str:
    """
    Extract a unique ordering key from a manifest entry.
    
    The ordering key is constructed from the seed, strategy, and the sequence
    of example IDs in that prompt configuration. This allows us to detect
    if two different seeds produced the exact same ordering of examples.
    
    Args:
        entry: A single entry from the prompt manifest
        
    Returns:
        A string key representing the ordering of examples
    """
    seed = entry.get('seed')
    strategy = entry.get('strategy')
    
    # The examples list contains the sequence of example IDs
    examples = entry.get('examples', [])
    example_ids = [ex.get('id') for ex in examples]
    
    # Create a key that represents the ordering: seed is excluded to check
    # if different seeds produced the same ordering
    ordering_tuple = tuple(example_ids)
    
    return f"{strategy}:{ordering_tuple}"

def validate_no_duplicates(manifest: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, List[str]]]:
    """
    Validate that there are no duplicate orderings within a strategy group across seeds.
    
    This function checks if the same sequence of examples appears in multiple
    entries with the same strategy but different seeds. If duplicates are found,
    it returns False and a list of duplicate entries.
    
    Args:
        manifest: The loaded prompt manifest dictionary
        
    Returns:
        Tuple of:
            - is_valid: True if no duplicates found, False otherwise
            - duplicates: List of formatted duplicate entries
            - strategy_groups: Dictionary mapping strategy to list of ordering keys
    """
    entries = manifest.get('entries', [])
    logger.info(f"Validating {len(entries)} entries for duplicate orderings")
    
    # Group entries by strategy
    strategy_groups: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}
    
    for entry in entries:
        strategy = entry.get('strategy')
        if strategy not in strategy_groups:
            strategy_groups[strategy] = []
        
        ordering_key = extract_ordering_key(entry)
        strategy_groups[strategy].append((ordering_key, entry))
    
    # Check for duplicates within each strategy group
    duplicates: List[str] = []
    duplicate_details: Dict[str, List[str]] = {}
    is_valid = True
    
    for strategy, group in strategy_groups.items():
        seen_keys: Dict[str, List[Dict[str, Any]]] = {}
        
        for ordering_key, entry in group:
            if ordering_key not in seen_keys:
                seen_keys[ordering_key] = []
            seen_keys[ordering_key].append(entry)
        
        # Find duplicates
        for ordering_key, entries_with_key in seen_keys.items():
            if len(entries_with_key) > 1:
                is_valid = False
                seed_list = [e.get('seed') for e in entries_with_key]
                msg = f"Strategy '{strategy}': Duplicate ordering found across seeds {seed_list}"
                duplicates.append(msg)
                
                if strategy not in duplicate_details:
                    duplicate_details[strategy] = []
                duplicate_details[strategy].append(msg)
                
                logger.warning(msg)
    
    if is_valid:
        logger.info("Validation passed: No duplicate orderings found within strategy groups")
    else:
        logger.error(f"Validation failed: Found {len(duplicates)} duplicate ordering(s)")
    
    return is_valid, duplicates, duplicate_details

def main():
    """
    Main entry point for the validation script.
    
    Loads the prompt manifest, validates for duplicate orderings,
    and exits with appropriate status code.
    """
    parser = argparse.ArgumentParser(
        description='Validate prompt manifest for duplicate orderings within strategy groups'
    )
    parser.add_argument(
        '--manifest',
        type=str,
        default='data/processed/prompt_manifest.json',
        help='Path to the prompt manifest JSON file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/processed/validation_orderings.json',
        help='Path to save the validation report'
    )
    
    args = parser.parse_args()
    manifest_path = Path(args.manifest)
    output_path = Path(args.output)
    
    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        sys.exit(1)
    
    try:
        manifest = load_prompt_manifest(manifest_path)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest: {e}")
        sys.exit(1)
    
    is_valid, duplicates, duplicate_details = validate_no_duplicates(manifest)
    
    # Create validation report
    report = {
        'is_valid': is_valid,
        'total_entries': len(manifest.get('entries', [])),
        'duplicate_count': len(duplicates),
        'duplicates': duplicates,
        'strategy_groups': duplicate_details,
        'manifest_path': str(manifest_path),
        'validation_timestamp': 'validation_run'  # Placeholder for actual timestamp
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save report
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report saved to {output_path}")
    
    # Exit with appropriate code
    if is_valid:
        logger.info("Validation PASSED")
        sys.exit(0)
    else:
        logger.error("Validation FAILED")
        sys.exit(1)

if __name__ == '__main__':
    main()
