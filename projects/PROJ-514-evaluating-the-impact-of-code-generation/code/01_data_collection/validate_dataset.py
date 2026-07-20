"""
Validates the collected dataset (Human and LLM samples).
Checks for syntax validity (Python/Java) and generates a validation report.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.config import get_config
from utils.logger import get_logger
from utils.validators import validate_file_syntax, get_language_from_extension

logger = get_logger("validate_dataset")

def load_samples_from_dir(dir_path: Path) -> List[Dict[str, Any]]:
    """
    Loads metadata from sidecar JSON files or infers from filenames.
    Scans for code files (.py, .java) in the directory tree.
    """
    samples = []
    if not dir_path.exists():
        logger.warning(f"Directory does not exist: {dir_path}")
        return samples
    
    for file_path in dir_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in ['.py', '.java']:
            samples.append({
                "file_path": str(file_path),
                "filename": file_path.name,
                "extension": file_path.suffix
            })
    return samples

def validate_samples(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validates a list of sample dictionaries using the shared validator.
    Returns a summary and a list of failures.
    """
    total = len(samples)
    valid_count = 0
    invalid_count = 0
    failures = []

    for sample in samples:
        file_path = Path(sample["file_path"])
        is_valid, reason = validate_file_syntax(file_path)
        
        if is_valid:
            valid_count += 1
            sample["status"] = "valid"
        else:
            invalid_count += 1
            sample["status"] = "invalid"
            sample["error"] = reason
            failures.append({
                "file": sample["file_path"],
                "reason": reason
            })
    
    return {
        "total": total,
        "valid": valid_count,
        "invalid": invalid_count,
        "failures": failures
    }

def main():
    config = get_config()
    human_dir = Path(config["raw_human_dir"])
    llm_dir = Path(config["raw_llm_dir"])
    output_dir = Path(config["intermediate_dir"])
    output_file = output_dir / "validation_report.json"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Validating Human Samples in: {human_dir}")
    human_samples = load_samples_from_dir(human_dir)
    logger.info(f"Found {len(human_samples)} human sample files.")
    human_results = validate_samples(human_samples)
    logger.info(f"Human Samples: {human_results['valid']}/{human_results['total']} valid")

    logger.info(f"Validating LLM Samples in: {llm_dir}")
    llm_samples = load_samples_from_dir(llm_dir)
    logger.info(f"Found {len(llm_samples)} LLM sample files.")
    llm_results = validate_samples(llm_samples)
    logger.info(f"LLM Samples: {llm_results['valid']}/{llm_results['total']} valid")

    total_samples = human_results["total"] + llm_results["total"]
    total_valid = human_results["valid"] + llm_results["valid"]
    
    if total_samples > 0:
        validation_rate = total_valid / total_samples
    else:
        validation_rate = 0.0

    # Per task spec: Do not impose a hard threshold to auto-halt, 
    # but report the status and flag if critically low.
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "threshold_target": 0.95,
        "actual_rate": validation_rate,
        "meets_threshold": validation_rate >= 0.95,
        "human": human_results,
        "llm": llm_results,
        "all_failures": human_results["failures"] + llm_results["failures"]
    }

    # Write report
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report written to: {output_file}")
    
    if total_samples == 0:
        logger.error("No samples found to validate. Check data collection steps.")
    elif not report["meets_threshold"]:
        logger.warning(f"Validation rate {validation_rate:.2%} is below 95% target.")
        if validation_rate < 0.50:
            logger.critical("CRITICAL: Validation rate is critically low (<50%). Manual review required.")
    else:
        logger.info("Dataset validation passed threshold.")

if __name__ == "__main__":
    main()