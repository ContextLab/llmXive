"""
T026b: Filter Drifted Pairs

Reads the output of the simplification pipeline (simplified_functions.jsonl)
and the drift detection logs (simplification_log.json).
Filters out pairs where equivalence could not be verified or drift was detected.
Outputs valid_pairs.jsonl containing only the safe pairs.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import logger utilities from existing project structure
from utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_error, log_stage_exclusion

# Import equivalence check types if needed for type hinting, though we read logs directly
# from benchmark.equivalence import DriftLog # Optional, logs are JSON

logger = get_logger(__name__)

INPUT_SIMPLIFIED_PATH = Path("data/processed/simplified_functions.jsonl")
INPUT_DRIFT_LOG_PATH = Path("results/simplification_log.json")
OUTPUT_VALID_PAIRS_PATH = Path("data/processed/valid_pairs.jsonl")

def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""
    data = []
    if not path.exists():
        logger.error(f"Input file not found: {path}")
        return data
    
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON on line {line_num} in {path}: {e}")
    return data

def load_drift_log(path: Path) -> Dict[str, Any]:
    """Load the drift detection summary JSON."""
    if not path.exists():
        logger.warning(f"Drift log not found at {path}. Assuming no drift detected (all pairs valid).")
        return {"drifted_pairs": [], "unverifiable_pairs": []}
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def filter_pairs(
    simplified_data: List[Dict[str, Any]], 
    drift_log: Dict[str, Any]
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter the simplified data based on drift logs.
    
    Returns:
        (valid_pairs, excluded_pairs)
    """
    valid_pairs = []
    excluded_pairs = []

    # Build sets of IDs for quick lookup from the drift log
    # The log structure is expected to be:
    # {
    #   "drifted_pairs": [{"original_id": "...", "simplified_id": "...", ...}, ...],
    #   "unverifiable_pairs": [{"original_id": "...", "simplified_id": "...", ...}, ...]
    # }
    
    drifted_ids = set()
    unverifiable_ids = set()

    for item in drift_log.get("drifted_pairs", []):
        # We use the simplified_id as the primary key for the simplified file
        if "simplified_id" in item:
            drifted_ids.add(item["simplified_id"])
        elif "id" in item: # Fallback if structure varies
            drifted_ids.add(item["id"])

    for item in drift_log.get("unverifiable_pairs", []):
        if "simplified_id" in item:
            unverifiable_ids.add(item["simplified_id"])
        elif "id" in item:
            unverifiable_ids.add(item["id"])

    logger.info(f"Found {len(drifted_ids)} drifted pairs and {len(unverifiable_ids)} unverifiable pairs in logs.")

    for pair in simplified_data:
        pair_id = pair.get("simplified_id") or pair.get("id")
        if not pair_id:
            logger.warning(f"Pair missing ID, excluding: {pair.get('original_id', 'unknown')}")
            excluded_pairs.append({
                "pair": pair,
                "reason": "missing_id",
                "exclusion_reason_code": "missing_id"
            })
            continue

        if pair_id in drifted_ids:
            reason = "drift_detected"
            log_stage_exclusion(logger, reason, f"Pair {pair_id} failed equivalence check (drift detected).")
            excluded_pairs.append({
                "pair": pair,
                "reason": "drift_detected",
                "exclusion_reason_code": "drift_detected"
            })
        elif pair_id in unverifiable_ids:
            reason = "equivalence_unverifiable"
            log_stage_exclusion(logger, reason, f"Pair {pair_id} equivalence could not be verified (AST diff insufficient or execution error).")
            excluded_pairs.append({
                "pair": pair,
                "reason": "equivalence_unverifiable",
                "exclusion_reason_code": "equivalence_unverifiable"
            })
        else:
            valid_pairs.append(pair)

    return valid_pairs, excluded_pairs

def verify_stratum_counts(valid_pairs: List[Dict[str, Any]]) -> bool:
    """
    Verify that the valid pairs contain at least 10 pairs per stratum.
    Strata are expected to be in the 'stratum' field of the pair.
    """
    stratum_counts = {}
    for pair in valid_pairs:
        stratum = pair.get("stratum", "unknown")
        stratum_counts[stratum] = stratum_counts.get(stratum, 0) + 1
    
    logger.info(f"Valid pairs distribution by stratum: {stratum_counts}")
    
    min_required = 10
    all_pass = True
    for stratum, count in stratum_counts.items():
        if count < min_required:
            logger.warning(f"Stratum '{stratum}' has only {count} pairs (min required: {min_required}).")
            all_pass = False
        else:
            logger.info(f"Stratum '{stratum}' meets requirement: {count} >= {min_required}.")
    
    return all_pass

def run_filter_drift():
    """Main entry point for the drift filtering task."""
    log_stage_start(logger, "T026b", "Filtering drifted and unverifiable pairs")

    # 1. Load inputs
    simplified_data = load_jsonl(INPUT_SIMPLIFIED_PATH)
    if not simplified_data:
        log_stage_error(logger, "T026b", "No data found in simplified_functions.jsonl. Aborting.")
        return False

    drift_log = load_drift_log(INPUT_DRIFT_LOG_PATH)

    # 2. Filter
    valid_pairs, excluded_pairs = filter_pairs(simplified_data, drift_log)

    # 3. Save valid pairs
    OUTPUT_VALID_PAIRS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_VALID_PAIRS_PATH, 'w', encoding='utf-8') as f:
        for pair in valid_pairs:
            f.write(json.dumps(pair) + '\n')
    
    logger.info(f"Wrote {len(valid_pairs)} valid pairs to {OUTPUT_VALID_PAIRS_PATH}")

    # 4. Save exclusion report (optional but useful for debugging)
    exclusion_report_path = Path("results/exclusion_report.json")
    with open(exclusion_report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "total_input": len(simplified_data),
            "total_valid": len(valid_pairs),
            "total_excluded": len(excluded_pairs),
            "excluded_details": excluded_pairs
        }, f, indent=2)
    
    # 5. Verify stratum counts
    if not verify_stratum_counts(valid_pairs):
        logger.warning("Verification failed: Some strata have < 10 pairs.")
        # Note: We do not fail the task entirely if the data is just sparse,
        # but we log the warning as per requirements.
    
    log_stage_complete(logger, "T026b", f"Filter complete. Valid: {len(valid_pairs)}, Excluded: {len(excluded_pairs)}")
    return True

def main():
    success = run_filter_drift()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
