"""
Validation logic for User Story 1.

Implements SC-006: Calculate 'inconclusive' flag if failure rate > 10%.
Input: data/processed/human_verification_results.json
Output: data/processed/validation_status.json
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Import config to get paths
from src.config import get_config


def load_verification_results(input_path: Path) -> list:
    """Load human verification results from JSON file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Verification results file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list format and dict with 'results' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'results' in data:
        return data['results']
    else:
        raise ValueError(f"Unexpected data format in {input_path}. Expected list or dict with 'results' key.")


def calculate_failure_rate(results: list) -> float:
    """
    Calculate the failure rate from verification results.
    
    A 'failure' is defined as a result where the consensus flag indicates
    the item could NOT be verified as a false memory (i.e., 'verified': False).
    
    Returns:
        float: Failure rate (0.0 to 1.0)
    """
    if not results:
        return 0.0
    
    failure_count = 0
    total_count = len(results)
    
    for item in results:
        # Check if the item failed verification
        # The consensus workflow outputs a 'verified' boolean
        if not item.get('verified', False):
            failure_count += 1
    
    return failure_count / total_count if total_count > 0 else 0.0


def calculate_inconclusive_flag(failure_rate: float, threshold: float = 0.10) -> bool:
    """
    Determine if the study should be flagged as 'inconclusive'.
    
    SC-006: If failure rate > 10%, the results are inconclusive.
    
    Args:
        failure_rate: The calculated failure rate (0.0 to 1.0)
        threshold: The threshold for inconclusive flag (default 0.10 = 10%)
    
    Returns:
        bool: True if inconclusive, False otherwise
    """
    return failure_rate > threshold


def generate_validation_status(
    failure_rate: float, 
    inconclusive: bool, 
    total_items: int, 
    failed_items: int
) -> Dict[str, Any]:
    """Generate the validation status dictionary."""
    return {
        "validation_timestamp": datetime.utcnow().isoformat() + "Z",
        "metrics": {
            "total_items": total_items,
            "failed_items": failed_items,
            "failure_rate": round(failure_rate, 4),
            "threshold": 0.10
        },
        "status": {
            "inconclusive": inconclusive,
            "reason": "Failure rate exceeds 10% threshold" if inconclusive else "Failure rate within acceptable range"
        },
        "recommendation": "Study results are inconclusive" if inconclusive else "Proceed with correlation analysis"
    }


def write_validation_status(status: Dict[str, Any], output_path: Path) -> None:
    """Write validation status to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)


def run_validation_workflow(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    threshold: float = 0.10
) -> Dict[str, Any]:
    """
    Run the complete validation workflow.
    
    Args:
        input_path: Path to human_verification_results.json (uses config if None)
        output_path: Path for validation_status.json (uses config if None)
        threshold: Failure rate threshold for inconclusive flag (default 0.10)
    
    Returns:
        Dict containing the validation status
    """
    config = get_config()
    
    if input_path is None:
        input_path = Path(config.paths.data_processed) / "human_verification_results.json"
    
    if output_path is None:
        output_path = Path(config.paths.data_processed) / "validation_status.json"
    
    # Load results
    results = load_verification_results(input_path)
    
    # Calculate metrics
    failure_rate = calculate_failure_rate(results)
    total_items = len(results)
    failed_items = int(failure_rate * total_items)
    
    # Determine inconclusive flag
    inconclusive = calculate_inconclusive_flag(failure_rate, threshold)
    
    # Generate status
    status = generate_validation_status(
        failure_rate=failure_rate,
        inconclusive=inconclusive,
        total_items=total_items,
        failed_items=failed_items
    )
    
    # Write output
    write_validation_status(status, output_path)
    
    return status


def main():
    """CLI entry point for validation workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate human verification results and check SC-006 inconclusive flag"
    )
    parser.add_argument(
        "--input", 
        type=str, 
        default=None,
        help="Path to human_verification_results.json"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=None,
        help="Path for validation_status.json output"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.10,
        help="Failure rate threshold for inconclusive flag (default: 0.10)"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input) if args.input else None
    output_path = Path(args.output) if args.output else None
    
    try:
        status = run_validation_workflow(
            input_path=input_path,
            output_path=output_path,
            threshold=args.threshold
        )
        
        print(f"Validation completed successfully.")
        print(f"Total items: {status['metrics']['total_items']}")
        print(f"Failed items: {status['metrics']['failed_items']}")
        print(f"Failure rate: {status['metrics']['failure_rate']:.2%}")
        print(f"Inconclusive: {status['status']['inconclusive']}")
        print(f"Recommendation: {status['recommendation']}")
        print(f"Output written to: {status.get('output_path', 'N/A')}")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error during validation: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
