import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_json_file(path: str) -> List[Dict[str, Any]]:
    """Load a JSON file and return its contents as a list of dictionaries."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def calculate_accuracy(classified: List[Dict[str, Any]], golden: List[Dict[str, Any]]) -> float:
    """
    Calculate accuracy between classified traces and the golden set.
    
    Args:
        classified: List of classified traces with 'trace_id' and 'predicted_label'.
        golden: List of golden traces with 'trace_id' and 'ground_truth_label'.
        
    Returns:
        Accuracy as a float between 0.0 and 1.0.
    """
    if not golden:
        logger.warning("Golden set is empty. Cannot calculate accuracy.")
        return 0.0

    # Create a lookup for golden traces by trace_id
    golden_lookup = {t.get("trace_id"): t.get("ground_truth_label") for t in golden}
    
    correct = 0
    total = 0

    for item in classified:
        trace_id = item.get("trace_id")
        if trace_id not in golden_lookup:
            logger.warning(f"Trace {trace_id} not found in golden set. Skipping.")
            continue

        predicted = item.get("predicted_label")
        actual = golden_lookup[trace_id]

        if predicted is None or actual is None:
            logger.warning(f"Missing label for {trace_id}. Skipping.")
            continue

        total += 1
        if predicted == actual:
            correct += 1
        else:
            logger.debug(f"Mismatch for {trace_id}: predicted={predicted}, actual={actual}")

    if total == 0:
        logger.warning("No matching traces found between classified and golden sets.")
        return 0.0
    
    return correct / total

def main():
    """Main entry point for the validation script."""
    parser = argparse.ArgumentParser(description="Validate classification results against golden set")
    parser.add_argument("--input", type=str, required=True, help="Input classified traces JSON")
    parser.add_argument("--golden", type=str, required=True, help="Golden set JSON")
    parser.add_argument("--output", type=str, default=None, help="Output report JSON (optional)")
    
    args = parser.parse_args()
    
    # Validate input files exist
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    if not os.path.exists(args.golden):
        logger.error(f"Golden file not found: {args.golden}")
        sys.exit(1)

    try:
        classified = load_json_file(args.input)
        golden = load_json_file(args.golden)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading files: {e}")
        sys.exit(1)

    logger.info(f"Loaded {len(classified)} classified traces and {len(golden)} golden traces.")
    
    accuracy = calculate_accuracy(classified, golden)
    logger.info(f"Classification accuracy: {accuracy:.4f}")
    
    result = {
        "accuracy": accuracy,
        "total_classified": len(classified),
        "total_golden": len(golden),
        "matching": int(len(classified) * accuracy),
        "input_file": args.input,
        "golden_file": args.golden
    }

    if args.output:
        output_dir = os.path.dirname(args.output)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Validation report written to {args.output}")
    
    # Exit with success regardless of accuracy (T013b handles the gate)
    sys.exit(0)

if __name__ == "__main__":
    main()