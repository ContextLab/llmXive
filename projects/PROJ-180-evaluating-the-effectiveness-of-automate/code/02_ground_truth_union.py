"""
T028: Implement 'Union Ground Truth' construction.

Merges validated heuristic candidates and validated random samples into a unified ground truth.

Inputs:
    - data/processed/validated_heuristic_candidates.json (from T023b-Ingest)
    - data/processed/validated_ground_truth.json (from T024b-Ingest)

Output:
    - data/processed/ground_truth_union.json
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Set

# Add project root to path if running directly
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.config import get_data_processed_dir

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file and return its contents as a list of dictionaries."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required input file not found: {file_path}")
    
    logger.info(f"Loading data from: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        logger.warning(f"Expected list in {file_path}, got {type(data)}. Wrapping in list.")
        return [data] if data else []
    return data

def construct_union_ground_truth(
    heuristic_path: Path,
    random_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Merge heuristic and random validated candidates into a single ground truth.
    
    The union includes:
    1. All items from the heuristic set (validated_heuristic_candidates.json)
    2. All items from the random set (validated_ground_truth.json)
    
    Deduplication is performed based on a unique identifier if present,
    or by comparing the full content if no ID exists.
    
    Returns a summary of the union construction.
    """
    logger.info(f"Starting union construction from:")
    logger.info(f"  - Heuristic: {heuristic_path}")
    logger.info(f"  - Random: {random_path}")

    # Load inputs
    heuristic_data = load_json_file(heuristic_path)
    random_data = load_json_file(random_path)

    logger.info(f"Loaded {len(heuristic_data)} heuristic candidates")
    logger.info(f"Loaded {len(random_data)} random samples")

    # Track unique items to avoid duplicates
    seen_ids: Set[str] = set()
    union_items: List[Dict[str, Any]] = []
    duplicates_found = 0

    # Process heuristic candidates first
    for item in heuristic_data:
        # Determine unique key: try 'id' first, then generate hash of content
        if 'id' in item:
            unique_key = str(item['id'])
        elif 'comment_id' in item:
            unique_key = str(item['comment_id'])
        else:
            # Fallback: use JSON string representation as key
            unique_key = json.dumps(item, sort_keys=True)

        if unique_key not in seen_ids:
            seen_ids.add(unique_key)
            # Add source tag
            item['source'] = 'heuristic'
            union_items.append(item)
        else:
            duplicates_found += 1

    # Process random samples
    for item in random_data:
        if 'id' in item:
            unique_key = str(item['id'])
        elif 'comment_id' in item:
            unique_key = str(item['comment_id'])
        else:
            unique_key = json.dumps(item, sort_keys=True)

        if unique_key not in seen_ids:
            seen_ids.add(unique_key)
            # Add source tag
            item['source'] = 'random'
            union_items.append(item)
        else:
            duplicates_found += 1

    logger.info(f"Union construction complete:")
    logger.info(f"  - Heuristic items: {len(heuristic_data)}")
    logger.info(f"  - Random items: {len(random_data)}")
    logger.info(f"  - Duplicates removed: {duplicates_found}")
    logger.info(f"  - Final union size: {len(union_items)}")

    # Construct output structure
    output_data = {
        "metadata": {
            "description": "Union of validated heuristic candidates and random samples",
            "sources": ["validated_heuristic_candidates.json", "validated_ground_truth.json"],
            "total_items": len(union_items),
            "heuristic_count": len(heuristic_data),
            "random_count": len(random_data),
            "duplicates_removed": duplicates_found,
            "generated_by": "T028-ground-truth-union"
        },
        "items": union_items
    }

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Writing union ground truth to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    return output_data

def main():
    """Main entry point for T028."""
    processed_dir = get_data_processed_dir()
    
    heuristic_input = processed_dir / "validated_heuristic_candidates.json"
    random_input = processed_dir / "validated_ground_truth.json"
    output_file = processed_dir / "ground_truth_union.json"

    # Check if inputs exist
    if not heuristic_input.exists():
        logger.error(f"Heuristic input missing: {heuristic_input}")
        logger.error("Please ensure T023b-Ingest has run successfully.")
        sys.exit(1)
    
    if not random_input.exists():
        logger.error(f"Random input missing: {random_input}")
        logger.error("Please ensure T024b-Ingest has run successfully.")
        sys.exit(1)

    try:
        construct_union_ground_truth(heuristic_input, random_input, output_file)
        logger.info("T028 completed successfully.")
    except Exception as e:
        logger.error(f"Error during union construction: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
