"""
Assignment Generator Module
Implements Latin-square design assignment logic for balanced task conditions.
"""
import random
from typing import List, Dict, Any
from pathlib import Path
from utils.config_manager import get_config

# Condition constants
CONDITION_BASELINE = "baseline"
CONDITION_LLM = "llm"
CONDITION_RULE = "rule"

CONDITIONS = [CONDITION_BASELINE, CONDITION_LLM, CONDITION_RULE]

def generate_latin_square(n: int) -> List[List[str]]:
    """
    Generate an n x n Latin square using cyclic shifts.
    Each row is a cyclic shift of the conditions list.
    """
    if n != len(CONDITIONS):
        raise ValueError(f"Latin square size {n} must match number of conditions {len(CONDITIONS)}")
    
    # Create base row
    base_row = CONDITIONS[:]
    square = []
    
    for i in range(n):
        # Cyclic shift by i positions
        shifted_row = base_row[i:] + base_row[:i]
        square.append(shifted_row)
    
    return square

def assign_conditions(participant_id: str, task_ids: List[str], cohort_size: int = 30) -> Dict[str, Dict[str, str]]:
    """
    Assign conditions to tasks for a participant using Latin-square design.
    
    Args:
        participant_id: Unique participant identifier
        task_ids: List of task IDs to assign conditions to
        cohort_size: Expected cohort size for Latin square generation
    
    Returns:
        Dictionary mapping participant_id to a dict of task_id -> condition
    """
    if len(task_ids) > len(CONDITIONS):
        raise ValueError(f"Number of tasks ({len(task_ids)}) exceeds number of conditions ({len(CONDITIONS)})")
    
    # Generate Latin square for the cohort
    latin_square = generate_latin_square(len(CONDITIONS))
    
    # Determine participant's row in the Latin square
    # Use participant_id hash to ensure deterministic assignment
    # Extract numeric part if exists, otherwise use hash
    try:
        # Try to extract number from participant_id (e.g., "P001" -> 1)
        numeric_part = int(''.join(filter(str.isdigit, participant_id)))
    except ValueError:
        numeric_part = hash(participant_id) % 10000
    
    # Map to row index (0 to cohort_size-1)
    row_index = numeric_part % len(latin_square)
    
    # Assign conditions to tasks
    assignments = {}
    for i, task_id in enumerate(task_ids):
        condition = latin_square[row_index][i]
        assignments[task_id] = condition
    
    return {participant_id: assignments}

def generate_cohort_assignments(participant_ids: List[str], task_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Generate assignments for an entire cohort of participants.
    
    Args:
        participant_ids: List of participant identifiers
        task_ids: List of task IDs to assign conditions to
    
    Returns:
        List of assignment records for database insertion
    """
    assignments = []
    
    for participant_id in participant_ids:
        participant_assignment = assign_conditions(participant_id, task_ids)
        for p_id, task_conditions in participant_assignment.items():
            for task_id, condition in task_conditions.items():
                assignments.append({
                    "participant_id": p_id,
                    "task_id": task_id,
                    "condition": condition
                })
    
    return assignments

def save_assignments(assignments: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save assignments to a JSON file.
    
    Args:
        assignments: List of assignment records
        output_path: Path to output JSON file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        import json
        json.dump(assignments, f, indent=2)
    
    # Also generate hashes for versioning
    from utils.hash_artifacts import hash_file
    hash_value = hash_file(path)
    return hash_value