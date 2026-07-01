"""
Validates the collected dataset (Human and LLM samples).
Checks for syntax validity (Python/Java) and generates a validation report.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.config import get_config
from utils.logger import get_logger
from utils.validators import validate_file_syntax, get_language_from_extension

logger = get_logger("validate_dataset")

def load_samples_from_dir(dir_path: Path) -> List[Dict[str, Any]]:
    """Loads metadata from sidecar JSON files or infers from filenames."""
    samples = []
    if not dir_path.exists():
        return samples
    
    # We expect metadata files (e.g., sample_id.json) or we scan for code files
    # The task implies we have samples in data/raw/human_samples and data/raw/llm_samples
    # We will scan for code files and look for corresponding metadata if available,
    # or just validate the code files directly.
    
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
    Validates a list of sample dictionaries.
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
    human_dir = config["raw_human_dir"]
    llm_dir = config["raw_llm_dir"]
    output_dir = config["intermediate_dir"]
    output_file = output_dir / "validation_report.json"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Validating Human Samples in: {human_dir}")
    human_samples = load_samples_from_dir(human_dir)
    human_results = validate_samples(human_samples)
    logger.info(f"Human Samples: {human_results['valid']}/{human_results['total']} valid")

    logger.info(f"Validating LLM Samples in: {llm_dir}")
    llm_samples = load_samples_from_dir(llm_dir)
    llm_results = validate_samples(llm_samples)
    logger.info(f"LLM Samples: {llm_results['valid']}/{llm_results['total']} valid")

    total_samples = human_results["total"] + llm_results["total"]
    total_valid = human_results["valid"] + llm_results["valid"]
    
    if total_samples > 0:
        validation_rate = total_valid / total_samples
    else:
        validation_rate = 0.0

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
    
    if not report["meets_threshold"]:
        logger.warning(f"Validation rate {validation_rate:.2%} is below 95% threshold.")
        # In a real CI, we might exit with error code here, but for this task
        # we just log and produce the report as requested.
    else:
        logger.info("Dataset validation passed threshold.")

if __name__ == "__main__":
    main()