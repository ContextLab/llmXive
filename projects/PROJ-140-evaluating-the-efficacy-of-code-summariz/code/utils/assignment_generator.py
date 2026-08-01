import random
import json
from typing import List, Dict, Any
from pathlib import Path
from utils.config_manager import get_config
from utils.hash_artifacts import hash_file

def generate_latin_square(n: int) -> List[List[int]]:
    """
    Generate an n x n Latin square.
    A Latin square is an n x n array filled with n different symbols,
    each occurring exactly once in each row and exactly once in each column.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    
    # Start with the first row: 0, 1, 2, ..., n-1
    first_row = list(range(n))
    
    # Generate subsequent rows by cyclically shifting
    square = []
    for i in range(n):
        # Shift the first row by i positions
        row = first_row[i:] + first_row[:i]
        square.append(row)
    
    return square

def assign_conditions(participant_id: int, task_id: int, conditions: List[str], latin_square: List[List[int]]) -> str:
    """
    Assign a condition to a participant for a specific task using the Latin square.
    
    Args:
        participant_id: Unique identifier for the participant
        task_id: Unique identifier for the task
        conditions: List of available conditions
        latin_square: Pre-generated Latin square for assignment
    
    Returns:
        The assigned condition
    """
    if not conditions:
        raise ValueError("conditions list cannot be empty")
    
    n = len(conditions)
    if n != len(latin_square) or any(len(row) != n for row in latin_square):
        raise ValueError(f"Latin square dimensions ({len(latin_square)}x{len(latin_square[0])}) do not match number of conditions ({n})")
    
    # Use participant_id and task_id to determine the position in the Latin square
    # Ensure we stay within bounds
    row_idx = participant_id % n
    col_idx = task_id % n
    
    condition_idx = latin_square[row_idx][col_idx]
    return conditions[condition_idx]

def generate_cohort_assignments(
    participant_ids: List[int],
    task_ids: List[int],
    conditions: List[str],
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Generate condition assignments for a cohort of participants across multiple tasks.
    
    Args:
        participant_ids: List of participant identifiers
        task_ids: List of task identifiers
        conditions: List of conditions to assign
        seed: Random seed for reproducibility
    
    Returns:
        List of assignment dictionaries with participant_id, task_id, and assigned_condition
    """
    random.seed(seed)
    n = len(conditions)
    
    # Generate a random Latin square
    base_square = generate_latin_square(n)
    
    # Optionally shuffle the conditions mapping for additional randomization
    shuffled_conditions = conditions.copy()
    random.shuffle(shuffled_conditions)
    
    # Map the Latin square values to the shuffled conditions
    # The Latin square values are 0..n-1, so we can directly index
    assignments = []
    
    for pid in participant_ids:
        for tid in task_ids:
            assigned_condition = assign_conditions(pid, tid, shuffled_conditions, base_square)
            assignments.append({
                "participant_id": pid,
                "task_id": tid,
                "assigned_condition": assigned_condition
            })
    
    return assignments

def save_assignments(assignments: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save the generated assignments to a JSON file.
    
    Args:
        assignments: List of assignment dictionaries
        output_path: Path to the output JSON file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(assignments, f, indent=2)
    
    # Generate a hash for versioning
    hash_value = hash_file(path)
    return hash_value

def main():
    """
    Main function to generate and save Latin-square based condition assignments.
    """
    config = get_config()
    
    # Example configuration (can be overridden by .env or config file)
    participant_ids = list(range(1, 21))  # 20 participants
    task_ids = list(range(1, 11))         # 10 tasks
    conditions = ["LLM-Sim", "Rule-Based", "Baseline"]  # 3 conditions
    
    if len(conditions) != 3:
        raise ValueError("This implementation assumes exactly 3 conditions for the Latin square design.")
    
    seed = config.get("latin_square_seed", 42)
    
    assignments = generate_cohort_assignments(participant_ids, task_ids, conditions, seed)
    
    output_path = config.get("assignments_output_path", "data/analysis_results/condition_assignments.json")
    hash_value = save_assignments(assignments, output_path)
    
    print(f"Generated {len(assignments)} assignments.")
    print(f"Saved to: {output_path}")
    print(f"Artifact hash: {hash_value}")
    
    return assignments

if __name__ == "__main__":
    main()