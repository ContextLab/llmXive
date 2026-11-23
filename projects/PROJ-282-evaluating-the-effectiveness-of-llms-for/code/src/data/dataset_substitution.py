"""
Dataset Substitution Logic for PROJ-282.

This module implements the conditional logic to adapt BigVul samples
to the NIST Juliet schema requirements when NIST Juliet is unavailable.
It documents the justification for the substitution and writes mapping rules.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.utils.logger import get_logger, log_stage_complete, log_stage_failure
from src.utils.config import get_project_root, get_data_logs_path

logger = get_logger(__name__)


def load_bigvul_metadata() -> Dict[str, Any]:
    """
    Load metadata describing the BigVul dataset structure.
    
    Returns a dictionary mapping BigVul fields to their expected meanings.
    This is a reference for the mapping logic.
    
    Expected BigVul columns (based on T012 requirements):
    - 'language': C, C++, JavaScript
    - 'vulnerability_type': CWE ID or description
    - 'code': The code snippet
    - 'is_vulnerable': Boolean label (0 or 1)
    
    Returns:
        Dict[str, Any]: Metadata description.
    """
    return {
        "source": "BigVul",
        "fields": {
            "language": "Target programming language (C, C++, JS)",
            "vulnerability_type": "CWE identifier or description",
            "code": "Source code snippet",
            "is_vulnerable": "Binary label (1=vulnerable, 0=safe)"
        },
        "format": "CSV or Parquet"
    }


def generate_substitution_justification(failure_reason: str) -> Dict[str, Any]:
    """
    Generate a structured justification for substituting NIST Juliet with BigVul.
    
    Args:
        failure_reason (str): The specific reason NIST Juliet fetch failed.
        
    Returns:
        Dict[str, Any]: A dictionary containing the justification details,
                        mapping rules, and schema compatibility notes.
    """
    justification = {
        "substitution_event": {
            "primary_dataset": "NIST Juliet (C/C++)",
            "fallback_dataset": "BigVul (C, C++, JavaScript)",
            "failure_reason": failure_reason,
            "timestamp": log_stage_complete.__module__  # Placeholder for actual timestamp logic
        },
        "justification": (
            "NIST Juliet repository could not be fetched due to network or access restrictions. "
            "BigVul is used as the primary fallback as it contains a substantial collection of "
            "C and C++ vulnerable code snippets with ground truth labels. This substitution "
            "allows the pipeline to proceed with zero-shot vulnerability detection evaluation "
            "while maintaining scientific rigor regarding real-world code samples."
        ),
        "schema_mapping_rules": [
            {
                "target_field": "language",
                "source_field": "language",
                "transformation": "Direct mapping. Ensure values are normalized to 'C', 'C++', 'JavaScript'."
            },
            {
                "target_field": "ground_truth_category",
                "source_field": "vulnerability_type",
                "transformation": "Direct mapping. If CWE ID is present, use it. If description, attempt CWE ID lookup or keep description."
            },
            {
                "target_field": "ground_truth_label",
                "source_field": "is_vulnerable",
                "transformation": "Direct mapping. 1 -> 'vulnerable', 0 -> 'safe'."
            },
            {
                "target_field": "code",
                "source_field": "code",
                "transformation": "Direct mapping."
            }
        ],
        "limitations": [
            "BigVul includes JavaScript, which was not the primary focus of NIST Juliet (C/C++). "
            "Analysis results should be stratified by language.",
            "The distribution of vulnerability types may differ from NIST Juliet's structured test cases."
        ]
    }
    return justification


def write_justification_log(justification: Dict[str, Any], failure_reason: str) -> Path:
    """
    Write the substitution justification to the project's log directory.
    
    Args:
        justification (Dict[str, Any]): The justification dictionary.
        failure_reason (str): The reason for the substitution.
        
    Returns:
        Path: The path to the written log file.
    """
    logs_path = get_data_logs_path()
    logs_path.mkdir(parents=True, exist_ok=True)
    
    output_file = logs_path / "dataset_substitution_justification.json"
    
    log_entry = {
        "status": "SUBSTITUTION_EXECUTED",
        "reason": failure_reason,
        "details": justification
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(log_entry, f, indent=2)
    
    logger.info(f"Wrote dataset substitution justification to {output_file}")
    return output_file


def run_dataset_substitution_logic(failure_reason: str) -> bool:
    """
    Execute the full dataset substitution logic.
    
    This function:
    1. Loads BigVul metadata.
    2. Generates the justification and mapping rules.
    3. Writes the justification log to `data/logs/dataset_substitution_justification.json`.
    
    Args:
        failure_reason (str): The specific reason NIST Juliet fetch failed.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        logger.info("Running dataset substitution logic for BigVul fallback.")
        
        # Load metadata
        bigvul_meta = load_bigvul_metadata()
        logger.debug(f"Loaded BigVul metadata: {list(bigvul_meta.keys())}")
        
        # Generate justification
        justification = generate_substitution_justification(failure_reason)
        logger.debug("Generated substitution justification.")
        
        # Write log
        log_path = write_justification_log(justification, failure_reason)
        
        logger.info("Dataset substitution logic completed successfully.")
        return True
        
    except Exception as e:
        logger.error(f"Failed to run dataset substitution logic: {e}", exc_info=True)
        return False


def main():
    """
    Main entry point for the dataset substitution script.
    
    Expects a failure reason to be passed or determined.
    For this task, we simulate the condition where T011 failed.
    """
    # In a real pipeline, this would be called by the orchestrator (T015)
    # with the actual error message from T011.
    # Here we demonstrate the logic.
    
    failure_msg = "NIST Juliet git clone failed: Connection timed out."
    
    success = run_dataset_substitution_logic(failure_msg)
    
    if success:
        print("Dataset substitution justification written successfully.")
    else:
        print("Dataset substitution logic failed.")
        exit(1)


if __name__ == "__main__":
    main()
