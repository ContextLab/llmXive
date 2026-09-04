import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define failure reason types as a simple class/named tuple equivalent
class FailureReason:
    """Enum-like class for failure modes."""
    MODEL_SUBSTITUTION = "model_substitution"
    DATA_UNAVAILABLE = "data_unavailable"
    COVARIATE_MISSING = "covariate_missing"
    MISSING_SEED = "missing_seed"
    VALIDATION_FAILED = "validation_failed"
    OTHER = "other"

def load_existing_failure_log(log_path: str = "artifacts/logs/failure_log.json") -> List[Dict[str, Any]]:
    """
    Loads an existing failure log if it exists, otherwise returns an empty list.
    """
    path = Path(log_path)
    if not path.exists():
        logger.info(f"No existing failure log found at {log_path}. Starting fresh.")
        return []
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                logger.warning("Existing failure log is not a list. Resetting.")
                return []
            return data
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load existing failure log: {e}")
        return []

def record_failure(
    log_entries: List[Dict[str, Any]],
    paper_doi: str,
    failure_mode: str,
    details: str
) -> None:
    """
    Appends a failure record to the in-memory list.
    """
    entry = {
        "paper_doi": paper_doi,
        "failure_mode": failure_mode,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    log_entries.append(entry)
    logger.info(f"Recorded failure for {paper_doi}: {failure_mode}")

def compile_failure_summary(
    repro_results_path: str = "artifacts/reports/repro_results.json"
) -> List[Dict[str, Any]]:
    """
    Reads the aggregated repro_results.json and compiles a failure log
    based on flags and null values found in the results.
    """
    log_entries: List[Dict[str, Any]] = []
    path = Path(repro_results_path)
    
    if not path.exists():
        logger.warning(f"Repro results file not found at {repro_results_path}. Cannot compile failure log.")
        return log_entries

    try:
        with open(path, 'r', encoding='utf-8') as f:
            results = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to read repro results: {e}")
        return log_entries

    if not isinstance(results, list):
        logger.error("Repro results file does not contain a list of results.")
        return log_entries

    for entry in results:
        doi = entry.get("doi", "unknown")
        flags = entry.get("flags", [])
        mae = entry.get("mae")
        r2 = entry.get("r2")
        
        # Check for specific failure modes based on flags and missing data
        if "model_substitution" in flags:
            record_failure(
                log_entries, doi, FailureReason.MODEL_SUBSTITUTION,
                "Model exceeded parameter limit (>1M) and was substituted with Random Forest baseline."
            )
        
        if "covariate_missing" in flags:
            record_failure(
                log_entries, doi, FailureReason.COVARIATE_MISSING,
                "Required experimental covariates (temp, solvent, etc.) were missing from source data."
            )

        if "data_unavailable" in flags:
            record_failure(
                log_entries, doi, FailureReason.DATA_UNAVAILABLE,
                "Dataset variables (SMILES, yield) could not be verified or loaded."
            )

        if "missing_seed" in flags:
            record_failure(
                log_entries, doi, FailureReason.MISSING_SEED,
                "Random seed was not reported in the source paper; default seed 42 was used."
            )

        # Check for null metrics that imply failure to reproduce
        if mae is None and "model_substitution" not in flags and "data_unavailable" not in flags:
            # If MAE is null but no specific flag, it might be a generic failure
            record_failure(
                log_entries, doi, FailureReason.OTHER,
                "Reproduction failed resulting in null MAE (generic failure)."
            )

    return log_entries

def write_failure_report(
    log_entries: List[Dict[str, Any]],
    output_path: str = "artifacts/logs/failure_log.json"
) -> None:
    """
    Writes the compiled failure log to the specified JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(log_entries, f, indent=2)
    
    logger.info(f"Failure log written to {output_path} with {len(log_entries)} entries.")

def main():
    """
    Main entry point to compile and write the failure log.
    """
    logger.info("Starting failure log compilation.")
    
    # 1. Compile failures from repro results
    log_entries = compile_failure_summary()
    
    # 2. Write to file
    write_failure_report(log_entries)
    
    logger.info("Failure log compilation complete.")

if __name__ == "__main__":
    main()
