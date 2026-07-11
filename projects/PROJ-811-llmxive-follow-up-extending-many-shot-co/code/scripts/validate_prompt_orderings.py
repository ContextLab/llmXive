"""
Script to validate that no duplicate orderings exist within a strategy group across seeds.

This script scans the generated prompt manifest or prompt files to ensure that
the sequence of example IDs for a given strategy is unique across all seeds.
Duplicate orderings would indicate a failure in the randomization logic or
an error in the sorting logic.

Output: Writes a validation report to data/processed/validation_orderings.json
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set

from code.src.parser_utils import load_json_file, save_json_file
from code.src.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_prompt_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the prompt manifest JSON file."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Prompt manifest not found at {manifest_path}")
    return load_json_file(manifest_path)

def extract_ordering_key(entry: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Extract the strategy name and the ordered list of example IDs from a manifest entry.
    
    Returns:
        Tuple of (strategy_name, list_of_example_ids)
    """
    strategy = entry.get('strategy', 'unknown')
    # The ordering is typically stored as a list of example IDs in the 'examples' or 'order' field
    # We need to check the structure of the manifest. 
    # Based on typical manifest structures from T028:
    # entry might look like: {"seed": 123, "strategy": "ascending", "examples": [id1, id2, ...], "file": "..."}
    examples = entry.get('examples', entry.get('order', []))
    return strategy, examples

def validate_no_duplicates(manifest: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that no duplicate orderings exist within a strategy group across seeds.
    
    Args:
        manifest: The loaded prompt manifest dictionary.
        
    Returns:
        Tuple of (is_valid, report_dict)
    """
    entries = manifest.get('prompts', [])
    if not entries:
        logger.warning("No prompt entries found in manifest.")
        return True, {"valid": True, "message": "No entries to validate."}

    # Group orderings by strategy
    strategy_orderings: Dict[str, Dict[str, List[str]]] = {}
    
    for entry in entries:
        strategy, ordering = extract_ordering_key(entry)
        
        if strategy not in strategy_orderings:
            strategy_orderings[strategy] = {}
        
        # Convert ordering list to tuple for hashing/comparison
        ordering_tuple = tuple(ordering)
        seed_id = entry.get('seed', 'unknown')
        
        # Check for duplicates within this strategy
        if ordering_tuple in strategy_orderings[strategy]:
            existing_seed = strategy_orderings[strategy][ordering_tuple]
            logger.error(f"Duplicate ordering found in strategy '{strategy}': "
                         f"Seed {seed_id} matches Seed {existing_seed}")
            return False, {
                "valid": False,
                "strategy": strategy,
                "duplicate_seeds": [existing_seed, seed_id],
                "ordering": list(ordering_tuple)
            }
        
        strategy_orderings[strategy][ordering_tuple] = seed_id

    logger.info("Validation passed: No duplicate orderings found within any strategy group.")
    return True, {
        "valid": True,
        "strategies_checked": list(strategy_orderings.keys()),
        "total_entries": len(entries)
    }

def main():
    parser = argparse.ArgumentParser(
        description="Validate that no duplicate orderings exist within a strategy group across seeds."
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/processed/prompt_manifest.json",
        help="Path to the prompt manifest JSON file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/validation_orderings.json",
        help="Path to write the validation report."
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    output_path = Path(args.output)

    try:
        logger.info(f"Loading prompt manifest from {manifest_path}...")
        manifest = load_prompt_manifest(manifest_path)
        
        logger.info("Validating orderings...")
        is_valid, report = validate_no_duplicates(manifest)
        
        report["manifest_path"] = str(manifest_path)
        report["status"] = "passed" if is_valid else "failed"
        
        logger.info(f"Validation result: {'PASSED' if is_valid else 'FAILED'}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_json_file(output_path, report)
        logger.info(f"Validation report saved to {output_path}")
        
        if not is_valid:
            logger.error("Validation failed. Duplicate orderings detected.")
            sys.exit(1)
        else:
            sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()