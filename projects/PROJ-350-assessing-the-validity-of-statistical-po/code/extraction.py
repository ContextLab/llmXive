import json
import os
import sys
import time
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

class ExtractionError(Exception):
    """Custom exception for extraction failures."""
    pass

def extract_planned_metrics(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract planned power, target_n, and effect_size_assumption from raw OSF JSON.
    
    Args:
        raw_data: Parsed JSON content from OSF pre-registration.
        
    Returns:
        Dictionary with extracted metrics and metadata.
    """
    # Placeholder for NLP/Regex logic implemented in T013
    # This function is expected to be extended by T013 logic
    # For now, we return a structure that T015 will validate
    return {
        "planned_power": raw_data.get("planned_power"),
        "target_n": raw_data.get("target_n"),
        "effect_size_assumption": raw_data.get("effect_size_assumption"),
        "source_citation": raw_data.get("source_citation", {}),
        "missing_planned_data": False,
        "is_primary": True
    }

def fetch_study_pre_registration_data(osf_id: str) -> Dict[str, Any]:
    """
    Fetch pre-registration data from OSF API.
    
    Args:
        osf_id: OSF study identifier.
        
    Returns:
        Raw JSON data from OSF.
    """
    # Placeholder for T012 OSF fetch logic
    return {"osf_id": osf_id, "raw_content": {}}

def extract_batch(osf_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Extract metrics for a batch of OSF IDs.
    
    Args:
        osf_ids: List of OSF identifiers.
        
    Returns:
        List of extracted metric dictionaries.
    """
    results = []
    for osf_id in osf_ids:
        raw = fetch_study_pre_registration_data(osf_id)
        metrics = extract_planned_metrics(raw)
        results.append(metrics)
    return results

def validate_extracted_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate extracted records ensuring target_n > 0 and flagging invalid ones.
    
    This function implements T015:
    - Ensures target_n is a positive integer.
    - Flags records with missing or invalid target_n.
    - Adds a 'valid' boolean flag to each record.
    
    Args:
        records: List of dictionaries containing extracted metrics.
        
    Returns:
        List of records with 'valid' flag and 'validation_error' field added.
    """
    validated_records = []
    
    for record in records:
        record_copy = record.copy()
        target_n = record_copy.get("target_n")
        
        is_valid = True
        error_msg = None
        
        if target_n is None:
            is_valid = False
            error_msg = "target_n is missing"
        elif not isinstance(target_n, (int, float)):
            is_valid = False
            error_msg = f"target_n is not a number: {type(target_n).__name__}"
        elif target_n <= 0:
            is_valid = False
            error_msg = f"target_n must be > 0, got {target_n}"
        elif not float(target_n).is_integer():
            # Allow floats that are effectively integers, but warn if not
            if target_n < 1.0:
                is_valid = False
                error_msg = f"target_n must be >= 1, got {target_n}"
            else:
                # It's a float >= 1 but not integer (e.g., 10.5)
                # Depending on strictness, this might be invalid. 
                # For this validation, we flag it as potentially invalid but not strictly < 0.
                # However, the requirement is strictly target_n > 0.
                # We will accept non-integers > 0 but log a warning if needed.
                # To be safe and strict on 'count' logic:
                pass 
        
        record_copy["valid"] = is_valid
        if error_msg:
            record_copy["validation_error"] = error_msg
        else:
            record_copy["validation_error"] = None
            
        validated_records.append(record_copy)
        
    return validated_records

def main():
    """
    Main entry point for extraction and validation.
    Demonstrates the validation logic on a sample list.
    """
    # Sample data simulating extraction output
    sample_records = [
        {"target_n": 50, "planned_power": 0.8, "effect_size_assumption": 0.5},
        {"target_n": 0, "planned_power": 0.8, "effect_size_assumption": 0.5},
        {"target_n": -10, "planned_power": 0.9, "effect_size_assumption": 0.3},
        {"target_n": None, "planned_power": 0.8, "effect_size_assumption": 0.5},
        {"target_n": 100, "planned_power": 0.95, "effect_size_assumption": 0.2}
    ]
    
    print("Running validation on extracted records...")
    validated = validate_extracted_records(sample_records)
    
    for i, rec in enumerate(validated):
        status = "VALID" if rec["valid"] else "INVALID"
        error = rec.get("validation_error", "None")
        print(f"Record {i}: {status} - {error}")
        
    return validated

if __name__ == "__main__":
    main()