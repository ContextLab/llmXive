"""
T026: Add functional drift detection.

This script loads the simplified functions from T025, runs the equivalence check
(T015) against their original counterparts, and logs pairs with drift to
results/simplification_log.json.

Input: data/processed/simplified_functions.jsonl (output of T025)
Output: results/simplification_log.json
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import from existing API surface
from utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_error
from benchmark.equivalence import run_equivalence_check_batch, DriftLog

logger = get_logger(__name__)

def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    
    items = []
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON on line {line_num} in {path}: {e}")
                raise
    return items

def save_json(path: Path, data: Any) -> None:
    """Save data as formatted JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

def run_drift_detection(
    simplified_input_path: Path,
    original_input_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Run drift detection on simplified functions.
    
    Args:
        simplified_input_path: Path to simplified_functions.jsonl
        original_input_path: Path to validated_functions.jsonl (originals)
        output_path: Path to write the drift log
        
    Returns:
        Summary dictionary of the run
    """
    log_stage_start(logger, "drift_detection", {
        "simplified_input": str(simplified_input_path),
        "original_input": str(original_input_path),
        "output": str(output_path)
    })

    try:
        # Load data
        logger.info(f"Loading simplified functions from {simplified_input_path}")
        simplified_funcs = load_jsonl(simplified_input_path)
        logger.info(f"Loaded {len(simplified_funcs)} simplified functions")

        logger.info(f"Loading original functions from {original_input_path}")
        original_funcs = load_jsonl(original_input_path)
        logger.info(f"Loaded {len(original_funcs)} original functions")

        if len(simplified_funcs) != len(original_funcs):
            logger.warning(
                f"Count mismatch: {len(simplified_funcs)} simplified vs "
                f"{len(original_funcs)} original. Processing up to min count."
            )
            min_count = min(len(simplified_funcs), len(original_funcs))
            simplified_funcs = simplified_funcs[:min_count]
            original_funcs = original_funcs[:min_count]

        # Prepare pairs for batch check
        pairs = []
        for i, (orig, simp) in enumerate(zip(original_funcs, simplified_funcs)):
            # Ensure we have the necessary keys
            if 'code' not in orig or 'code' not in simp:
                logger.error(f"Pair {i} missing 'code' key. Skipping.")
                continue
            
            pairs.append({
                "id": orig.get("id", f"pair_{i}"),
                "original_code": orig["code"],
                "simplified_code": simp["code"],
                "stratum": orig.get("stratum", "unknown")
            })

        if not pairs:
            logger.error("No valid pairs found to process.")
            raise ValueError("No valid pairs found to process.")

        # Run equivalence check batch
        logger.info(f"Running equivalence check on {len(pairs)} pairs...")
        results = run_equivalence_check_batch(pairs)

        # Aggregate results into DriftLog format
        drift_log = {
            "total_pairs": len(pairs),
            "equivalent_pairs": 0,
            "drifted_pairs": 0,
            "failed_checks": 0,
            "drift_details": []
        }

        for res in results:
            if res.get("error"):
                drift_log["failed_checks"] += 1
                drift_log["drift_details"].append({
                    "id": res["id"],
                    "stratum": res.get("stratum", "unknown"),
                    "status": "error",
                    "error": str(res["error"])
                })
            elif res.get("equivalent"):
                drift_log["equivalent_pairs"] += 1
            else:
                drift_log["drifted_pairs"] += 1
                drift_log["drift_details"].append({
                    "id": res["id"],
                    "stratum": res.get("stratum", "unknown"),
                    "status": "drift_detected",
                    "reason": res.get("reason", "functional_drift"),
                    "details": res.get("details", {})
                })

        # Save log
        save_json(output_path, drift_log)
        logger.info(f"Drift log saved to {output_path}")

        log_stage_complete(
            logger, 
            "drift_detection", 
            {
                "total": drift_log["total_pairs"],
                "equivalent": drift_log["equivalent_pairs"],
                "drifted": drift_log["drifted_pairs"],
                "failed": drift_log["failed_checks"]
            }
        )

        return drift_log

    except Exception as e:
        log_stage_error(logger, "drift_detection", str(e))
        raise

def main():
    """Entry point for the drift detection script."""
    root = Path(__file__).resolve().parent.parent
    simplified_path = root / "data" / "processed" / "simplified_functions.jsonl"
    original_path = root / "data" / "processed" / "validated_functions.jsonl"
    output_path = root / "results" / "simplification_log.json"

    # Verify inputs exist (fail loudly if not)
    if not simplified_path.exists():
        logger.error(f"Input file missing: {simplified_path}")
        logger.error("Have you run T025 (main_simplify.py) yet?")
        sys.exit(1)
    
    if not original_path.exists():
        logger.error(f"Input file missing: {original_path}")
        logger.error("Have you run the data sampling pipeline (T014/T017) yet?")
        sys.exit(1)

    run_drift_detection(simplified_path, original_path, output_path)
    logger.info("Drift detection completed successfully.")

if __name__ == "__main__":
    main()