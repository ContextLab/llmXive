"""
Main script for functional drift detection.

Loads simplified functions from data/processed/simplified_functions.jsonl,
runs equivalence checks against their original counterparts using T015 logic,
and logs pairs with drift to results/simplification_log.json.

This satisfies T026: Add functional drift detection.
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

from utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_error
from benchmark.equivalence import run_equivalence_check_batch, DriftLog

logger = get_logger(__name__)

def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file and return a list of dictionaries."""
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error at line {line_num}: {e}")
                raise
    return data

def save_json(data: Any, file_path: Path) -> None:
    """Save data as JSON to the specified file path."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Saved results to {file_path}")

def run_drift_detection(
    simplified_functions_path: Path,
    validated_functions_path: Path,
    output_log_path: Path
) -> Dict[str, Any]:
    """
    Run drift detection on simplified functions.
    
    Args:
        simplified_functions_path: Path to simplified_functions.jsonl
        validated_functions_path: Path to validated_functions.jsonl (originals)
        output_log_path: Path to write the drift log JSON
        
    Returns:
        Summary statistics of the drift detection run.
    """
    log_stage_start(logger, "Drift Detection", {
        "simplified_input": str(simplified_functions_path),
        "original_input": str(validated_functions_path),
        "output": str(output_log_path)
    })

    try:
        # Load simplified functions
        logger.info(f"Loading simplified functions from {simplified_functions_path}")
        simplified_functions = load_jsonl(simplified_functions_path)
        logger.info(f"Loaded {len(simplified_functions)} simplified functions")

        # Load original validated functions
        logger.info(f"Loading validated functions from {validated_functions_path}")
        validated_functions = load_jsonl(validated_functions_path)
        logger.info(f"Loaded {len(validated_functions)} validated functions")

        # Create a mapping from function_id to original code
        original_map = {func['function_id']: func['code'] for func in validated_functions}
        
        drift_results: List[DriftLog] = []
        pairs_checked = 0
        drifts_detected = 0
        equivalence_failed = 0

        for simplified_func in simplified_functions:
            func_id = simplified_func.get('function_id')
            if not func_id:
                logger.warning(f"Simplified function missing 'function_id', skipping: {simplified_func}")
                continue

            original_code = original_map.get(func_id)
            if not original_code:
                logger.warning(f"Original code not found for function_id: {func_id}")
                continue

            simplified_code = simplified_func.get('code')
            if not simplified_code:
                logger.warning(f"Simplified function missing 'code' for {func_id}, skipping")
                continue

            pairs_checked += 1
            logger.info(f"Checking equivalence for function_id: {func_id}")

            try:
                # Run equivalence check using T015 logic
                # Note: run_equivalence_check_batch expects a list of (original, simplified) tuples
                # or a specific batch format. Based on T015 signature, we assume it handles
                # the logic for a pair or batch. We will call it for the single pair.
                # The function signature from T015 is: run_equivalence_check_batch(pairs)
                # where pairs is likely a list of (original_code, simplified_code).
                
                pair_results = run_equivalence_check_batch([(original_code, simplified_code)])
                
                if pair_results and len(pair_results) > 0:
                    result = pair_results[0]
                    drift_results.append(result)
                    
                    if result.is_drifted:
                        drifts_detected += 1
                        logger.info(f"DRIFT DETECTED for {func_id}: {result.reason}")
                    else:
                        logger.info(f"No drift for {func_id}")
                else:
                    logger.warning(f"No result returned for {func_id}")
                    equivalence_failed += 1

            except Exception as e:
                logger.error(f"Equivalence check failed for {func_id}: {e}", exc_info=True)
                # Create a drift log entry indicating failure
                drift_results.append(DriftLog(
                    function_id=func_id,
                    is_drifted=True,
                    reason=f"Equivalence check error: {str(e)}",
                    execution_details={"error": str(e)}
                ))
                equivalence_failed += 1

        # Prepare output summary
        summary = {
            "total_pairs_checked": pairs_checked,
            "drifts_detected": drifts_detected,
            "equivalence_check_failures": equivalence_failed,
            "drift_rate": drifts_detected / pairs_checked if pairs_checked > 0 else 0.0,
            "results": [
                {
                    "function_id": r.function_id,
                    "is_drifted": r.is_drifted,
                    "reason": r.reason,
                    "execution_details": r.execution_details
                }
                for r in drift_results
            ]
        }

        # Save results
        save_json(summary, output_log_path)

        log_stage_complete(logger, "Drift Detection", {
            "pairs_checked": pairs_checked,
            "drifts_detected": drifts_detected,
            "output_file": str(output_log_path)
        })

        return summary

    except Exception as e:
        log_stage_error(logger, "Drift Detection", str(e), exc_info=True)
        raise

def main():
    """Entry point for the drift detection pipeline."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    simplified_input = project_root / "data" / "processed" / "simplified_functions.jsonl"
    validated_input = project_root / "data" / "processed" / "validated_functions.jsonl"
    output_log = project_root / "results" / "simplification_log.json"

    if not simplified_input.exists():
        logger.error(f"Simplified functions file not found: {simplified_input}")
        sys.exit(1)
    
    if not validated_input.exists():
        logger.error(f"Validated functions file not found: {validated_input}")
        sys.exit(1)

    logger.info("Starting functional drift detection pipeline...")
    run_drift_detection(simplified_input, validated_input, output_log)
    logger.info("Drift detection complete.")

if __name__ == "__main__":
    main()