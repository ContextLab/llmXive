"""
Feature Extraction Script for llmXive Pipeline.

This script loads the ground truth dataset, filters out unparseable tasks,
and extracts structural features (metrics and dependency graphs) from the
code differences.

It explicitly implements the logic to skip tree-sitter processing for tasks
flagged as 'Unparseable' in the ground truth, ensuring robustness against
syntax errors.
"""
import os
import csv
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Ensure the parent directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.baseline_runner import ExecutionResult

# Constants
GROUND_TRUTH_PATH = Path("data/processed/ground_truth.csv")
GRAPHS_DIR = Path("data/graphs")
FEATURES_CSV_PATH = Path("data/processed/features.csv")


def load_ground_truth(filepath: Path) -> List[Dict[str, Any]]:
    """
    Loads the ground truth CSV file.

    Args:
        filepath: Path to the ground_truth.csv file.

    Returns:
        A list of dictionaries representing the rows.

    Raises:
        FileNotFoundError: If the ground truth file does not exist.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Ground truth file not found: {filepath}")

    data = []
    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def filter_unparseable(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filters out tasks that are marked as 'Unparseable' in the ground truth.

    This function explicitly checks the 'dynamic_execution_outcome' or a specific
    status flag to identify tasks that failed parsing and should be skipped
    during feature extraction to prevent tree-sitter errors.

    Args:
        tasks: List of task dictionaries.

    Returns:
        A list of tasks that are NOT marked as 'Unparseable'.
    """
    filtered = []
    for task in tasks:
        # Check for 'Unparseable' status in the outcome or a dedicated flag
        outcome = task.get('dynamic_execution_outcome', '')
        status = task.get('status', '')
        
        # Identify unparseable tasks based on T016 implementation details
        is_unparseable = (
            outcome.lower() == 'unparseable' or 
            status.lower() == 'unparseable'
        )
        
        if not is_unparseable:
            filtered.append(task)
        else:
            # Log skipped tasks for traceability (optional but good practice)
            print(f"Skipping unparseable task: {task.get('task_id', 'Unknown')}")
    
    return filtered


def get_lines_of_code(code_diff: str) -> int:
    """
    Calculates the lines of code (LOC) in a code diff.
    
    Args:
        code_diff: The code difference string.
        
    Returns:
        The number of non-empty lines.
    """
    if not code_diff:
        return 0
    lines = code_diff.split('\n')
    return len([line for line in lines if line.strip()])


def get_cyclomatic_complexity(code_diff: str) -> int:
    """
    Calculates a basic cyclomatic complexity estimate.
    
    Note: A full tree-sitter implementation is in T020/T021. This provides
    a fallback or simple heuristic if tree-sitter is not available or 
    as a base metric.
    
    Args:
        code_diff: The code difference string.
        
    Returns:
        An integer representing the complexity estimate.
    """
    if not code_diff:
        return 0
    
    # Simple heuristic based on control flow keywords
    # This is a placeholder for the full tree-sitter implementation required by T020
    keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'with']
    count = 1 # Base complexity
    for keyword in keywords:
        count += code_diff.count(f' {keyword} ')
        count += code_diff.count(f'{keyword}:')
    return count


def get_dependency_depth(code_diff: str) -> int:
    """
    Estimates dependency depth.
    
    Note: Full implementation relies on tree-sitter AST traversal (T020).
    Returns a placeholder value here if tree-sitter is not invoked directly in this function.
    
    Args:
        code_diff: The code difference string.
        
    Returns:
        An integer representing depth.
    """
    if not code_diff:
        return 0
    # Placeholder logic - T020 will replace this with AST-based calculation
    return 1


def calculate_semantic_complexity_score(code_diff: str) -> float:
    """
    Calculates a semantic complexity score.
    
    Note: Full implementation relies on tree-sitter AST traversal (T020).
    
    Args:
        code_diff: The code difference string.
        
    Returns:
        A float representing the score.
    """
    if not code_diff:
        return 0.0
    # Placeholder - T020 will implement the real metric
    return 1.0


def extract_graph_and_metrics(task_id: str, code_diff: str) -> Dict[str, Any]:
    """
    Extracts the dependency graph and metrics for a single task.
    
    This function is a wrapper that would call the tree-sitter logic implemented
    in T020/T021. For T019, we ensure the structure is ready to receive that logic
    and handle the filtering of unparseable tasks upstream.
    
    Args:
        task_id: The unique identifier for the task.
        code_diff: The code difference string.
        
    Returns:
        A dictionary containing metrics and graph structure.
    """
    # T020/T021 will implement the actual tree-sitter parsing here.
    # For now, we return the basic metrics calculated by helper functions.
    return {
        "task_id": task_id,
        "lines_of_code": get_lines_of_code(code_diff),
        "cyclomatic_complexity": get_cyclomatic_complexity(code_diff),
        "dependency_depth": get_dependency_depth(code_diff),
        "semantic_complexity_score": calculate_semantic_complexity_score(code_diff),
        # Placeholder for graph structure
        "graph": {
            "nodes": [],
            "edges": []
        }
    }


def serialize_graph(task_id: str, graph_data: Dict[str, Any]) -> None:
    """
    Serializes the dependency graph to a JSON file.
    
    Args:
        task_id: The unique identifier for the task.
        graph_data: The dictionary containing graph data.
    """
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = GRAPHS_DIR / f"{task_id}.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2)


def main():
    """
    Main entry point for the feature extraction script.
    
    1. Loads ground truth.
    2. Filters out unparseable tasks (T019 requirement).
    3. Iterates through valid tasks.
    4. Extracts features and serializes graphs.
    """
    print("Starting feature extraction...")
    
    # 1. Load Ground Truth
    try:
        tasks = load_ground_truth(GROUND_TRUTH_PATH)
        print(f"Loaded {len(tasks)} tasks from ground truth.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # 2. Filter Unparseable Tasks (T019 Core Logic)
    valid_tasks = filter_unparseable(tasks)
    print(f"Filtered to {len(valid_tasks)} valid tasks for processing.")
    
    if not valid_tasks:
        print("No valid tasks to process. Exiting.")
        return

    # 3. Process Tasks
    processed_metrics = []
    
    for task in valid_tasks:
        task_id = task.get('task_id')
        code_diff = task.get('code_diff', '')
        
        if not task_id:
            print("Warning: Task missing ID, skipping.")
            continue
        
        try:
            # Extract metrics and graph
            metrics = extract_graph_and_metrics(task_id, code_diff)
            
            # Serialize graph to disk (T023 requirement, implemented here for flow)
            serialize_graph(task_id, metrics['graph'])
            
            # Prepare row for features CSV
            # We merge the original task data with the new metrics
            row = {**task}
            row['lines_of_code'] = metrics['lines_of_code']
            row['cyclomatic_complexity'] = metrics['cyclomatic_complexity']
            row['dependency_depth'] = metrics['dependency_depth']
            row['semantic_complexity_score'] = metrics['semantic_complexity_score']
            
            processed_metrics.append(row)
            
        except Exception as e:
            print(f"Error processing task {task_id}: {e}")
            # In a robust pipeline, we might mark this as failed in the output
            # rather than stopping, but for now we log and continue.
            continue
    
    # 4. Write Features CSV (T024 requirement, implemented here to complete the flow)
    if processed_metrics:
        fieldnames = list(processed_metrics[0].keys())
        with open(FEATURES_CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(processed_metrics)
        print(f"Successfully wrote features to {FEATURES_CSV_PATH}")
    else:
        print("No features were generated.")

if __name__ == "__main__":
    main()