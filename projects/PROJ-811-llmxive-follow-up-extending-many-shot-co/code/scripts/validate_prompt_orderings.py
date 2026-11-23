"""
Script to validate prompt orderings for duplicate orderings within a strategy group across seeds.

This implements T027: Add validation to ensure no duplicate orderings within a strategy group across seeds.

The validation logic checks that for each strategy (e.g., "Logical Ascending", "Logical Random", "Original CDS"),
the ordering of examples (defined by the sequence of example IDs or hashes) is unique across all seeds.
This prevents accidental duplication of the same prompt configuration under different seeds.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set

# Import from existing API surface
from code.src.parser_utils import load_json_file, save_json_file
from code.src.config import PROJECT_ROOT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_prompt_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load the prompt manifest file.
    
    Args:
        manifest_path: Path to the prompt manifest JSON file
        
    Returns:
        Dictionary containing the prompt manifest data
        
    Raises:
        FileNotFoundError: If the manifest file does not exist
        json.JSONDecodeError: If the manifest file contains invalid JSON
    """
    logger.info(f"Loading prompt manifest from {manifest_path}")
    return load_json_file(manifest_path)


def extract_ordering_key(entry: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Extract a unique ordering key from a prompt manifest entry.
    
    The ordering key is composed of:
    - Strategy name
    - Sequence of example IDs (or hashes) in the prompt
    - This creates a canonical representation of the ordering
    
    Args:
        entry: A single entry from the prompt manifest
        
    Returns:
        Tuple of (strategy, ordering_signature, seed)
    """
    strategy = entry.get('strategy', 'unknown')
    seed = entry.get('seed', 'unknown')
    
    # Extract the sequence of example IDs or hashes that define the ordering
    # This assumes the manifest contains a 'examples' or 'ordering' field
    examples = entry.get('examples', [])
    if not examples:
        # Fallback: try to get ordering from a dedicated field
        examples = entry.get('ordering', [])
    
    # Create a signature from the sequence of example identifiers
    # Using IDs or hashes to represent the ordering
    ordering_signature = tuple(
        ex.get('id', ex.get('hash', str(ex))) for ex in examples
    )
    
    return (strategy, ordering_signature, seed)


def validate_no_duplicates(manifest: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate that there are no duplicate orderings within a strategy group across seeds.
    
    This function checks that for each strategy, the ordering of examples is unique
    across all seeds. If two different seeds produce the exact same ordering for the
    same strategy, this indicates a potential issue (e.g., deterministic shuffling
    with the same seed, or a bug in the ordering logic).
    
    Args:
        manifest: The prompt manifest dictionary
        
    Returns:
        Tuple of (is_valid, list_of_duplicates)
        - is_valid: True if no duplicates found, False otherwise
        - list_of_duplicates: List of duplicate entries found
    """
    logger.info("Validating prompt orderings for duplicates...")
    
    # Group entries by strategy
    strategy_orderings: Dict[str, Dict[Tuple, List[Dict[str, Any]]]] = {}
    
    entries = manifest.get('entries', [])
    if not entries:
        logger.warning("No entries found in manifest")
        return True, []
    
    for entry in entries:
        strategy, ordering_sig, seed = extract_ordering_key(entry)
        
        if strategy not in strategy_orderings:
            strategy_orderings[strategy] = {}
        
        if ordering_sig not in strategy_orderings[strategy]:
            strategy_orderings[strategy][ordering_sig] = []
        
        strategy_orderings[strategy][ordering_sig].append({
            'seed': seed,
            'strategy': strategy,
            'ordering_signature': str(ordering_sig)[:50] + '...'  # Truncate for logging
        })
    
    # Find duplicates (orderings that appear more than once within a strategy)
    duplicates = []
    for strategy, orderings in strategy_orderings.items():
        for ordering_sig, occurrences in orderings.items():
            if len(occurrences) > 1:
                # Found a duplicate ordering within this strategy
                duplicates.append({
                    'strategy': strategy,
                    'ordering_signature': str(ordering_sig),
                    'occurrences': occurrences,
                    'count': len(occurrences)
                })
                logger.warning(
                    f"Duplicate ordering found in strategy '{strategy}': "
                    f"appears {len(occurrences)} times across seeds: "
                    f"{[occ['seed'] for occ in occurrences]}"
                )
    
    is_valid = len(duplicates) == 0
    
    if is_valid:
        logger.info("Validation passed: No duplicate orderings found within strategy groups.")
    else:
        logger.error(
            f"Validation failed: Found {len(duplicates)} duplicate ordering(s) "
            f"within strategy groups."
        )
    
    return is_valid, duplicates


def main():
    """
    Main entry point for the validation script.
    
    Usage:
        python -m code.scripts.validate_prompt_orderings [--manifest PATH] [--output PATH]
    
    Options:
        --manifest: Path to the prompt manifest file (default: data/processed/prompt_manifest.json)
        --output: Path to save the validation report (default: data/processed/validation_ordering_report.json)
        --fail-on-duplicate: Exit with code 1 if duplicates are found
    """
    parser = argparse.ArgumentParser(
        description="Validate prompt orderings for duplicate orderings within strategy groups."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=PROJECT_ROOT / "data" / "processed" / "prompt_manifest.json",
        help="Path to the prompt manifest file"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "processed" / "validation_ordering_report.json",
        help="Path to save the validation report"
    )
    parser.add_argument(
        "--fail-on-duplicate",
        action="store_true",
        help="Exit with code 1 if duplicates are found"
    )
    
    args = parser.parse_args()
    
    # Load manifest
    try:
        manifest = load_prompt_manifest(args.manifest)
    except FileNotFoundError:
        logger.error(f"Manifest file not found: {args.manifest}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest file: {e}")
        sys.exit(1)
    
    # Validate
    is_valid, duplicates = validate_no_duplicates(manifest)
    
    # Generate report
    report = {
        "validation_status": "passed" if is_valid else "failed",
        "manifest_path": str(args.manifest),
        "total_entries": len(manifest.get('entries', [])),
        "duplicate_count": len(duplicates),
        "duplicates": duplicates,
        "strategies_checked": list(set(
            extract_ordering_key(entry)[0] for entry in manifest.get('entries', [])
        )),
        "timestamp": str(Path(args.output).parent.parent.name)  # Placeholder for actual timestamp
    }
    
    # Save report
    args.output.parent.mkdir(parents=True, exist_ok=True)
    save_json_file(args.output, report)
    logger.info(f"Validation report saved to {args.output}")
    
    # Exit code
    if args.fail_on_duplicate and not is_valid:
        logger.error("Exiting with failure code due to duplicate orderings.")
        sys.exit(1)
    elif not is_valid:
        logger.warning("Validation failed, but continuing (no --fail-on-duplicate flag).")
        sys.exit(0)
    else:
        logger.info("Validation successful.")
        sys.exit(0)


if __name__ == "__main__":
    main()
