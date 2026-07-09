"""
Assignment Generator Module
Implements Latin-square design assignment logic for balanced task conditions.
"""
import random
import json
from typing import List, Dict, Any
from pathlib import Path
from utils.config_manager import get_config
from utils.hash_artifacts import hash_file

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

def save_assignments(assignments: List[Dict[str, Any]], output_path: str) -> str:
    """
    Save assignments to a JSON file.
    
    Args:
        assignments: List of assignment records
        output_path: Path to output JSON file
    
    Returns:
        SHA-256 hash of the generated file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(assignments, f, indent=2)
    
    # Generate hash for versioning
    hash_value = hash_file(path)
    return hash_value

def main():
    """
    Main entry point to generate and save cohort assignments.
    Reads configuration from .env or defaults.
    """
    config = get_config()
    
    # Default cohort size and task list if not configured
    cohort_size = config.get('cohort_size', 30)
    
    # Generate synthetic participant IDs for demonstration
    # In a real study, these would be loaded from a participant registry
    participant_ids = [f"P{i:03d}" for i in range(1, cohort_size + 1)]
    
    # Load task IDs from a predefined list or config
    # For this implementation, we assume 3 tasks to match 3 conditions
    task_ids = config.get('task_ids', ["TASK_001", "TASK_002", "TASK_003"])
    
    if len(task_ids) > len(CONDITIONS):
        print(f"Warning: {len(task_ids)} tasks requested, but only {len(CONDITIONS)} conditions available. "
              f"Truncating to first {len(CONDITIONS)} tasks.")
        task_ids = task_ids[:len(CONDITIONS)]
    
    # Generate assignments
    assignments = generate_cohort_assignments(participant_ids, task_ids)
    
    # Define output path
    output_path = config.get('assignment_output_path', 'data/analysis_results/condition_assignments.json')
    
    # Save and get hash
    file_hash = save_assignments(assignments, output_path)
    
    print(f"Generated {len(assignments)} assignments for {cohort_size} participants.")
    print(f"Output saved to: {output_path}")
    print(f"File hash (SHA-256): {file_hash}")
    
    return output_path

if __name__ == "__main__":
    main()
