import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import ensure_directories
from utils.logging import get_perturbation_logger, init_logging

# Constants
CANDIDATES_FILE = "data/processed/perturbation_candidates.json"


def log_candidate_to_file(candidate: Dict[str, Any], log_path: Optional[str] = None) -> None:
    """
    Append a single candidate record to the JSONL candidates file.
    
    Args:
        candidate: Dictionary containing task_id, perturbation_type, raw_score, is_valid, reason.
        log_path: Optional override for the log file path. Defaults to CANDIDATES_FILE.
    """
    if log_path is None:
        log_path = str(Path.cwd() / CANDIDATES_FILE)
    
    # Ensure directory exists
    ensure_directories([str(Path(log_path).parent)])
    
    # Initialize logger for file operations
    logger = get_perturbation_logger()
    
    # Append as JSONL (one JSON object per line) for robustness against interruptions
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(candidate, ensure_ascii=False) + '\n')
        logger.debug(f"Logged candidate for task {candidate.get('task_id')} to {log_path}")
    except IOError as e:
        logger.error(f"Failed to write candidate to {log_path}: {e}")
        raise


def load_all_candidates(log_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load all candidates from the JSONL file.
    
    Args:
        log_path: Optional override for the log file path.
        
    Returns:
        List of candidate dictionaries.
    """
    if log_path is None:
        log_path = str(Path.cwd() / CANDIDATES_FILE)
        
    candidates = []
    if not os.path.exists(log_path):
        return candidates
        
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    candidates.append(json.loads(line))
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON in candidates file: {e}")
        
    return candidates


def get_candidates_by_task(candidates: List[Dict[str, Any]], task_id: str) -> List[Dict[str, Any]]:
    """Filter candidates by task_id."""
    return [c for c in candidates if c.get('task_id') == task_id]


def get_candidates_by_validity(candidates: List[Dict[str, Any]], is_valid: bool) -> List[Dict[str, Any]]:
    """Filter candidates by validity status."""
    return [c for c in candidates if c.get('is_valid') == is_valid]


def get_candidates_by_type(candidates: List[Dict[str, Any]], perturbation_type: str) -> List[Dict[str, Any]]:
    """Filter candidates by perturbation type."""
    return [c for c in candidates if c.get('perturbation_type') == perturbation_type]


def generate_sensitivity_summary(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a summary of candidates for sensitivity analysis.
    
    Args:
        candidates: List of all candidate dictionaries.
        
    Returns:
        Dictionary containing counts by validity and type.
    """
    total = len(candidates)
    valid_count = sum(1 for c in candidates if c.get('is_valid'))
    invalid_count = total - valid_count
    
    type_counts = {}
    for c in candidates:
        p_type = c.get('perturbation_type', 'unknown')
        type_counts[p_type] = type_counts.get(p_type, 0) + 1
        
    return {
        "total_candidates": total,
        "valid_candidates": valid_count,
        "invalid_candidates": invalid_count,
        "distribution_by_type": type_counts
    }


def main():
    """
    Main entry point for testing the logging integration.
    This function demonstrates logging a candidate and reading it back.
    """
    # Initialize logging
    init_logging()
    logger = get_perturbation_logger()
    logger.info("Starting logging integration test")
    
    # Example candidate data
    test_candidates = [
        {
            "task_id": "human_eval_001",
            "perturbation_type": "synonym",
            "raw_score": 0.98,
            "is_valid": True,
            "reason": "Semantic similarity above threshold (0.95)"
        },
        {
            "task_id": "human_eval_001",
            "perturbation_type": "typo",
            "raw_score": 0.92,
            "is_valid": False,
            "reason": "Semantic similarity below threshold (0.95)"
        },
        {
            "task_id": "human_eval_002",
            "perturbation_type": "rephrase",
            "raw_score": 0.96,
            "is_valid": True,
            "reason": "Semantic similarity above threshold (0.95)"
        }
    ]
    
    # Log candidates
    for candidate in test_candidates:
        log_candidate_to_file(candidate)
        
    # Load and verify
    loaded_candidates = load_all_candidates()
    logger.info(f"Loaded {len(loaded_candidates)} candidates")
    
    # Generate summary
    summary = generate_sensitivity_summary(loaded_candidates)
    logger.info(f"Sensitivity summary: {json.dumps(summary, indent=2)}")
    
    # Verify filtering
    task_001_candidates = get_candidates_by_task(loaded_candidates, "human_eval_001")
    logger.info(f"Candidates for human_eval_001: {len(task_001_candidates)}")
    
    valid_candidates = get_candidates_by_validity(loaded_candidates, True)
    logger.info(f"Valid candidates: {len(valid_candidates)}")
    
    logger.info("Logging integration test completed successfully")


if __name__ == "__main__":
    main()
