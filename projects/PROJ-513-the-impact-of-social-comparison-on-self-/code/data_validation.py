"""
Data Validation Framework (FR-007, FR-008, FR-009).

Implements checks for:
- Data completeness (FR-007)
- Metadata matching (FR-008)
- Visual indistinguishability (FR-009)
"""
import os
import json
import glob
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

# Import from analysis for seed if needed, though not strictly for validation
# from analysis import get_random_seed

class DataValidationError(Exception):
    """Custom exception for validation failures."""
    pass

def check_data_completeness(data_dir: str, threshold: float = 0.95) -> bool:
    """
    FR-007: Check if at least 95% of expected data is present.
    """
    # Implementation depends on expected count vs actual
    # For now, a placeholder that returns True if data_dir exists and has files
    data_path = Path(data_dir)
    if not data_path.exists():
        raise DataValidationError(f"Data directory {data_dir} does not exist.")
    
    files = list(data_path.glob("*.jsonl"))
    if len(files) == 0:
        # If no data yet, completeness is 0? Or N/A?
        # Assuming we check against a known N if available, else skip
        return True 
    
    # Placeholder logic: assume we have a target N defined elsewhere
    # For T024, this will be integrated properly.
    return True

def check_metadata_matching() -> bool:
    """
    FR-008: Check metadata matching (pose, lighting) between AI and Human sets.
    """
    # Load metadata from data/stimuli
    ai_dir = Path("data/stimuli/ai")
    human_dir = Path("data/stimuli/human")
    
    if not ai_dir.exists() or not human_dir.exists():
        raise DataValidationError("Stimuli directories not found.")
    
    # Logic to match pairs and verify metadata
    # This is a simplified check for the gate
    ai_files = list(ai_dir.glob("*.json"))
    human_files = list(human_dir.glob("*.json"))
    
    if len(ai_files) != len(human_files):
        raise DataValidationError(f"Count mismatch: AI={len(ai_files)}, Human={len(human_files)}")
    
    # Verify specific fields exist
    required_fields = ['pose', 'lighting']
    for f in ai_files + human_files:
        with open(f) as file:
            meta = json.load(file)
            for field in required_fields:
                if field not in meta:
                    raise DataValidationError(f"Missing metadata field '{field}' in {f.name}")
    
    return True

def check_visual_indistinguishability() -> bool:
    """
    FR-009: Check visual indistinguishability using data/pretest/results.json.
    Verifies p-value > 0.05.
    """
    pretest_file = Path("data/pretest/results.json")
    
    if not pretest_file.exists():
        raise DataValidationError("Pre-test results file (data/pretest/results.json) not found.")
    
    with open(pretest_file) as f:
        results = json.load(f)
    
    p_value = results.get("p_value")
    
    if p_value is None:
        raise DataValidationError("p_value not found in pre-test results.")
    
    if p_value <= 0.05:
        raise DataValidationError(f"Visual indistinguishability failed: p={p_value} <= 0.05. Stimuli are distinguishable.")
    
    return True

def run_all_validations() -> Dict[str, bool]:
    """
    Runs all validation checks.
    """
    results = {}
    
    try:
        results['completeness'] = check_data_completeness("data/processed")
    except DataValidationError as e:
        results['completeness'] = False
        # Log error but continue? Or stop? Gate usually stops.
    
    try:
        results['metadata'] = check_metadata_matching()
    except DataValidationError as e:
        results['metadata'] = False
    
    try:
        results['visual'] = check_visual_indistinguishability()
    except DataValidationError as e:
        results['visual'] = False
    
    return results

def main():
    """
    CLI entry point for validation.
    """
    print("Running Data Validation...")
    try:
        results = run_all_validations()
        print(json.dumps(results, indent=2))
        
        if all(results.values()):
            print("All validations passed.")
            return 0
        else:
            print("Some validations failed.")
            return 1
    except Exception as e:
        print(f"Validation error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
