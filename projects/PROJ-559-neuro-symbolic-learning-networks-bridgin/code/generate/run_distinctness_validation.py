"""
Runner script to validate distinctness between symbolic and neural explanations
for all generated explanation pairs in the project.
"""
import os
import sys
import json
import logging
from typing import List, Dict, Any, Tuple

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from generate.validate_distinctness import validate_distinctness, validate_explanation_pair
from utils.validation import validate_batch

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_explanation_pairs(data_dir: str) -> List[Tuple[str, str, str]]:
    """
    Find all explanation pairs (symbolic, neural, neuro-symbolic) in the data directory.

    Returns:
        List of tuples (symbolic_path, neural_path, problem_id)
    """
    pairs = []
    problem_ids = set()

    # Scan for explanation files
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.startswith("explanation_") and file.endswith(".json"):
                # Extract problem_id and type from filename
                # Expected format: explanation_{type}_{problem_id}.json
                parts = file.replace("explanation_", "").replace(".json", "").split("_")
                if len(parts) >= 2:
                    exp_type = parts[0]
                    problem_id = "_".join(parts[1:])
                    problem_ids.add(problem_id)

    # Pair symbolic and neural explanations
    for problem_id in problem_ids:
        symbolic_path = os.path.join(data_dir, f"explanation_symbolic_{problem_id}.json")
        neural_path = os.path.join(data_dir, f"explanation_neural_{problem_id}.json")

        if os.path.exists(symbolic_path) and os.path.exists(neural_path):
            pairs.append((symbolic_path, neural_path, problem_id))

    return pairs

def run_batch_validation(
    data_dir: str,
    output_dir: str,
    threshold: float = 0.7
) -> Tuple[bool, Dict[str, Any]]:
    """
    Run distinctness validation on all explanation pairs in the data directory.

    Args:
        data_dir: Directory containing explanation JSON files
        output_dir: Directory to write validation reports
        threshold: Maximum allowed similarity score

    Returns:
        Tuple of (all_passed, summary_report)
    """
    os.makedirs(output_dir, exist_ok=True)

    pairs = find_explanation_pairs(data_dir)

    if not pairs:
        logger.warning("No explanation pairs found in the data directory")
        return True, {"pairs_checked": 0, "passed": 0, "failed": 0, "details": []}

    results = []
    passed_count = 0
    failed_count = 0

    for symbolic_path, neural_path, problem_id in pairs:
        try:
            report_path = os.path.join(output_dir, f"validation_report_{problem_id}.json")
            is_valid, report = validate_explanation_pair(
                symbolic_path,
                neural_path,
                report_path
            )

            report["problem_id"] = problem_id
            results.append(report)

            if is_valid:
                passed_count += 1
                logger.info(f"✓ {problem_id}: Validation passed")
            else:
                failed_count += 1
                logger.warning(f"✗ {problem_id}: Validation failed - {report.get('issues', [])}")

        except Exception as e:
            failed_count += 1
            error_report = {
                "problem_id": problem_id,
                "validation_passed": False,
                "issues": [f"Error during validation: {str(e)}"],
                "symbolic_file": symbolic_path,
                "neural_file": neural_path
            }
            results.append(error_report)
            logger.error(f"✗ {problem_id}: Error - {e}")

    # Write summary report
    summary_report = {
        "pairs_checked": len(pairs),
        "passed": passed_count,
        "failed": failed_count,
        "threshold": threshold,
        "details": results
    }

    summary_path = os.path.join(output_dir, "validation_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_report, f, indent=2)

    logger.info(f"Summary written to {summary_path}")

    all_passed = failed_count == 0
    return all_passed, summary_report

def main():
    """Main entry point for standalone execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run distinctness validation on all explanation pairs"
    )
    parser.add_argument(
        "--data-dir",
        default="data/generated",
        help="Directory containing explanation JSON files (default: data/generated)"
    )
    parser.add_argument(
        "--output-dir",
        default="data/validation",
        help="Directory to write validation reports (default: data/validation)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Maximum allowed similarity score (default: 0.7)"
    )

    args = parser.parse_args()

    if not os.path.exists(args.data_dir):
        logger.error(f"Data directory not found: {args.data_dir}")
        sys.exit(1)

    all_passed, summary = run_batch_validation(
        args.data_dir,
        args.output_dir,
        args.threshold
    )

    print(json.dumps(summary, indent=2))

    if not all_passed:
        logger.error("Batch validation failed")
        sys.exit(1)
    else:
        logger.info("Batch validation passed")
        sys.exit(0)

if __name__ == "__main__":
    main()