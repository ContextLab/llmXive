import json
import os
from typing import Any, Dict, List, Tuple

# Schema definitions for validation
EXPLANATION_SCHEMA = {
    "required": ["explanation_id", "problem_id", "condition", "text"],
    "types": {
        "explanation_id": str,
        "problem_id": str,
        "condition": str,
        "text": str,
        "symbolic_trace": list,
        "neural_narrative": str,
        "generated_at": str
    }
}

PROBLEM_SCHEMA = {
    "required": ["problem_id", "subject", "topic", "difficulty", "question_text", "correct_answer"],
    "types": {
        "problem_id": str,
        "subject": str,
        "topic": str,
        "difficulty": int,
        "question_text": str,
        "correct_answer": str
    }
}

SIMULATION_LOG_SCHEMA = {
    "required": [
        "student_id", "condition", "problem_id", "attempt", "timestamp",
        "knowledge_state", "correct", "rt_seconds", "comprehension_rating", "data_source"
    ],
    "types": {
        "student_id": str,
        "condition": str,
        "problem_id": str,
        "attempt": int,
        "timestamp": str,
        "knowledge_state": float,
        "correct": bool,
        "rt_seconds": float,
        "comprehension_rating": int,
        "data_source": str
    }
}

def validate_explanation(data: Dict[str, Any]) -> bool:
    """
    Validate an explanation object against the schema.
    
    Args:
        data: The explanation dictionary to validate.
    
    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(data, dict):
        return False
    
    # Check required fields
    for field in EXPLANATION_SCHEMA["required"]:
        if field not in data:
            return False
    
    # Check types
    for field, expected_type in EXPLANATION_SCHEMA["types"].items():
        if field in data and not isinstance(data[field], expected_type):
            return False
    
    return True

def validate_problem(data: Dict[str, Any]) -> bool:
    """
    Validate a problem object against the schema.
    
    Args:
        data: The problem dictionary to validate.
    
    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(data, dict):
        return False
    
    for field in PROBLEM_SCHEMA["required"]:
        if field not in data:
            return False
    
    for field, expected_type in PROBLEM_SCHEMA["types"].items():
        if field in data and not isinstance(data[field], expected_type):
            return False
    
    return True

def validate_simulation_log(data: Dict[str, Any]) -> bool:
    """
    Validate a simulation log entry against the schema.
    
    Args:
        data: The log entry dictionary to validate.
    
    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(data, dict):
        return False
    
    for field in SIMULATION_LOG_SCHEMA["required"]:
        if field not in data:
            return False
    
    for field, expected_type in SIMULATION_LOG_SCHEMA["types"].items():
        if field in data and not isinstance(data[field], expected_type):
            return False
    
    return True

def validate_batch(data_list: List[Dict[str, Any]], schema_type: str) -> Tuple[int, List[str]]:
    """
    Validate a batch of data items.
    
    Args:
        data_list: List of dictionaries to validate.
        schema_type: One of 'explanation', 'problem', 'simulation_log'.
    
    Returns:
        Tuple of (count_valid, list_of_errors)
    """
    valid_count = 0
    errors = []
    
    if schema_type == "explanation":
        validator = validate_explanation
    elif schema_type == "problem":
        validator = validate_problem
    elif schema_type == "simulation_log":
        validator = validate_simulation_log
    else:
        raise ValueError(f"Unknown schema type: {schema_type}")
    
    for i, item in enumerate(data_list):
        if validator(item):
            valid_count += 1
        else:
            errors.append(f"Item {i} failed validation")
    
    return valid_count, errors
