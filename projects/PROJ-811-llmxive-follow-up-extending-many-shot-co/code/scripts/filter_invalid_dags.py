import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

from code.src.parser_utils import load_json_file, save_json_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_manifest(manifest_path: str) -> Dict[str, Any]:
    """Load the DAG manifest JSON file."""
    path = Path(manifest_path)
    if not path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    logger.info(f"Loading manifest from {manifest_path}")
    data = load_json_file(path)
    
    if "examples" not in data:
        logger.error("Manifest missing 'examples' key")
        raise ValueError("Manifest missing 'examples' key")
    
    return data

def filter_invalid_entries(manifest_data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter the manifest to remove invalid traces (cycles, invalid edges).
    
    Returns:
        Tuple of (valid_examples, invalid_examples)
    """
    examples = manifest_data.get("examples", [])
    valid_examples = []
    invalid_examples = []
    
    for entry in examples:
        is_valid = entry.get("is_valid", True)
        entry_id = entry.get("id", "unknown")
        
        if is_valid:
            valid_examples.append(entry)
            logger.debug(f"Entry {entry_id} is valid, keeping")
        else:
            reason = entry.get("invalid_reason", "unknown")
            invalid_examples.append(entry)
            logger.info(f"Entry {entry_id} is invalid (reason: {reason}), excluding")
    
    logger.info(f"Filtered {len(invalid_examples)} invalid entries out of {len(examples)} total")
    return valid_examples, invalid_examples

def save_manifest(manifest_data: Dict[str, Any], output_path: str) -> None:
    """Save the filtered manifest to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving filtered manifest to {output_path}")
    save_json_file(path, manifest_data)

def main():
    """Main entry point for filtering invalid DAGs."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Filter invalid DAG traces from manifest")
    parser.add_argument("--manifest", required=True, help="Path to input DAG manifest JSON")
    parser.add_argument("--output", required=True, help="Path to output filtered manifest JSON")
    
    args = parser.parse_args()
    
    try:
        # Load the manifest
        manifest_data = load_manifest(args.manifest)
        
        # Filter invalid entries
        valid_examples, invalid_examples = filter_invalid_entries(manifest_data)
        
        # Update manifest with only valid examples
        manifest_data["examples"] = valid_examples
        manifest_data["metadata"]["total_examples"] = len(valid_examples)
        manifest_data["metadata"]["excluded_count"] = len(invalid_examples)
        manifest_data["metadata"]["filtered_at"] = "T017_execution"
        
        # Save the filtered manifest
        save_manifest(manifest_data, args.output)
        
        logger.info(f"Successfully filtered manifest. Valid: {len(valid_examples)}, Excluded: {len(invalid_examples)}")
        print(f"Filtered manifest saved to {args.output}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid manifest format: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
