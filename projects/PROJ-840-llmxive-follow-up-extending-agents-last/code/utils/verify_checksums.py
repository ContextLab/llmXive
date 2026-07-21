import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

from utils.seeds import verify_pairing
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_json_file(path: str) -> List[Dict[str, Any]]:
    """Load a JSON file and return its contents as a list of dictionaries."""
    with open(path, 'r') as f:
        return json.load(f)

def verify_all_pairings(input_path: str, seed: int) -> Tuple[bool, List[str]]:
    """
    Verify pairing for all traces in the input file.
    
    Args:
        input_path: Path to JSON file containing traces
        seed: The seed used for generation (must match the one used to create traces)
        
    Returns:
        Tuple of (all_valid: bool, errors: List[str])
    """
    traces = load_json_file(input_path)
    errors = []
    all_valid = True

    for trace in traces:
        trace_id = trace.get("trace_id")
        if not trace_id:
            errors.append(f"Trace missing trace_id: {trace}")
            all_valid = False
            continue

        try:
            # Verify pairing using the seed and trace instance
            # verify_pairing expects (trace_id, seed) where seed is the integer
            is_valid = verify_pairing(trace_id, seed)
            if not is_valid:
                errors.append(f"Pairing verification failed for trace_id: {trace_id}")
                all_valid = False
        except Exception as e:
            errors.append(f"Error verifying pairing for {trace_id}: {str(e)}")
            all_valid = False

    return all_valid, errors

def main():
    parser = argparse.ArgumentParser(description="Verify checksums and pairings for traces")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file with traces")
    parser.add_argument("--seed", type=int, default=42, help="Seed used for generation")
    parser.add_argument("--output", type=str, default=None, help="Output file for errors (optional)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    logger.info(f"Verifying pairings for {args.input} with seed {args.seed}")
    all_valid, errors = verify_all_pairings(args.input, args.seed)
    
    if all_valid:
        logger.info("All pairings verified successfully.")
        sys.exit(0)
    else:
        logger.error(f"Verification failed. {len(errors)} errors found.")
        for err in errors:
            logger.error(f"  - {err}")
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(errors, f, indent=2)
            logger.info(f"Errors written to {args.output}")
        sys.exit(1)

if __name__ == "__main__":
    main()