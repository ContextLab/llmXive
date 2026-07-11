"""
T019: Verify and archive output for User Story 1.

This script validates that the data pipeline (T014-T018) successfully generated
the required output artifacts:
1. data/processed/cleaned_studies.csv
2. data/raw/excluded_studies.log

It performs structural validation (file existence, non-empty content, schema compliance)
and logs the verification results using the project's structured logging infrastructure.
"""
import os
import sys
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger, log_event
from utils.config import get_data_path, get_output_path, get_code_path
from data.models import Study

logger = get_logger(__name__)

# Define expected artifacts per T019
REQUIRED_ARTIFACTS = {
    "cleaned_studies": {
        "path": "data/processed/cleaned_studies.csv",
        "type": "csv",
        "required_columns": [
            "study_id", "title", "author", "year", 
            "intervention_component", "delivery_format",
            "n_treatment", "n_control", "outcome_domain",
            "effect_size", "se_effect_size"
        ]
    },
    "excluded_studies": {
        "path": "data/raw/excluded_studies.log",
        "type": "log",
        "min_lines": 0  # Log can be empty if no exclusions, but must exist
    }
}

def verify_csv_artifact(artifact_name: str, artifact_config: Dict[str, Any]) -> Dict[str, Any]:
    """Verify a CSV artifact exists, is non-empty, and matches schema."""
    result = {
        "name": artifact_name,
        "path": artifact_config["path"],
        "status": "pending",
        "issues": []
    }
    
    full_path = project_root / artifact_config["path"]
    
    # Check existence
    if not full_path.exists():
        result["status"] = "failed"
        result["issues"].append(f"File does not exist: {full_path}")
        return result
    
    # Check file size
    if full_path.stat().st_size == 0:
        result["status"] = "failed"
        result["issues"].append("File is empty")
        return result
    
    # Validate CSV structure
    if artifact_config["type"] == "csv":
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                if not headers:
                    result["status"] = "failed"
                    result["issues"].append("CSV has no headers")
                    return result
                
                # Check required columns
                missing_cols = set(artifact_config["required_columns"]) - set(headers)
                if missing_cols:
                    result["status"] = "failed"
                    result["issues"].append(f"Missing required columns: {missing_cols}")
                    return result
                
                # Count records
                rows = list(reader)
                record_count = len(rows)
                
                if record_count == 0:
                    result["status"] = "warning"
                    result["issues"].append("CSV has headers but no data records")
                else:
                    result["status"] = "passed"
                    result["record_count"] = record_count
                    
        except Exception as e:
            result["status"] = "failed"
            result["issues"].append(f"CSV validation error: {str(e)}")
    
    return result

def verify_log_artifact(artifact_name: str, artifact_config: Dict[str, Any]) -> Dict[str, Any]:
    """Verify a log artifact exists."""
    result = {
        "name": artifact_name,
        "path": artifact_config["path"],
        "status": "pending",
        "issues": []
    }
    
    full_path = project_root / artifact_config["path"]
    
    if not full_path.exists():
        result["status"] = "failed"
        result["issues"].append(f"File does not exist: {full_path}")
        return result
    
    if full_path.stat().st_size == 0:
        # Empty log is acceptable if no studies were excluded
        result["status"] = "passed"
        result["line_count"] = 0
        return result
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
            result["status"] = "passed"
            result["line_count"] = line_count
    except Exception as e:
        result["status"] = "failed"
        result["issues"].append(f"Log file read error: {str(e)}")
    
    return result

def main():
    """Main verification routine for T019."""
    logger.info("Starting T019 verification routine")
    
    verification_results = {}
    all_passed = True
    
    # Verify each required artifact
    for artifact_name, config in REQUIRED_ARTIFACTS.items():
        logger.info(f"Verifying artifact: {artifact_name}")
        
        if config["type"] == "csv":
            result = verify_csv_artifact(artifact_name, config)
        elif config["type"] == "log":
            result = verify_log_artifact(artifact_name, config)
        else:
            result = {
                "name": artifact_name,
                "path": config["path"],
                "status": "failed",
                "issues": ["Unknown artifact type"]
            }
        
        verification_results[artifact_name] = result
        
        if result["status"] == "failed":
            all_passed = False
            logger.error(f"Verification FAILED for {artifact_name}: {result['issues']}")
        elif result["status"] == "warning":
            logger.warning(f"Verification WARNING for {artifact_name}: {result['issues']}")
        else:
            logger.info(f"Verification PASSED for {artifact_name}")
    
    # Log summary
    log_event(
        event_type="t019_verification_complete",
        data={
            "overall_status": "passed" if all_passed else "failed",
            "results": verification_results
        }
    )
    
    # Print summary to stdout
    print("\n" + "="*60)
    print("T019 VERIFICATION SUMMARY")
    print("="*60)
    for name, result in verification_results.items():
        status_icon = "✓" if result["status"] in ["passed", "warning"] else "✗"
        print(f"{status_icon} {name}: {result['status'].upper()}")
        if result.get("issues"):
            for issue in result["issues"]:
                print(f"    - {issue}")
        if "record_count" in result:
            print(f"    Records: {result['record_count']}")
        if "line_count" in result:
            print(f"    Log lines: {result['line_count']}")
    print("="*60)
    
    if not all_passed:
        print("\nVERIFICATION FAILED: One or more artifacts are missing or invalid.")
        sys.exit(1)
    else:
        print("\nVERIFICATION PASSED: All required artifacts are present and valid.")
        sys.exit(0)

if __name__ == "__main__":
    main()
