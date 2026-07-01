"""
Tool Validity Check for PMD Static Analysis.

This module validates the PMD configuration by running it against a known
"clean" reference set of code samples. It calculates the false-positive rate
and flags the tool configuration as invalid if the rate exceeds 5%.

Dependencies:
- T022 (parse_results.py) must have run to populate data/intermediate/analysis_results.json
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
from utils.config import get_project_root

logger = get_logger(__name__)

# Configuration
FALSE_POSITIVE_THRESHOLD = 0.05  # 5%
REFERENCE_DIR_HUMAN = "data/raw/human_samples"
REFERENCE_DIR_LLM = "data/raw/llm_samples"
INPUT_RESULTS_FILE = "data/intermediate/analysis_results.json"
OUTPUT_VALIDITY_FILE = "data/intermediate/tool_validity_status.json"

# Expected "clean" smells for reference set (based on plan.md context:
# we assume the reference set is curated to be free of the 4 target smells)
TARGET_SMELLS = [
    "LongMethod",
    "DuplicatedCode",
    "FeatureEnvy",
    "LongParameterList"
]

def load_analysis_results() -> Optional[Dict[str, Any]]:
    """Load parsed analysis results from T022."""
    root = get_project_root()
    results_path = root / INPUT_RESULTS_FILE
    
    if not results_path.exists():
        logger.error(f"Analysis results not found at {results_path}. "
                     "Please ensure T022 (parse_results.py) has been run.")
        return None
    
    try:
        with open(results_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse analysis results JSON: {e}")
        return None

def identify_reference_samples(results: Dict[str, Any]) -> List[str]:
    """
    Identify samples that belong to the reference set.
    
    In this implementation, we assume the reference set consists of:
    1. All human samples (data/raw/human_samples)
    2. All LLM samples (data/raw/llm_samples)
    
    We filter the results to only include samples that exist in these directories.
    """
    root = get_project_root()
    human_dir = root / REFERENCE_DIR_HUMAN
    llm_dir = root / REFERENCE_DIR_LLM
    
    reference_ids = set()
    
    # Collect sample IDs from directories
    for directory in [human_dir, llm_dir]:
        if directory.exists():
            for item in directory.iterdir():
                if item.is_file() and item.suffix == '.py':
                    # Extract sample ID from filename (e.g., human_sample_001.py -> human_sample_001)
                    sample_id = item.stem
                    reference_ids.add(sample_id)
                elif item.is_file() and item.suffix == '.java':
                    sample_id = item.stem
                    reference_ids.add(sample_id)
    
    return list(reference_ids)

def calculate_false_positive_rate(
    results: Dict[str, Any], 
    reference_sample_ids: List[str]
) -> float:
    """
    Calculate the false-positive rate on the reference set.
    
    A false positive is defined as a detected smell in a reference sample
    that is expected to be clean (i.e., contains none of the TARGET_SMELLS).
    """
    if not reference_sample_ids:
        logger.warning("No reference samples found for validity check.")
        return 0.0
    
    total_checks = 0
    false_positives = 0
    
    for sample_id in reference_sample_ids:
        if sample_id not in results:
            # Sample not in results (might be excluded due to syntax error)
            continue
        
        sample_data = results[sample_id]
        smells_detected = sample_data.get("smells", [])
        
        # Check for any of the target smells
        for smell in smells_detected:
            smell_type = smell.get("type", "")
            if smell_type in TARGET_SMELLS:
                total_checks += 1
                false_positives += 1
                logger.debug(f"False positive detected in {sample_id}: {smell_type}")
    
    if total_checks == 0:
        logger.warning("No target smells were checked in the reference set.")
        return 0.0
    
    return false_positives / total_checks

def write_validity_status(is_valid: bool, false_positive_rate: float) -> None:
    """Write the validity status to the output file."""
    root = get_project_root()
    output_path = root / OUTPUT_VALIDITY_FILE
    
    status_data = {
        "is_valid": is_valid,
        "false_positive_rate": false_positive_rate,
        "threshold_used": FALSE_POSITIVE_THRESHOLD,
        "reference_samples_checked": len(identify_reference_samples(load_analysis_results() or {})),
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "target_smells": TARGET_SMELLS
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, indent=2)
    
    logger.info(f"Validity status written to {output_path}")

def main() -> int:
    """Main entry point for the tool validity check."""
    logger.info("Starting tool validity check...")
    
    # Load results
    results = load_analysis_results()
    if results is None:
        logger.error("Aborting: Could not load analysis results.")
        return 1
    
    # Identify reference samples
    reference_ids = identify_reference_samples(results)
    if not reference_ids:
        logger.error("Aborting: No reference samples found.")
        return 1
    
    logger.info(f"Found {len(reference_ids)} reference samples to validate.")
    
    # Calculate false positive rate
    fpr = calculate_false_positive_rate(results, reference_ids)
    logger.info(f"Calculated false positive rate: {fpr:.4f} ({fpr*100:.2f}%)")
    
    # Determine validity
    is_valid = fpr <= FALSE_POSITIVE_THRESHOLD
    
    if is_valid:
        logger.info(f"Tool configuration is VALID (FPR {fpr:.4f} <= {FALSE_POSITIVE_THRESHOLD})")
    else:
        logger.warning(f"Tool configuration is INVALID (FPR {fpr:.4f} > {FALSE_POSITIVE_THRESHOLD})")
        logger.warning("PMD ruleset may be too aggressive or misconfigured.")
    
    # Write results
    write_validity_status(is_valid, fpr)
    
    return 0 if is_valid else 1

if __name__ == "__main__":
    sys.exit(main())